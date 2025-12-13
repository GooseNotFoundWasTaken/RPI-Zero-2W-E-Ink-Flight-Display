import time
import requests
import math
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from io import BytesIO
from PIL import Image
import numpy as np
import image_converter
import os

# -----------------------------
# CONFIG
# -----------------------------
TARGET_LAT = 0.0 # Replace with your location
TARGET_LON = 0.0
MAX_DISTANCE_M = 10000

BOUNDING_BOX = {
    "lamin": -38.6,
    "lomin": 144.2,
    "lamax": -37.5,
    "lomax": 145.5
}

RAPIDAPI_KEY = "MY_RAPID_API_KEY"  # Replace with your RapidAPI key

AIRLINE_PREFIX_MAP = {
    "QFA": "QF", "JST": "JQ", "VOZ": "VA", "RXA": "ZL", "UTY": "QQ", "QLK": "QF",
    "ANZ": "NZ", "FJI": "FJ", "UAE": "EK", "SIA": "SQ", "QTR": "QR", "ETD": "EY",
    "CPA": "CX", "MAS": "MH", "THA": "TG", "GIA": "GA", "CSN": "CZ", "CES": "MU",
    "UAL": "UA", "DAL": "DL", "AAL": "AA", "JAL": "JL", "ANA": "NH", "BAW": "BA",
}


# Padding config (fractions of banner width/height)
LOGO_PAD_H = 0.04  # horizontal padding fraction (4% each side)
LOGO_PAD_V = 0.06  # vertical padding fraction (total fraction removed from banner height)

# Text layout config
DEFAULT_FLIGHT_NUM_FONT = 28
DEFAULT_AIRCRAFT_FONT = 16
MIN_AIRCRAFT_FONT = 10
TEXT_RIGHT_LIMIT = 9.5  # data coordinate limit (x) to keep text inside card

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def parse_state_vector(s):
    return {
        "icao24": s[0],
        "callsign": s[1].strip() if s[1] else None,
        "origin_country": s[2],
        "last_contact": s[4],
        "longitude": s[5],
        "latitude": s[6],
        "baro_altitude": s[7],
        "on_ground": s[8],
        "velocity_mps": s[9],
        "heading_deg": s[10],
        "vertical_rate": s[11],
        "geo_altitude": s[13],
        "squawk": s[14],
        "spi": s[15],
        "position_source": s[16]
    }

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def opensky_callsign_to_flight_number(callsign):
    if not callsign:
        return None
    callsign = callsign.strip()
    if len(callsign) < 4:
        return None
    airline_icao = callsign[:3]
    number_part = callsign[3:].lstrip("0")
    if airline_icao not in AIRLINE_PREFIX_MAP:
        return None
    airline_iata = AIRLINE_PREFIX_MAP[airline_icao]
    return f"{airline_iata}{number_part}"

def lookup_route_aerodatabox(flight_number):
    if not flight_number or RAPIDAPI_KEY == "YOUR_RAPIDAPI_KEY_HERE":
        return None

    url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_number}"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }

    try:
        r = requests.get(url, headers=headers, params={"date": today}, timeout=10)
        if r.status_code != 200:
            print(f"AeroDataBox request failed with status code: {r.status_code}")
            return None
        data = r.json()
        if not data or len(data) == 0:
            return None

        flight = data[0]
        return {
            "flight_number": flight.get("number"),
            "airline": flight.get("airline", {}).get("name"),
            "departure_airport": flight.get("departure", {}).get("airport", {}).get("name"),
            "departure_iata": flight.get("departure", {}).get("airport", {}).get("iata"),
            "departure_city": flight.get("departure", {}).get("airport", {}).get("municipalityName"),
            "arrival_airport": flight.get("arrival", {}).get("airport", {}).get("name"),
            "arrival_iata": flight.get("arrival", {}).get("airport", {}).get("iata"),
            "arrival_city": flight.get("arrival", {}).get("airport", {}).get("municipalityName"),
            "aircraft_model": flight.get("aircraft", {}).get("model"),
        }
    except requests.exceptions.RequestException as e:
        print(f"Error making AeroDataBox request: {e}")
        return None
    except Exception as e:
        print(f"General error processing AeroDataBox response: {e}")
        return None

