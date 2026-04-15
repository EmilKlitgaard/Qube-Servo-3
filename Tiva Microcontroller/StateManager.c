/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: StateManager.c
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

/***************************** Include files *******************************/
#include "StateManager.h"

/*****************************   Variables   *******************************/
// System state array: [SYSTEM_STATE, SYSTEM_MODE, NUMPAD_STATE, POTENTIOMETER_STATE, ENCODER_STATE]
static INT8U system_states[5] = {0};

// Number of states (for bounds checking)
static const INT8U MAX_STATES = sizeof(system_states) / sizeof(system_states[0]);

// Mutex semaphore
static xSemaphoreHandle state_mutex = NULL;

/*****************************   Functions   *******************************/
void init_state_manager(void) {
    // Create mutex for state protection (before any task uses it)
    state_mutex = xSemaphoreCreateMutex();
    
    // Verify mutex creation succeeded
    configASSERT(state_mutex != NULL);
    
    // Initialize all system states
    system_states[SYSTEM_STATE] = SYSTEM_IDLE;
    system_states[SYSTEM_MODE] = MODE_NUMPAD;
    system_states[NUMPAD_STATE] = 0;
    system_states[POTENTIOMETER_STATE] = 0;
    system_states[ENCODER_STATE] = 0;
}


void set_state(INT8U state_id, INT8U value) {
    // Validate state_id is within bounds
    if (state_id >= MAX_STATES) {
        return;
    }
    
    // Validate mutex exists
    if (state_mutex == NULL) {
        return;
    }
    
    // Take mutex with max delay (blocking call within task context)
    if (xSemaphoreTake(state_mutex, portMAX_DELAY)) {
        system_states[state_id] = value;
        xSemaphoreGive(state_mutex);
    }
}


INT8U read_state(INT8U state_id) {
    INT8U value = 0;
    
    // Validate state_id is within bounds
    if (state_id >= MAX_STATES) {
        return 0;
    }
    
    // Validate mutex exists
    if (state_mutex == NULL) {
        return 0;
    }
    
    // Take mutex with max delay (blocking call within task context)
    if (xSemaphoreTake(state_mutex, portMAX_DELAY)) {
        value = system_states[state_id];
        xSemaphoreGive(state_mutex);
    }
    
    return value;
}
