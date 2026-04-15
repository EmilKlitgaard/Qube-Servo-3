/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Sleep.h
*
* PROJECT....:
*
* DESCRIPTION: Sleep/delay functions using FreeRTOS
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
#include "FreeRTOS.h"
#include "task.h"
#include "data_type.h"

/*****************************    Defines    *******************************/

/*****************************   Constants   *******************************/

/*****************************   Functions   *******************************/
void sleep_ms(INT32U ms);
/*****************************************************************************
*   Input    : Milliseconds to sleep
*   Output   : -
*   Function : Sleep for specified milliseconds using FreeRTOS
******************************************************************************/

/****************************** End Of Module *******************************/
