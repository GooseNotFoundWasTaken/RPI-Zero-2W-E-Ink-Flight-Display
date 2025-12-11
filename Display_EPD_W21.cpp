#include "Display_EPD_W21.h"
#include "Display_EPD_W21_spi.h"
#include <thread>
#include <chrono>

// Helper for delays
inline void delay_ms(int ms) {
    std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

// Color mapping
uint8_t Color_get(uint8_t color) {
    switch (color) {
        case 0x00: return white;
        case 0x01: return yellow;
        case 0x02: return red;
        case 0x03: return black;
        default: return white;
    }
}

void lcd_chkstatus(void) {
    while (isEPD_W21_BUSY == LOW) { // LOW = busy
        delay_ms(10);
    }
}

// ------------------ Initialization ------------------

void EPD_init(void) {
    delay_ms(20);
    EPD_W21_RST_0; 
    delay_ms(50);
    EPD_W21_RST_1;
    delay_ms(50);

    EPD_W21_WriteCMD(0x66);
    EPD_W21_WriteDATA(0x49);
    EPD_W21_WriteDATA(0x55);
    EPD_W21_WriteDATA(0x13);
    EPD_W21_WriteDATA(0x5D);
    EPD_W21_WriteDATA(0x05);
    EPD_W21_WriteDATA(0x10);

    EPD_W21_WriteCMD(0x4D);
    EPD_W21_WriteDATA(0x78);

    EPD_W21_WriteCMD(0x00);
    EPD_W21_WriteDATA(0x0F);
    EPD_W21_WriteDATA(0x29);

    EPD_W21_WriteCMD(0x01);
    EPD_W21_WriteDATA(0x07);
    EPD_W21_WriteDATA(0x00);

    EPD_W21_WriteCMD(0x03);
    EPD_W21_WriteDATA(0x10);
    EPD_W21_WriteDATA(0x54);
    EPD_W21_WriteDATA(0x44);

    EPD_W21_WriteCMD(0x06);
    EPD_W21_WriteDATA(0x0F);
    EPD_W21_WriteDATA(0x0A);
    EPD_W21_WriteDATA(0x2F);
    EPD_W21_WriteDATA(0x25);
    EPD_W21_WriteDATA(0x22);
    EPD_W21_WriteDATA(0x2E);
    EPD_W21_WriteDATA(0x21);

    EPD_W21_WriteCMD(0x50);
    EPD_W21_WriteDATA(0x37);

    EPD_W21_WriteCMD(0x60);
    EPD_W21_WriteDATA(0x02);
    EPD_W21_WriteDATA(0x02);

    EPD_W21_WriteCMD(0x61);
    EPD_W21_WriteDATA(Source_BITS / 256);
    EPD_W21_WriteDATA(Source_BITS % 256);
    EPD_W21_WriteDATA(Gate_BITS / 256);
    EPD_W21_WriteDATA(Gate_BITS % 256);

    EPD_W21_WriteCMD(0xE7);
    EPD_W21_WriteDATA(0x1C);

    EPD_W21_WriteCMD(0xE3);
    EPD_W21_WriteDATA(0x22);

    EPD_W21_WriteCMD(0xB6);
    EPD_W21_WriteDATA(0x6F);

    EPD_W21_WriteCMD(0xB4);
    EPD_W21_WriteDATA(0xD0);

    EPD_W21_WriteCMD(0xE9);
    EPD_W21_WriteDATA(0x01);

    EPD_W21_WriteCMD(0x30);
    EPD_W21_WriteDATA(0x08);

    EPD_W21_WriteCMD(0x04);
    lcd_chkstatus();
}

void EPD_init_Fast(void) {
    EPD_init();
    EPD_W21_WriteCMD(0xE0);
    EPD_W21_WriteDATA(0x02);

    EPD_W21_WriteCMD(0xE6);
    EPD_W21_WriteDATA(92);

    EPD_W21_WriteCMD(0xA5);
    EPD_W21_WriteDATA(0x00);
    lcd_chkstatus();
}

// ------------------ Display functions ------------------

void EPD_refresh(void) {
    EPD_W21_WriteCMD(0x12);
    EPD_W21_WriteDATA(0x00);
    lcd_chkstatus();
}

void EPD_sleep(void) {
    EPD_W21_WriteCMD(0x02);
    EPD_W21_WriteDATA(0x00);
    lcd_chkstatus();

    EPD_W21_WriteCMD(0x07);
    EPD_W21_WriteDATA(0xA5);
}

void Display_All_Black(void) {
    EPD_W21_WriteCMD(0x10);
    for (unsigned long i = 0; i < ALLSCREEN_BYTES; i++) {
        EPD_W21_WriteDATA(0x00);
    }
    EPD_refresh();
}

void Display_All_White(void) {
    EPD_W21_WriteCMD(0x10);
    for (unsigned long i = 0; i < ALLSCREEN_BYTES; i++) {
        EPD_W21_WriteDATA(0x55);
    }
    EPD_refresh();
}

void Display_All_Yellow(void) {
    EPD_W21_WriteCMD(0x10);
    for (unsigned long i = 0; i < ALLSCREEN_BYTES; i++) {
        EPD_W21_WriteDATA(0xAA);
    }
    EPD_refresh();
}

void Display_All_Red(void) {
    EPD_W21_WriteCMD(0x10);
    for (unsigned long i = 0; i < ALLSCREEN_BYTES; i++) {
        EPD_W21_WriteDATA(0xFF);
    }
    EPD_refresh();
}

// ------------------ Image display ------------------

void PIC_display(const uint8_t* picData) {
    EPD_W21_WriteCMD(0x10);
    for (unsigned int i = 0; i < Gate_BITS; i++) {
        for (unsigned int j = 0; j < Source_BITS / 4; j++) {
            uint8_t temp1 = picData[i * Source_BITS / 4 + j];
            uint8_t data_H1 = Color_get((temp1 >> 6) & 0x03) << 6;
            uint8_t data_H2 = Color_get((temp1 >> 4) & 0x03) << 4;
            uint8_t data_L1 = Color_get((temp1 >> 2) & 0x03) << 2;
            uint8_t data_L2 = Color_get(temp1 & 0x03);
            uint8_t data = data_H1 | data_H2 | data_L1 | data_L2;
            EPD_W21_WriteDATA(data);
        }
    }
    EPD_refresh();
}
