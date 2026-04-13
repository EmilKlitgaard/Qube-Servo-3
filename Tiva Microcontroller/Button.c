/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Handler.c
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
#include "Button.h"
#include "Print.h"
#include "GPIO.h"

/*****************************   Constants   *******************************/
volatile INT8U pending_button = 0;


/*****************************   Functions   *******************************/
void init_button_handler(void) {
    // Configure GPIOF Interrupts for Both Pins (PF4, PF0)
    GPIO_PORTF_IS_R &= ~(0x11);     // Edge-sensitive
    GPIO_PORTF_IEV_R &= ~(0x11);    // Trigger on press (Set to Falling edge, as buttons are active low)
    GPIO_PORTF_ICR_R = 0x11;        // Clear any prior interrupt
    GPIO_PORTF_IM_R |= 0x11;        // Unmask interrupts
    NVIC_EN0_R |= 0x40000000;       // Enable interrupt 30 (GPIOF) in NVIC
    NVIC_PRI7_R = (NVIC_PRI7_R & 0xFFFFFF1F) | 0x60; // Set GPIO Port F (Button) to priority 3 (lower)
}


// !!! Remember to enabled handler in "tm4c123gh6pm_startup_ccs.c" !!!
void button_handler(void) {
    // Check for PF4 (SW1) press:
    if (GPIO_PORTF_MIS_R & 0x10) {
        INT8U state = read_state(SYSTEM_STATE);
        if (state == SYSTEM_IDLE) {
            print_str("System Running...");
            set_state(SYSTEM_STATE, SYSTEM_RUNNING);
            //set_led(GREEN);
        } else {
            print_str("System Idle...");
            set_state(SYSTEM_STATE, SYSTEM_IDLE);
            set_led(RED);
        }
        GPIO_PORTF_ICR_R = 0x10;        // Clear interrupt
    }

    // Check for PF0 (SW2) press:
    if (GPIO_PORTF_MIS_R & 0x01) {
        INT8U mode = read_state(SYSTEM_MODE);
        if (mode == MODE_NUMPAD) {
            set_state(SYSTEM_MODE, MODE_POTENTIOMETER);
            print_str("\n[MODE]: Potentiometer mode");
        } else {
            set_state(SYSTEM_MODE, MODE_NUMPAD);
            print_str("\n[MODE]: Numpad mode");
        }
        GPIO_PORTF_ICR_R = 0x01;        // Clear interrupt
    }
}
