/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: GPIO.h
*
* PROJECT....:
*
* DESCRIPTION:
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 050128  KA    Module created.
*
*****************************************************************************/

#pragma once

/***************************** Include files *******************************/
#include <stdint.h>
#include <stdbool.h>
#include "data_type.h"
#include "tm4c123gh6pm.h"
#include "Timer.h"
#include "Sleep.h"

/*****************************    Defines    *******************************/
// Colors
#define RED         0x02    // PF1
#define BLUE        0x04    // PF2
#define GREEN       0x08    // PF3
#define WHITE       0x0E    // PF1 + PF2 + PF3

// Buttons
#define SW1         0x10    // PF4
#define SW2         0x01    // PF0
#define BOTH        0x11    // PF0 + PF4

/*****************************   Constants   *******************************/

/*****************************   Functions   *******************************/
extern void init_gpio(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Initialize GPIO pins. Activates RGB Led (PF1 - PF3), and SW1/SW2 Buttons (PF0 & PF4).
******************************************************************************/


extern void toggle_led(INT8U color);
/*****************************************************************************
*   Input    : color: RED, BLUE, GREEN, WHITE
*   Output   : -
*   Function : Toggle the color of the led.
******************************************************************************/


extern void set_led(INT8U color);
/*****************************************************************************
*   Input    : color: RED, BLUE, GREEN, WHITE
*   Output   : -
*   Function : Sets led to specified color.
******************************************************************************/


extern void turn_off_led(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Turns off led
******************************************************************************/


extern void blink_led(INT8U color);
/*****************************************************************************
*   Input    : color: RED, BLUE, GREEN, WHITE
*   Output   : -
*   Function : Blink the led 3 times.
******************************************************************************/


extern BOOLEAN button_pressed(INT8U button);
/*****************************************************************************
*   Input    : button: SW1, SW2, Both
*   Output   : -
*   Function : Check if button is pressed.
******************************************************************************/


extern void await_button_press(INT8U button);
/*****************************************************************************
*   Input    : button: SW1, SW2, Both
*   Output   : -
*   Function : Wait until button is pressed.
******************************************************************************/
