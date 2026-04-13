/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Events.h
*
* PROJECT....:
*
* DESCRIPTION: Set global event states
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
#include <stdbool.h>
#include "data_type.h"

/*****************************    Defines    *******************************/
#define MAX_EVENTS 64
#define MAX_STATES 64
#define INVALID_STATE_ID   0xFF

/*****************************   Constants   *******************************/
INT8U msg_event[MAX_EVENTS];
INT8U msg_state[MAX_STATES];

/*****************************   Functions   *******************************/
BOOLEAN get_event(INT8U);
/*****************************************************************************
*   Input    : id
*   Output   : event
*   Function : Read a event and reset
******************************************************************************/


void set_event(INT8U);
/*****************************************************************************
*   Input    : id
*   Output   : -
*   Function : Set a event to true
******************************************************************************/


INT8U get_state(INT8U);
/*****************************************************************************
*   Input    : id
*   Output   : event
*   Function : Get a state and reset afterwards
******************************************************************************/


INT8U read_state(INT8U);
/*****************************************************************************
*   Input    : id
*   Output   : event
*   Function : Read a state
******************************************************************************/



void set_state(INT8U, INT8U);
/*****************************************************************************
*   Input    : id, event
*   Output   : -
*   Function : Set a state
******************************************************************************/

