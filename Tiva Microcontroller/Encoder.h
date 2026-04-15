/*****************************************************************************
* Odense University College of Enginerring
* Embedded C Programming (ECP)
*
* MODULENAME.: Encoder.h
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
#include <FreeRTOS.h>
#include <task.h>
#include "tm4c123gh6pm.h"
#include "global_variables.h"
#include "data_type.h"
#include "StateManager.h"
#include "Print.h"
#include "Sleep.h"

/*****************************    Defines    *******************************/
#define INVALID_ENCODER_VALUE    0xFF   // Invalid encoder input

// Encoder direction definitions
#define ENCODER_STEADY           0      // No movement
#define ENCODER_LEFT             1      // Encoder rotated left
#define ENCODER_RIGHT            2      // Encoder rotated right

// Encoder value limits and increments
#define ENC_INCREMENT        5      // Amount to increment/decrement encoder value per step
#define ENC_START_VALUE      50     // Starting value for encoder (e.g., mid-point)

// Scan delays
#define ENCODER_SCAN_MS      5
#define ENCODER_SLEEP_MS     50

// PA5, PA6, PA7 for encoder pins
#define ENC_A_PIN              0x20        // PA5 (channel A)
#define ENC_B_PIN              0x40        // PA6 (channel B)
#define ENC_MASK               0x60        // Mask for A and B (PA5 and PA6)
#define ENC_P2_PIN             0x80        // PA7 (push button)
#define ENC_MASK_ALL           0xE0        // PA5, PA6, PA7 combined

/*****************************   Types   ***********************************/
/*****************************   Constants   *******************************/
/*****************************   Functions   *******************************/
extern void init_encoder(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Initialize encoder GPIO pins on PA5, PA6, PA7.
******************************************************************************/


INT8U scan_encoder(void);
/*****************************************************************************
*   Input    : -
*   Output   : Encoder angle value (0-180, representing -90 to +90 degrees)
*   Function : Returns the encoder angle value. Returns INVALID_ENCODER_INPUT (0xFF) on error.
******************************************************************************/


extern void encoder_task(void *pvParameters);
/*****************************************************************************
*   Input    : FreeRTOS task parameter (unused)
*   Output   : -
*   Function : FreeRTOS task for encoder scanning
******************************************************************************/



