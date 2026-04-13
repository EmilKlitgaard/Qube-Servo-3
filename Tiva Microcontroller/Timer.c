/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Timer.c
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
#include "Timer.h"
#include "Sleep.h"

/*****************************   Variables   *******************************/
volatile INT8U active_timers = 0;

/*****************************   Functions   *******************************/
void init_timer(void) {
    // Initialize timer array for single/repeating timers
    int i;
    for (i=0; i<MAX_TIMERS; i++) {
        timers[i].active = false;
        timers[i].callback = 0;
        timers[i].countdown = 0;
        timers[i].interval_ms = 0;
        timers[i].repeat = false;
    }

    // Setup Timer 1 for single/repeating timers
    SYSCTL_RCGCTIMER_R |= 0x02;             // Enable clock to Timer 1
    while ((SYSCTL_PRTIMER_R & 0x02) == 0); // Wait for timer to be ready
    TIMER1_CTL_R &= ~0x01;                  // Disable Timer 1A before configuration
    TIMER1_CFG_R = 0x00;                    // Configure Timer 1A as 32-bit timer mode
    TIMER1_TAMR_R = 0x02;                   // Configure Timer 1A as periodic mode
    TIMER1_TAILR_R = TIMER_LOAD_VALUE;      // Set load value for 1ms interrupt
    TIMER1_IMR_R |= 0x01;                   // Enable interrupt on Timer 1A
    NVIC_EN0_R |= 0x00200000;               // Enable Timer 1A interrupt in NVIC (Interrupt 21)
    NVIC_PRI5_R = (NVIC_PRI5_R & 0xFFFFFF1F) | 0x40;  // Set Timer 1A to lower priority (Priority 2)
    TIMER1_CTL_R |= 0x01;                   // Enable Timer 1A
}


/**
 * @brief Start a repeating interval timer
 */
timer_id start_repeating_timer(INT32U interval_ms, timer_callback callback) {
    return add_timer(interval_ms, callback, true);
}


/**
 * @brief Start a single execution timer
 */
timer_id start_timer(INT32U interval_ms, timer_callback callback) {
    return add_timer(interval_ms, callback, false);
}


/**
 * @brief Add a interval timer
 */
timer_id add_timer(INT32U interval_ms, timer_callback callback, BOOLEAN repeat) {
    // Find free timer slot
    INT8U i;
    for (i=0; i<MAX_TIMERS; i++) {
        if (!timers[i].active) {
            // Found free slot - initialize it
            timers[i].interval_ms = MILLISEC(interval_ms);
            timers[i].countdown = MILLISEC(interval_ms);
            timers[i].callback = callback;
            timers[i].active = true;
            timers[i].repeat = repeat;

            active_timers++;
            return i;  // Return timer ID
        }
    }

    // No free timers available
    return INVALID_TIMER_ID;
}


/**
 * @brief Update an existing timer or make a new if it does not exist
 */
timer_id update_timer(timer_id id, INT32U interval_ms, timer_callback callback) {
    if (id != INVALID_TIMER_ID && timers[id].active) {
        timers[id].interval_ms = MILLISEC(interval_ms);
        timers[id].countdown = MILLISEC(interval_ms);
        timers[id].callback = callback;
        return id;
    } else {
        return add_timer(interval_ms, callback, false);
    }
}


/**
 * @brief Stop a running interval timer
 */
bool stop_timer(timer_id id) {
    if (id >= MAX_TIMERS) return false;
    if (!timers[id].active) return false;

    timers[id].active = false;
    timers[id].callback = 0;

    active_timers--;

    return true;
}


/**
 * @brief Timer 1 interrupt handler - runs every 1ms (single/repeating timers)
 */
// !!! Remember to enabled handler in "tm4c123gh6pm_startup_ccs.c" !!!
void timer_handler(void) {
    // Clear interrupt flag for Timer 1
    TIMER1_ICR_R |= 0x01;

    if (!active_timers) return;

    // Process all active interval timers
    INT8U timers_found = 0;
    int i;
    for (i=0; i<MAX_TIMERS; i++) {
        if (timers[i].active) {
            // Increment timers_found
            timers_found++;

            // Decrement countdown
            timers[i].countdown--;

            // Check if interval expired
            if (timers[i].countdown == 0) {
                // Call the callback function
                timers[i].callback();

                // Reset interval if repeat, else stop timer.
                if (timers[i].repeat) {
                    // Reset countdown for next interval
                    timers[i].countdown = timers[i].interval_ms;
                } else {
                    stop_timer(i);
                }
            }
            if (timers_found == active_timers) return;
        }
    }
}
