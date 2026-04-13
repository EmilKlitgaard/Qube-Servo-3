/*****************************************************************************
* University of Southern Denmark
* Embedded Programming (EMP)
*
* MODULENAME.: GPIO.c
*
* PROJECT....:
*
* DESCRIPTION: See module specification file (.h-file).
*
* Change Log:
*****************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 150215  MoH   Module created.
*
*****************************************************************************/

/***************************** Include files *******************************/
#include "GPIO.h"
#include "Timer.h"
#include "Sleep.h"

/*****************************   Constants   *******************************/

/*****************************   Functions   *******************************/
void init_gpio(void) {
    // Enable the GPIO port that is used for the on-board LED.
    SYSCTL_RCGC2_R = SYSCTL_RCGC2_GPIOF; // | SYSCTL_RCGC2_GPIOD | SYSCTL_RCGC2_GPIOC;

    // Do a dummy read to insert a few cycles after enabling the peripheral.
    int dummy;
    dummy = SYSCTL_RCGC2_R;

    // Unlocks the GPIO_CR register (FP0).
    GPIO_PORTF_LOCK_R = GPIO_LOCK_KEY;   // From tm4c123gh6pm.h
    GPIO_PORTF_CR_R |= 0x01;             // Allow changes to PF0 (bit 0)

    // Set the direction as output (PF1 - PF3). And Input (PF0 & PF4)
    GPIO_PORTF_DIR_R = 0x0E;
    //GPIO_PORTC_DIR_R = 0xF0;
    //GPIO_PORTD_DIR_R = 0x4C;

    // Enable the GPIO pins for digital function (PF0 - PF4).
    GPIO_PORTF_DEN_R |= 0x1F;
    //GPIO_PORTC_DEN_R = 0xF0;
    //GPIO_PORTD_DEN_R = 0x4C;

    // Enable internal pull-up (PF0 & PF4).
    GPIO_PORTF_PUR_R |= 0x11;
}


void toggle_led(INT8U color) {
    GPIO_PORTF_DATA_R ^= color;      // Toggle led color
}


void set_led(INT8U color) {
    GPIO_PORTF_DATA_R &= ~(0x0E);    // Clear led
    GPIO_PORTF_DATA_R |= color;      // Set new color
}


void turn_off_led(void) {
    // Clear RGB LED bits
    GPIO_PORTF_DATA_R &= ~(0x0E);
}


void blink_led(INT8U color) {
    INT8U i;
    for (i=0; i<6; i++) {
        toggle_led(color);
        sleep_ms((INT64U)100);
    }
}


BOOLEAN button_pressed(INT8U button) {
    return (!(GPIO_PORTF_DATA_R & button));
}


void await_button_press(INT8U button) {
    while (GPIO_PORTF_DATA_R & button);
}
