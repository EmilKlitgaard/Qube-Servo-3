/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Button.c
*
* PROJECT....:
*
* DESCRIPTION: Button handling using FreeRTOS tasks
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 080219  MoH    Module created.
* 260415  User   Converted to FreeRTOS task
*
*****************************************************************************/

/***************************** Include files *******************************/
#include "Button.h"
#include "Print.h"
#include "GPIO.h"
#include "StateManager.h"
#include <FreeRTOS.h>
#include <task.h>

/*****************************   Constants   *******************************/
volatile INT8U pending_button = 0;

/*****************************   Variables   *******************************/
static INT8U last_sw1_state = 1;  // PF4 button state (active low)
static INT8U last_sw2_state = 1;  // PF0 button state (active low)

/*****************************   Functions   *******************************/
void init_button_handler(void) {
    // Button GPIO is already configured by init_gpio() in GPIO.c
}

// Polling-based button reading function
static INT8U read_button_sw1(void) {
    return GPIO_PORTF_DATA_R & BUTTON_SW1;  // Read PF4 (SW1)
}

static INT8U read_button_sw2(void) {
    return GPIO_PORTF_DATA_R & BUTTON_SW2;  // Read PF0 (SW2)
}


/**
 * Button task - Polls buttons periodically for state changes
 * 
 * Button behavior:
 * - PF4 (SW1): Toggle SYSTEM_STATE (IDLE <-> RUNNING)
 * - PF0 (SW2): Toggle SYSTEM_MODE (NUMPAD <-> POTENTIOMETER)
 * 
 * Polling approach used instead of interrupts for simplicity
 * with FreeRTOS task scheduling
 */
void button_task(void *pvParameters) {
    INT8U current_sw1, current_sw2;
    INT8U state;
    INT8U mode;
    
    // Initialize button states (active low = 1, pressed = 0)
    last_sw1_state = read_button_sw1();
    last_sw2_state = read_button_sw2();
    
    while (true) {
        // Read current button states
        current_sw1 = read_button_sw1();
        current_sw2 = read_button_sw2();

        // Check PF4 (SW1) - IDLE/RUNNING toggle
        if (current_sw1 != last_sw1_state) {
            if (current_sw1 == 0) {  // Button pressed (low)
                state = read_state(SYSTEM_STATE);
                if (state == SYSTEM_IDLE) {
                    print_str("System Running...");
                    set_state(SYSTEM_STATE, SYSTEM_RUNNING);
                } else {
                    print_str("System Idle...");
                    set_state(SYSTEM_STATE, SYSTEM_IDLE);
                    set_led(RED);
                }
                // Debounce delay
                sleep_ms(BUTTON_DEBOUNCE_MS);
            }
            last_sw1_state = current_sw1;
        }

        // Check PF0 (SW2) - MODE toggle
        if (current_sw2 != last_sw2_state) {
            if (current_sw2 == 0) {  // Button pressed (low)
                mode = read_state(SYSTEM_MODE);
                if (mode == MODE_ENCODER) {
                    set_state(SYSTEM_MODE, MODE_POTENTIOMETER);
                    print_str("\n[MODE]: Potentiometer mode");
                } 
                if (mode == MODE_POTENTIOMETER) {
                    set_state(SYSTEM_MODE, MODE_NUMPAD);
                    print_str("\n[MODE]: Numpad mode");
                }
                if (mode == MODE_NUMPAD) {
                    set_state(SYSTEM_MODE, MODE_ENCODER);
                    print_str("\n[MODE]: Encoder mode");
                }
                // Debounce delay
                sleep_ms(BUTTON_DEBOUNCE_MS);
            }
            last_sw2_state = current_sw2;
        }

        // Scan buttons periodically
        sleep_ms(BUTTON_SCAN_MS);
    }
}
