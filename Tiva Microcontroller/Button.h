/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Handler.h
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
#include "global_variables.h"
#include "Events.h"

/*****************************    Defines    *******************************/
#define BUTTON_STATE_MACHINE    0   // Set to 1 to activate the state machine.

/*****************************   Constants   *******************************/
extern volatile INT8U pending_button;

/*****************************   Functions   *******************************/
extern void init_button_handler(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Initialize the handler
******************************************************************************/


extern void button_handler(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : The button handler function (Runs whenever the handler is triggered).
******************************************************************************/


extern void button_loop(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Infinite loop for handling button presses.
******************************************************************************/
