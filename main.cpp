#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <thread>
#include <chrono>
#include "Display_EPD_W21.h"
#include "Display_EPD_W21_spi.h"
#include "Ap_29demo.h"

int main() {
    wiringPiSetupGpio(); // Use BCM numbering

    // Setup pins
    pinMode(BUSY_PIN, INPUT);
    pinMode(RES_PIN, OUTPUT);
    pinMode(DC_PIN, OUTPUT);
    pinMode(CS_PIN, OUTPUT);

    // Setup SPI
    wiringPiSPISetup(SPI_CHANNEL, SPI_SPEED);

    // Display demo
    EPD_init();
    PIC_display(gImage_1); // Example image from demo
    EPD_sleep();
    std::this_thread::sleep_for(std::chrono::seconds(5));

    EPD_init_Fast();
    PIC_display(gImage_1);
    EPD_sleep();
    std::this_thread::sleep_for(std::chrono::seconds(5));

    return 0;
}
