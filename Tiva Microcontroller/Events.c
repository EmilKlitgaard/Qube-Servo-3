/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Events.c
*
* PROJECT....:
*
* DESCRIPTION: See module specification file (.h-file).
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 080219  MoH    Module created.
*
*****************************************************************************/

/***************************** Include files *******************************/
#include "Events.h"

/*****************************    Defines    *******************************/

/*****************************   Constants   *******************************/

/*****************************   Variables   *******************************/

/*****************************   Functions   *******************************/
BOOLEAN get_event(INT8U id) {
    INT8U result = 0;
    if (id <= MAX_EVENTS) {
        if (msg_event[id]) {
            result = msg_event[id];     // Read event
            msg_event[id] = false;      // Reset after read
        }
    }
    return (result);
}


void set_event(INT8U id) {
    if (id < MAX_EVENTS)
        msg_event[id] = true;
}


INT8U get_state(INT8U id) {
    INT8U result = 0;
    if (id <= MAX_STATES) {
        if (msg_state[id]) {
            result = msg_state[id];     // Read state
            msg_state[id] = 0;          // Reset after read
        }
    }
    return (result);
}


INT8U read_state(INT8U id) {
    if (id > MAX_STATES) return (INVALID_STATE_ID);
    return (msg_state[id]);             // Return event
}



void set_state(INT8U id, INT8U state) {
    if (id <= MAX_STATES)
        msg_state[id] = state;
}
