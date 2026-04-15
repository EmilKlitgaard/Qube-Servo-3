/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: StateManager.h
*
* PROJECT....:
*
* DESCRIPTION: State management with mutex protection for FreeRTOS
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
#include <FreeRTOS.h>
#include <semphr.h>
#include "data_type.h"
#include "global_variables.h"

/*****************************    Defines    *******************************/

/*****************************   Constants   *******************************/

/*****************************   Functions   *******************************/
void init_state_manager(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Initialize state manager (mutexes, initial states)
******************************************************************************/

void set_state(INT8U state_id, INT8U value);
/*****************************************************************************
*   Input    : State ID, Value to set
*   Output   : -
*   Function : Thread-safe state setter
******************************************************************************/

INT8U read_state(INT8U state_id);
/*****************************************************************************
*   Input    : State ID
*   Output   : State value
*   Function : Thread-safe state getter
******************************************************************************/

/****************************** End Of Module *******************************/
