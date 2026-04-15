/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Sleep.c
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

/***************************** Include files *******************************/
#include "Sleep.h"

/*****************************   Functions   *******************************/
void sleep_ms(INT32U ms) {
    vTaskDelay(ms / portTICK_RATE_MS);
}
