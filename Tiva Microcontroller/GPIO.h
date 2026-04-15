/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: GPIO.h
*
* PROJECT....:
*
* DESCRIPTION: GPIO control for LEDs and inputs
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 260415  User  Module created.
*
*****************************************************************************/

#pragma once

/***************************** Include files *******************************/
#include <stdint.h>
#include <stdbool.h>
#include "data_type.h"
#include "tm4c123gh6pm.h"

/*****************************    Defines    *******************************/
// LED Colors (Port F pins)
#define RED         0x02    // PF1
#define BLUE        0x04    // PF2
#define GREEN       0x08    // PF3

#define PURPLE      (RED | BLUE)    // PF1 + PF2
#define YELLOW      (RED | GREEN)   // PF1 + PF3
#define CYAN        (BLUE | GREEN)  // PF2 + PF3

#define WHITE       (RED | BLUE | GREEN)

/*****************************   Constants   *******************************/

/*****************************   Functions   *******************************/
void init_gpio(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Initialize GPIO ports for LEDs and buttons
******************************************************************************/

void set_led(INT8U color);
/*****************************************************************************
*   Input    : Color (RED, GREEN, BLUE, or combinations)
*   Output   : -
*   Function : Set LED to specified color
******************************************************************************/

void toggle_led(INT8U color);
/*****************************************************************************
*   Input    : Color to toggle
*   Output   : -
*   Function : Toggle LED color
******************************************************************************/

void blink_led(INT8U color);
/*****************************************************************************
*   Input    : Color to blink
*   Output   : -
*   Function : Blink LED 3 times
******************************************************************************/

