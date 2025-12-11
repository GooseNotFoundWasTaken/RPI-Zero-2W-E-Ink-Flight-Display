#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <thread>
#include <chrono>
#include "Display_EPD_W21.h"
#include "Display_EPD_W21_spi.h"

int main() {
    // Initialize WiringPi
    wiringPiSetupGpio(); // BCM numbering

    // Set pin modes
    pinMode(BUSY_PIN, INPUT);
    pinMode(RES_PIN, OUTPUT);
    pinMode(DC_PIN, OUTPUT);
    pinMode(CS_PIN, OUTPUT);

    // Setup SPI
    wiringPiSPISetup(SPI_CHANNEL, SPI_SPEED);

    // Initialize display
    EPD_init();

    // Clear screen to white
    Display_All_White();

    // Put display to sleep
    EPD_sleep();

    // Optional: small delay to ensure sleep command processed
    std::this_thread::sleep_for(std::chrono::seconds(1));

    return 0;
}
