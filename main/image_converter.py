from PIL import Image
import sys

def convert_png_to_bin(filename):
	SOURCE_BITS = 184
	GATE_BITS = 384

	# Map RGB tuples to EPD 2-bit codes
	EPD_COLORS = {
	    (0,0,0)       : 0x03,  # Black
	    (255,255,255) : 0x00,  # White
	    (255,255,0)   : 0x01,  # Yellow
	    (255,0,0)     : 0x02   # Red
	}

	def nearest_epd_color(r,g,b):
	    # Find the RGB key with the minimum distance
	    best_dist = None
	    best_code = None
	    for (tr, tg, tb), code in EPD_COLORS.items():
	        dist = (r-tr)**2 + (g-tg)**2 + (b-tb)**2
	        if best_dist is None or dist < best_dist:
	            best_dist = dist
	            best_code = code
	    return best_code

	def png_to_bin(input_file, output_file):
	    img = Image.open(input_file).convert('RGB')
	    w, h = img.size

	    # Rotate if necessary
	    if (w, h) == (384, 184):
	        img = img.transpose(Image.ROTATE_90)
	    elif (w, h) != (184, 384):
	        raise ValueError(f"Image must be 384x184 or 184x384. Got {w}x{h}")

	    pixels = list(img.getdata())

	    with open(output_file, 'wb') as f:
	        for row in range(GATE_BITS):
	            for col in range(0, SOURCE_BITS, 4):
	                byte = 0
	                for i in range(4):
	                    r,g,b = pixels[row*SOURCE_BITS + col + i]
	                    code = nearest_epd_color(r,g,b)
	                    shift = (3-i)*2
	                    byte |= (code & 0x03) << shift
	                f.write(byte.to_bytes(1,'big'))
	png_to_bin(filename, "image.bin")
	return(filename)