def get_airline_tail(flight_number):
    """Fetch airline logo via Daisycon API (logos only, not tails)."""
    airline_code = flight_number[:2]  # IATA code
    # Request larger image so it scales cleanly in the taller banner
    url = f"https://images.daisycon.io/airline/?width=600&height=600&iata={airline_code}"

    try:
        resp = requests.get(url, timeout=8)
        ctype = resp.headers.get("Content-Type", "")
        if resp.status_code == 200 and "image" in ctype and len(resp.content) > 512:
            img = mpimg.imread(BytesIO(resp.content), format='png')
            print(f"  ✓ Logo loaded from Daisycon for {airline_code}")
            return img
        else:
            print(f"  ✗ No usable logo at Daisycon for {airline_code} (status={resp.status_code}, ctype={ctype})")
    except Exception as e:
        print(f"  ⚠ Error fetching Daisycon logo for {airline_code}: {e}")

    return None

def crop_center_square(img_array):
    """Crop a NumPy image array to a centered square."""
    h, w = img_array.shape[:2]
    min_dim = min(h, w)
    top = (h - min_dim) // 2
    left = (w - min_dim) // 2
    return img_array[top:top + min_dim, left:left + min_dim]

def normalize_to_uint8(img_array):
    """Ensure image array is uint8 (0-255) instead of float32 (0-1)."""
    if img_array.dtype == np.float32 or img_array.dtype == np.float64:
        img_array = (img_array * 255).clip(0, 255).astype(np.uint8)
    return img_array

def trim_whitespace(img_array, threshold=240):
    """Trim transparent or white borders from a logo image for better fit."""
    # If RGBA, prefer alpha channel to find visible content
    if img_array.ndim == 3 and img_array.shape[2] == 4:
        alpha = img_array[:, :, 3]
        mask = alpha > 0
    else:
        # Otherwise, use brightness threshold (near-white considered border)
        # If grayscale is not possible (e.g., missing channels), fallback safely
        if img_array.ndim == 3 and img_array.shape[2] >= 3:
            gray = img_array[:, :, :3].mean(axis=2)
        else:
            gray = img_array if img_array.ndim == 2 else img_array.mean(axis=-1)
        mask = gray < threshold

    coords = np.argwhere(mask)
    if coords.size == 0:
        return img_array  # nothing to trim
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0) + 1
    return img_array[y0:y1, x0:x1]

