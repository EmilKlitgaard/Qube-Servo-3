/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Sleep.c
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
* 260305  EK    Module created.
*
*****************************************************************************/

/***************************** Include files *******************************/
#include "Sleep.h"

/*****************************   Variables   *******************************/
volatile INT64U tick_count = 0;

/*****************************   Functions   *******************************/


void init_sleep(void) {
    SYSCTL_RCGCTIMER_R |= 0x01;                 // Enable clock to Timer 0
    while ((SYSCTL_PRTIMER_R & 0x01) == 0);     // Wait for timer to be ready
    TIMER0_CTL_R &= ~0x01;                      // Disable Timer 0A before configuration
    TIMER0_CFG_R = 0x00;                        // Configure Timer 0A as 32-bit timer mode
    TIMER0_TAMR_R = 0x02;                       // Configure Timer 0A as periodic mode
    TIMER0_TAILR_R = SLEEP_TIMER_LOAD_VALUE;    // Set load value for 1ms interrupt
    TIMER0_IMR_R |= 0x01;                       // Enable interrupt on Timer 0A
    NVIC_EN0_R |= 0x00080000;                   // Enable Timer 0A interrupt in NVIC (Interrupt 19)
    NVIC_PRI4_R = (NVIC_PRI4_R & 0xFF00FFFF) | 0x00200000;  // Set Timer 0A to HIGH priority (Priority 1)
    TIMER0_CTL_R |= 0x01;                       // Enable Timer 0A
}


/**
 * @brief Sleep for specified milliseconds (locally blocking)
 */
void sleep_ms(INT64U ms) {
    // Set target time
    const INT64U tick_target = tick_count + SLEEP_MILLISEC(ms);

    // Wait until target reached. Interrupts continue, so other timers continue.
    while (tick_count < tick_target);
}


/**
 * @brief Get current system tick count
 */
INT64U get_tick(void) {
    return tick_count;
}


/**
 * @brief Timer 0 interrupt handler - runs every 1ms (sleep timer)
 */
// !!! Remember to enabled handler in "tm4c123gh6pm_startup_ccs.c" !!!
void sleep_timer_handler(void) {
    // Clear interrupt flag for Timer 0
    TIMER0_ICR_R |= 0x01;

    // Increment global tick counter
    tick_count++;
}
