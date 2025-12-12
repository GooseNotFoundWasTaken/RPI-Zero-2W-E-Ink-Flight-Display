#ifndef _DISPLAY_EPD_W21_SPI_
#define _DISPLAY_EPD_W21_SPI_

#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <cstdint>
#include <chrono>
#include <thread>

// BCM GPIO mapping
#define BUSY_PIN 4
#define RES_PIN 17
#define DC_PIN 27
#define CS_PIN 22

// SPI channel and speed
#define SPI_CHANNEL 0
#define SPI_SPEED 10000000 // 10 MHz, safe starting point

// IO macros
#define EPD_W21_RST_0 digitalWrite(RES_PIN, LOW)
#define EPD_W21_RST_1 digitalWrite(RES_PIN, HIGH)
#define EPD_W21_DC_0  digitalWrite(DC_PIN, LOW)
#define EPD_W21_DC_1  digitalWrite(DC_PIN, HIGH)
#define EPD_W21_CS_0  digitalWrite(CS_PIN, LOW)
#define EPD_W21_CS_1  digitalWrite(CS_PIN, HIGH)

// Busy pin logic: LOW = busy, HIGH = idle
#define isEPD_W21_BUSY (digitalRead(BUSY_PIN))

// Function prototypes
void SPI_Write(uint8_t value);
void EPD_W21_WriteDATA(uint8_t datas);
void EPD_W21_WriteCMD(uint8_t command);

#endif