def create_flight_card(aircraft, route_info, flight_number):
    """Create a flight card with taller full-width top logo, smaller text, and aircraft type to the right."""
    # Exact pixel dimensions: 384x184px at 100 DPI
    fig, ax = plt.subplots(figsize=(3.84, 1.84), dpi=100)
    fig.patch.set_facecolor('white')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # Fetch logo
    logo = get_airline_tail(flight_number)
    airline_code = flight_number[:2]

    # Taller full-width top strip (banner)
    strip_w = 10.0    # full width of the card
    strip_h = 2.5     # taller banner height (was 1.6)
    strip_x = 0.0
    strip_y = 5.0 - strip_h  # anchored at the top

    # Text placement below the banner
    flight_num_x = 0.5
    target_y = strip_y - 0.7  # moved lower so it doesn't crowd the taller logo

    # Render logo in the banner, preserving aspect ratio, trimmed, centered, with padding
    if logo is not None:
        try:
            logo = normalize_to_uint8(logo)
            logo = trim_whitespace(logo)

            # Convert to PIL for reliable resizing
            pil_img = Image.fromarray(logo)

            # Target pixel size for the banner area (full banner)
            banner_px_w = int(strip_w * 100)
            banner_px_h = int(strip_h * 100)

            # Apply horizontal padding (reduce available width) and vertical padding (reduce available height)
            pad_h_px = int(banner_px_w * LOGO_PAD_H)
            pad_v_px = int(banner_px_h * LOGO_PAD_V)
            avail_w = banner_px_w - (pad_h_px * 2)
            avail_h = banner_px_h - pad_v_px

            if avail_w <= 0 or avail_h <= 0:
                raise ValueError("Padding too large for banner size")

            # Width-first scale so the logo spans the available width (not full banner width)
            orig_w, orig_h = pil_img.size
            if orig_w == 0 or orig_h == 0:
                raise ValueError("Invalid logo dimensions")

            scale_w = avail_w / orig_w
            new_w = int(avail_w)
            new_h = int(orig_h * scale_w)

            pil_resized = pil_img.resize((new_w, new_h), Image.LANCZOS)

            # If the resized image is taller than the available height, center-crop vertically
            if new_h > avail_h:
                top = (new_h - avail_h) // 2
                pil_cropped_inner = pil_resized.crop((0, top, new_w, top + avail_h))
            else:
                # If shorter, pad vertically by centering on a transparent background of available size
                canvas_inner = Image.new("RGBA", (avail_w, avail_h), (255, 255, 255, 0))
                if pil_resized.mode != "RGBA":
                    pil_resized_rgba = pil_resized.convert("RGBA")
                else:
                    pil_resized_rgba = pil_resized
                y_offset = (avail_h - new_h) // 2
                canvas_inner.paste(pil_resized_rgba, (0, y_offset), pil_resized_rgba)
                pil_cropped_inner = canvas_inner

            # Now place the inner image onto a full-banner canvas so we can center horizontally with padding
            banner_canvas = Image.new("RGBA", (banner_px_w, banner_px_h), (255, 255, 255, 0))
            x_offset = pad_h_px
            y_offset = (banner_px_h - avail_h) // 2  # center inner vertically within banner area
            banner_canvas.paste(pil_cropped_inner, (x_offset, y_offset), pil_cropped_inner)

            logo_array = np.array(banner_canvas)

            # Place the logo to fill the banner width minus padding (fractions relative to axes limits 0-10 and 0-5)
            x_frac = (strip_x / 10.0) + (LOGO_PAD_H)
            width_frac = 1.0 - (2 * LOGO_PAD_H)
            # vertical placement: keep small vertical inset so banner background still visible
            y_frac = (strip_y / 5.0) + (LOGO_PAD_V / 2.0)
            height_frac = (strip_h / 5.0) - LOGO_PAD_V

            # Ensure fractions are within (0,1)
            x_frac = max(0.0, min(1.0, x_frac))
            y_frac = max(0.0, min(1.0, y_frac))
            width_frac = max(0.01, min(1.0 - x_frac, width_frac))
            height_frac = max(0.01, min(1.0 - y_frac, height_frac))

            imagebox = ax.inset_axes([x_frac, y_frac, width_frac, height_frac])
            imagebox.imshow(logo_array)
            imagebox.axis('off')
            print(f"  ✓ Aspect-ratio logo rendered for {airline_code} with padding")
        except Exception as e:
            print(f"  ⚠ Logo processing failed for {airline_code}: {e}")
            # Fallback: colored banner
            color_map = {'QF': '#E40000', 'VA': '#D9291C', 'JQ': '#FF6600', 'ZL': '#003087'}
            color = color_map.get(airline_code, '#333333')
            ax.add_patch(plt.Rectangle((strip_x, strip_y), strip_w, strip_h,
                                       facecolor=color, edgecolor='none'))
    else:
        print(f"  ⚠ Logo unavailable for {airline_code}, using fallback")
        color_map = {'QF': '#E40000', 'VA': '#D9291C', 'JQ': '#FF6600', 'ZL': '#003087'}
        color = color_map.get(airline_code, '#333333')
        ax.add_patch(plt.Rectangle((strip_x, strip_y), strip_w, strip_h,
                                   facecolor=color, edgecolor='none'))

    # -------------------------
    # Dynamic text placement to avoid overlap
    # -------------------------

    # Flight number (draw first, measure, then place aircraft text)
    flight_text = ax.text(flight_num_x, target_y, flight_number,
                          fontsize=DEFAULT_FLIGHT_NUM_FONT, fontweight='bold',
                          color='black', ha='left', va='center')

    # Force a draw so we can measure text extents
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    # Get flight number bbox in display coords and convert to fraction of figure width
    flight_bbox_disp = flight_text.get_window_extent(renderer=renderer)
    fig_w_px, fig_h_px = fig.get_size_inches() * fig.dpi
    flight_width_frac = flight_bbox_disp.width / fig_w_px
    # Convert fraction to data units (x axis spans 0..10)
    axes_data_width = ax.get_xlim()[1] - ax.get_xlim()[0]
    flight_width_data = flight_width_frac * axes_data_width

    # Compute a padding in data units (8 px)
    padding_px = 8
    padding_data = (padding_px / fig_w_px) * axes_data_width

    # Initial aircraft x position: right after flight number + padding
    aircraft_x = flight_num_x + flight_width_data + padding_data

    # Ensure aircraft_x is not less than a sensible minimum
    aircraft_x = max(aircraft_x, flight_num_x + 1.0)

    # Now try to render aircraft text with decreasing font size until it fits within TEXT_RIGHT_LIMIT
    aircraft_text_str = route_info['aircraft_model'] if route_info and route_info.get('aircraft_model') else "Unknown Aircraft"
    aircraft_font = DEFAULT_AIRCRAFT_FONT

    def text_fits(x_pos, text, fontsize):
        # Create a temporary text object (invisible) to measure
        t = ax.text(x_pos, target_y, text, fontsize=fontsize, style='italic',
                    color='#444444', ha='left', va='center', alpha=0.0)
        fig.canvas.draw()
        bbox = t.get_window_extent(renderer=renderer)
        t.remove()
        width_frac = bbox.width / fig_w_px
        width_data = width_frac * axes_data_width
        # Check right edge
        right_edge = x_pos + width_data
        return right_edge <= TEXT_RIGHT_LIMIT

    # Reduce font until it fits or reach minimum
    while aircraft_font >= MIN_AIRCRAFT_FONT and not text_fits(aircraft_x, aircraft_text_str, aircraft_font):
        aircraft_font -= 1

    # If still doesn't fit at minimum font, clamp x to TEXT_RIGHT_LIMIT - width and right-align
    if not text_fits(aircraft_x, aircraft_text_str, aircraft_font):
        # measure width at min font
        t = ax.text(0, 0, aircraft_text_str, fontsize=aircraft_font, style='italic', alpha=0.0)
        fig.canvas.draw()
        bbox = t.get_window_extent(renderer=renderer)
        t.remove()
        width_frac = bbox.width / fig_w_px
        width_data = width_frac * axes_data_width
        aircraft_x = max(flight_num_x + 0.5, TEXT_RIGHT_LIMIT - width_data)
        ha = 'left'
    else:
        ha = 'left'

    # Finally draw the aircraft text
    ax.text(aircraft_x, target_y, aircraft_text_str, fontsize=aircraft_font, style='italic',
            color='#444444', ha=ha, va='center')

    # Route info below
    if route_info:
        dept_city = route_info.get('departure_city', route_info.get('departure_iata', 'Unknown'))
        arr_city = route_info.get('arrival_city', route_info.get('arrival_iata', 'Unknown'))
    else:
        dept_city = "Unknown"
        arr_city = "Unknown"

    ax.text(flight_num_x, target_y - 1.0, f"{dept_city} → {arr_city}",
            fontsize=16, color='black', ha='left', va='center')

    plt.tight_layout(pad=0)

    # Save image
    filename = f'flight_card_{flight_number}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(filename, dpi=100, pad_inches=0,
                facecolor='white', edgecolor='none')
    print(f"\n✓ Flight card saved as: {filename} (384x184px)")
    return filename
    plt.show()

