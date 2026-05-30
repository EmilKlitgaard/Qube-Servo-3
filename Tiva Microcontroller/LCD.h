/****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: LCD.h
*
* PROJECT....:
*
* DESCRIPTION: HD44780U LCD lcd driver (4-bit mode)
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 260422  Copilot  Module created.
*
*****************************************************************************/

#pragma once

/***************************** Include files *******************************/
#include <stdint.h>
#include <stdbool.h>
#include "data_type.h"
#include "tm4c123gh6pm.h"
#include "global_variables.h"

/*****************************    Defines    *******************************/
// LCD data pins (Port C)
#define LCD_D4_PIN      0x10    // PC4
#define LCD_D5_PIN      0x20    // PC5
#define LCD_D6_PIN      0x40    // PC6
#define LCD_D7_PIN      0x80    // PC7

// LCD control pins (Port D)
#define LCD_RS_PIN      0x04    // PD2
#define LCD_E_PIN       0x08    // PD3

/*****************************   Constants   *******************************/

/*****************************   Functions   *******************************/
extern void init_lcd(void);
/****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Initialize HD44780U LCD in 4-bit mode
******************************************************************************/

extern void clear_lcd(void);
/****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Clear entire LCD lcd and move cursor home
******************************************************************************/

extern void lcd_command(INT8U cmd);
/****************************************************************************
*   Input    : LCD command byte
*   Output   : -
*   Function : Send command byte to LCD controller
******************************************************************************/

extern void write_char(char ch);
/****************************************************************************
*   Input    : Character
*   Output   : -
*   Function : Write one character at current cursor position
******************************************************************************/

extern void write_str(const char *str);
/****************************************************************************
*   Input    : String
*   Output   : -
*   Function : Write zero-terminated string at current cursor position
******************************************************************************/

extern void set_cursor(INT8U x, INT8U y);
/****************************************************************************
*   Input    : x column (0..15), y row (0..1)
*   Output   : -
*   Function : Set LCD cursor position
******************************************************************************/

extern void write_str_at(INT8U x, INT8U y, const char *str);
/****************************************************************************
*   Input    : x column, y row, string
*   Output   : -
*   Function : Set cursor position and write string
******************************************************************************/

extern void lcd_task(void);
/****************************************************************************
*   Input    : -
*   Output   : -
*   Function : FreeRTOS task to update LCD based on system state and mode
******************************************************************************/

/****************************** End Of Module *******************************/
