#include "Display_EPD_W21_spi.h"

// SPI write a single byte
void SPI_Write(uint8_t value) {
    wiringPiSPIDataRW(SPI_CHANNEL, &value, 1);
}

// Write a command byte
void EPD_W21_WriteCMD(uint8_t command) {
    EPD_W21_CS_0;
    EPD_W21_DC_0;  // command mode
    SPI_Write(command);
    EPD_W21_CS_1;
}

// Write a data byte
void EPD_W21_WriteDATA(uint8_t datas) {
    EPD_W21_CS_0;
    EPD_W21_DC_1;  // data mode
    SPI_Write(datas);
    EPD_W21_CS_1;
}
