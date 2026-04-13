/*****************************************************************************
* Odense University College of Enginerring
* Embedded C Programming (ECP)
*
* MODULENAME.: Potentiometer.h
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
#include "global_variables.h"
#include "tm4c123gh6pm.h"
#include "Sleep.h"

/*****************************    Defines    *******************************/
#define INVALID_POTENTIOMETER_INPUT    0xFF    // Invalid potentiometer input

// PB5 maps to ADC0 AIN11 (analog input channel 11)
#define POT_AIN_CHANNEL        11
#define POT_GPIO_PIN           0x20        // PB5

/*****************************   Types   ***********************************/


/*****************************   Constants   *******************************/
extern volatile INT8U potentiometer_input;

/*****************************   Functions   *******************************/
extern void init_potentiometer(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Initialize potentiometer ADC on PB5 (AIN11).
******************************************************************************/


extern INT8U scan_potentiometer(void);
/*****************************************************************************
*   Input    : -
*   Output   : Potentiometer angle value (0-180, representing -90 to +90 degrees)
*   Function : Returns the potentiometer angle value. Returns INVALID_POTENTIOMETER_INPUT (0xFF) on error.
******************************************************************************/



