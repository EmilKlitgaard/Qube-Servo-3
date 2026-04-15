/*****************************************************************************
* Odense University College of Enginerring
* Embedded C Programming (ECP)
*
* MODULENAME.: Encoder.c
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
* 090928  MoH   Module created.
*
*****************************************************************************/

/***************************** Include files *******************************/
#include "Encoder.h"
#include "StateManager.h"
#include "Print.h"
#include "Sleep.h"
#include <FreeRTOS.h>
#include <task.h>

/*****************************    Defines    *******************************/
// Quadrature direction lookup table: only 2 rows for meaningful states
// Row 0: transitions from 0x00 (detent start)
// Row 1: transitions from 0x03 (detent approach)
static const INT8U direction_table[2][4] = {
    { ENCODER_STEADY, ENCODER_RIGHT, ENCODER_LEFT, ENCODER_STEADY },    // From 0x00
    { ENCODER_STEADY, ENCODER_LEFT, ENCODER_RIGHT, ENCODER_STEADY }     // From 0x03
};
/*****************************   Constants   *******************************/
/*****************************   Variables   *******************************/
static INT8S encoder_value = ENC_START_VALUE;
static INT8U encoder_state = 0;
static INT8U last_p2 = 1;

/*****************************   Functions   *******************************/
void init_encoder(void) {
    // Enable GPIOA clock
    SYSCTL_RCGC2_R |= SYSCTL_RCGC2_GPIOA;
    
    // Wait for clock to stabilize
    INT32U delay = 0;
    while (delay < 10) delay++;
    
    // Configure PA5, PA6, PA7 as digital input pins
    GPIO_PORTA_AFSEL_R &= ~0xE0;       // Disable alternate function for PA5, PA6, PA7
    GPIO_PORTA_DIR_R &= ~0xE0;         // Configure PA5, PA6, PA7 as input (bits 7,6,5)
    GPIO_PORTA_PUR_R |= 0xE0;          // Enable pull-up resistors on PA5, PA6, PA7
    GPIO_PORTA_DEN_R |= 0xE0;          // Enable digital operation on PA5, PA6, PA7
    
    // Initialize encoder state: read PA5 (A) and PA6 (B)
    INT8U cur_a = (GPIO_PORTA_DATA_R & ENC_A_PIN) ? 1 : 0;   // PA5
    INT8U cur_b = (GPIO_PORTA_DATA_R & ENC_B_PIN) ? 1 : 0;   // PA6
    encoder_state = cur_a + (cur_b ? 2 : 0);                 // State: A + (B*2)
    
    last_p2 = (GPIO_PORTA_DATA_R & ENC_P2_PIN) ? 1 : 0;      // PA7
}


INT8U scan_encoder(void) {
    INT8U cur_a, cur_b, cur_p2;
    INT8U current_state;
    INT8U prev_state = encoder_state;
    INT8U direction = INVALID_ENCODER_VALUE;
    
    // Read current pin states using mask constants from header
    cur_a = (GPIO_PORTA_DATA_R & ENC_A_PIN) ? 1 : 0;         // PA5 (channel A)
    cur_b = (GPIO_PORTA_DATA_R & ENC_B_PIN) ? 1 : 0;         // PA6 (channel B)
    cur_p2 = (GPIO_PORTA_DATA_R & ENC_P2_PIN) ? 1 : 0;       // PA7 (button)
    
    // Create 2-bit state: bits [1:0] = (B, A)
    current_state = cur_a + (cur_b ? 2 : 0);
    
    if (current_state != prev_state) {
        // Use 2-row lookup table: select row based on prev_state (0x00 or 0x03)
        INT8U table_row = (prev_state == 0x03) ? 1 : 0;
        direction = direction_table[table_row][current_state];
        
        // Update encoder state for next cycle
        encoder_state = current_state;
    }

    if (direction != ENCODER_STEADY && direction != INVALID_ENCODER_VALUE) {
        // Update encoder value based on direction
        if (direction == ENCODER_RIGHT) {
            encoder_value += ENC_INCREMENT;  // Increment encoder value
        } 
        if (direction == ENCODER_LEFT) {
            encoder_value -= ENC_INCREMENT;  // Decrement encoder value
        }
    }
    
    // Check button press separately (falling edge on P2: 1 -> 0)
    if (last_p2 == 1 && cur_p2 == 0) {
        encoder_value = ENC_START_VALUE;  // Reset encoder value on button press
    }
    
    // Update button state for next cycle
    last_p2 = cur_p2;

    // Clamp encoder value to 0 to 100.
    if (encoder_value > 100) {
        encoder_value = 100;
    }
    if (encoder_value < 0) {
        encoder_value = 0;
    }

    return encoder_value;
}


/*****************************   Encoder Task   *****************************/
void encoder_task(void *pvParameters) {
    INT8U value = INVALID_ENCODER_VALUE;
    INT8U last_value = INVALID_ENCODER_VALUE;
    INT8U system_state;
    INT8U system_mode;

    while (true) {
        system_state = read_state(SYSTEM_STATE);
        
        if (system_state == SYSTEM_RUNNING) {
            system_mode = read_state(SYSTEM_MODE);
            
            if (system_mode == MODE_ENCODER) {
                value = scan_encoder();
                
                // Only update state and print if rotation was detected
                if (value != INVALID_ENCODER_VALUE && value != last_value) {
                    set_state(ENCODER_STATE, value);
                    print_var(encoder_value);
                    last_value = value;
                }
            }
            // Polling interval for encoder scanning
            sleep_ms(ENCODER_SCAN_MS);  
        } else {
            // System idle, slower polling to reduce CPU usage
            sleep_ms(ENCODER_SLEEP_MS);
        }
    }
}