# -----------------------------
# MAIN LOOP
# -----------------------------
def main_loop():
    print("Starting OpenSky monitoring over Melbourne...")
    seen_flights = set()  # keep track of ICAO24 identifiers we’ve already processed

    while True:
        try:
            r = requests.get("https://opensky-network.org/api/states/all",
                             params=BOUNDING_BOX, timeout=10)
            r.raise_for_status()
            data = r.json()
        except:
            print("Error querying OpenSky, retrying in 10s...")
            time.sleep(10)
            continue

        if not data.get("states"):
            print("No aircraft found. Retrying in 10s...")
            time.sleep(10)
            continue

        aircraft = [parse_state_vector(s) for s in data["states"]]
        airborne = [a for a in aircraft if not a["on_ground"] and a["latitude"] and a["longitude"]]
        
        for a in airborne:
            a["distance_m"] = haversine(TARGET_LAT, TARGET_LON, a["latitude"], a["longitude"])
        
        airborne_within_10km = [a for a in airborne if a["distance_m"] <= MAX_DISTANCE_M]

        if not airborne_within_10km:
            print("No flights within 10 km. Retrying in 10s...")
            seen_flights.clear()
            time.sleep(10)
            continue

        # Then sort only these nearby flights
        airborne_within_10km.sort(key=lambda x: x["distance_m"])

        target_flight_number = None
        target_aircraft = None

        for a in airborne_within_10km:
            if a["icao24"] in seen_flights:
                continue
            flight_num = opensky_callsign_to_flight_number(a["callsign"])
            if flight_num:
                target_flight_number = flight_num
                target_aircraft = a
                seen_flights.add(a["icao24"])
                print(f"\n✓ New flight detected: {a['callsign']} -> {flight_num} ({int(a['distance_m'])}m away)")
                break

        if target_flight_number:
            route_info = lookup_route_aerodatabox(target_flight_number)
            print("Generating flight card...")
            delete_filename = image_converter.convert_png_to_bin(create_flight_card(target_aircraft, route_info, target_flight_number))
            os.remove(delete_filename)
            os.system("./display-image")
        else:
            print("No new supported flights nearby.")

        time.sleep(10)

if __name__ == "__main__":
    main_loop()
