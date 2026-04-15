/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: GPIO.c
*
* PROJECT....:
*
* DESCRIPTION: GPIO control for LEDs and inputs
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
#include "GPIO.h"
#include "Sleep.h"

/*****************************    Defines    *******************************/

/*****************************   Constants   *******************************/

/*****************************   Variables   *******************************/

/*****************************   Functions   *******************************/
void init_gpio(void) {
    // Enable the GPIO port F
    SYSCTL_RCGC2_R |= SYSCTL_RCGC2_GPIOF;

    // Do a dummy read to insert a few cycles after enabling the peripheral
    int dummy = SYSCTL_RCGC2_R;
    
    // Unlocks the GPIO_CR register (FP0).
    GPIO_PORTF_LOCK_R = GPIO_LOCK_KEY;   // From tm4c123gh6pm.h
    GPIO_PORTF_CR_R |= 0x01;             // Allow changes to PF0 (bit 0)
    
    // Configure button pins (PF4, PF0) as inputs
    GPIO_PORTF_DIR_R &= ~(0x01 | 0x10);          // Input
    GPIO_PORTF_DEN_R |= (0x01 | 0x10);           // Digital enable
    GPIO_PORTF_PUR_R |= (0x01 | 0x10);           // Enable pull-up

    // Configure LED pins (PF1, PF2, PF3) as outputs (digital)
    GPIO_PORTF_DIR_R |= (RED | BLUE | GREEN);    // Output
    GPIO_PORTF_DEN_R |= (RED | BLUE | GREEN);    // Digital enable
    GPIO_PORTF_DATA_R &= ~(RED | BLUE | GREEN);  // Start with all LEDs off
}


void set_led(INT8U color) {
    GPIO_PORTF_DATA_R = (GPIO_PORTF_DATA_R & ~(RED | BLUE | GREEN)) | color;
}


void toggle_led(INT8U color) {
    GPIO_PORTF_DATA_R ^= color;
}


void blink_led(INT8U color) {
    int i;
    for (i = 0; i < 3; i++) {
        set_led(color);
        sleep_ms(100);
        set_led(0);
        sleep_ms(100);
    }
}
