#ifndef _DISPLAY_EPD_W21_H_
#define _DISPLAY_EPD_W21_H_

#include <cstdint>

// 2-bit color definitions
#define black   0x00
#define white   0x01
#define yellow  0x02
#define red     0x03

#define Source_BITS 184
#define Gate_BITS   384
#define ALLSCREEN_BYTES (Source_BITS * Gate_BITS / 4)

// EPD functions
void EPD_init(void);
void EPD_init_Fast(void);
void EPD_sleep(void);
void EPD_refresh(void);
void lcd_chkstatus(void);
void PIC_display(const uint8_t* picData);
void Display_All_Black(void);
void Display_All_White(void);
void Display_All_Yellow(void);
void Display_All_Red(void);
uint8_t Color_get(uint8_t color);

#endif
