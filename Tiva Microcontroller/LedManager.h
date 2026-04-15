/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: LedManager.h
*
* PROJECT....:
*
* DESCRIPTION: LED management task for system status and mode indication
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 260415  User  Module created (merged status_led and led_controller)
*
*****************************************************************************/

#pragma once

/***************************** Include files *******************************/
#include <stdint.h>
#include <stdbool.h>
#include "data_type.h"

/*****************************    Defines    *******************************/

/*****************************   Constants   *******************************/

/*****************************   Functions   *******************************/
void led_manager_task(void *pvParameters);
/*****************************************************************************
*   Input    : FreeRTOS task parameter (unused)
*   Output   : -
*   Function : FreeRTOS task managing all LED behavior:
*              - Status indicator (PD6) blinking
*              - Mode/state LEDs (PF1-3) color control
******************************************************************************/
