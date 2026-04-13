/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Sleep.h
*
* PROJECT....:
*
* DESCRIPTION: Timer module providing:
*              - Background millisecond ticker
*              - Non-blocking interval timers with callbacks
*              - Locally-blocking sleep_ms() function
*              - Up to 10 concurrent interval timers
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 260305  EK    Module created.
*
*****************************************************************************/

#pragma once

/***************************** Include files *******************************/
#include <stdint.h>
#include <stdbool.h>
#include "data_type.h"
#include "tm4c123gh6pm.h"

/*****************************   Defines   **********************************/
#define SLEEP_TIMER_LOAD_VALUE        80000                       // 1ms
#define SLEEP_TICK_TIME               5                           // Tick time in ms. (1 tick each 5ms)
#define SLEEP_MILLISEC(time_ms)       time_ms / SLEEP_TICK_TIME   // Converts ticks to ms

/*****************************   Types   ***********************************/

/*****************************   Variables   *******************************/
extern volatile INT64U tick_count;           // Global millisecond counter

/*****************************   Functions   *******************************/
/**
 * @brief Initialize Timer module
 *
 * Sets up Timer 0 for 1ms interrupts running in background.
 * Call once during system initialization.
 *
 * @param None
 * @return None
 *
 * @note Must be called after system clock configuration
 */
extern void init_sleep(void);


/**
 * @brief Sleep (blocking) for specified milliseconds
 *
 * Blocks current code execution for duration, but allows background
 * timers and interrupts to continue processing.
 *
 * @param ms Milliseconds to sleep (INT32U)
 * @return None
 *
 * @note This is locally blocking but globally non-blocking
 * @note Timer interrupts continue during sleep
 *
 * @example
 *   sleep_ms(1000);  // Sleep for 1 second
 */
extern void sleep_ms(INT64U ms);


/**
 * @brief Get current system tick count in milliseconds
 *
 * Returns the number of milliseconds since init_timer() was called.
 * Useful for manual timing measurements.
 *
 * @param None
 * @return INT32U Current tick count (milliseconds)
 *
 * @note Rolls over every ~49 days (INT32U)
 *
 * @example
 *   INT32U start = get_tick();
 *   // ... do something ...
 *   INT32U elapsed = get_tick() - start;
 */
extern INT64U get_tick(void);


/**
 * @brief Timer interrupt handler - call from startup vector table
 *
 * Manages all timer operations. Called automatically by hardware interrupt.
 *
 * @param None
 * @return None
 *
 * @note DO NOT call manually
 * @note Must be assigned in tm4c123gh6pm_startup_ccs.c vector table
 * @note Current assignment: Timer 0 subtimer A interrupt
 */
extern void sleep_timer_handler(void);
