#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <thread>
#include <chrono>
#include <vector>
#include <fstream>
#include <iostream>
#include "Display_EPD_W21.h"
#include "Display_EPD_W21_spi.h"

// Function to load .bin file into a vector

std::vector<uint8_t> loadImageBin(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary);
    if (!file) {
        std::cerr << "Failed to open " << filename << std::endl;
        return {};
    }
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(file)),
                               std::istreambuf_iterator<char>());
    return data;
}

int main() {
    wiringPiSetupGpio();

    // Setup pins
    pinMode(BUSY_PIN, INPUT);
    pinMode(RES_PIN, OUTPUT);
    pinMode(DC_PIN, OUTPUT);
    pinMode(CS_PIN, OUTPUT);

    // Setup SPI
    wiringPiSPISetup(SPI_CHANNEL, 10000000);

    // Load the image
    auto image = loadImageBin("image.bin");

    if (image.empty()) {
        std::cerr << "Image is empty, exiting." << std::endl;
        return 1;
    }

    // Display
    EPD_init();
    PIC_display(image.data());  // <-- pass pointer to vector data
    EPD_sleep();
    std::this_thread::sleep_for(std::chrono::seconds(5));

    EPD_init_Fast();
    PIC_display(image.data());  // <-- same here
    EPD_sleep();
    std::this_thread::sleep_for(std::chrono::seconds(5));

    return 0;
}

