/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Timer.h
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
#define TIMER_LOAD_VALUE        80000                       // 1ms
#define TICK_TIME               5                           // Tick time in ms. (1 tick each 5ms)
#define MILLISEC(time_ms)       time_ms / TICK_TIME         // Converts ticks to ms
#define MAX_TIMERS              10                          // Maximum concurrent interval timers
#define INVALID_TIMER_ID        0xFF

/*****************************   Types   ***********************************/
typedef INT8U timer_id;                 // Timer ID for referencing created timers
typedef void (*timer_callback)(void);   // Timer callback function type - called when timer expires
typedef struct {
    INT32U interval_ms;           // Original interval
    INT32U countdown;             // Decrements each interrupt
    timer_callback callback;      // Function to call
    BOOLEAN active;                    // Is this timer active?
    BOOLEAN repeat;
} timer;

/*****************************   Variables   *******************************/
static volatile timer timers[MAX_TIMERS];    // Array of interval timers
static volatile INT8U active_timers;

/*****************************   Functions   *******************************/
/**
 * @brief Initialize Timer module
 *
 * Sets up Timer 0 and Timer 1 for 1ms interrupts running in background.
 * Call once during system initialization.
 *
 * @param None
 * @return None
 *
 * @note Must be called after system clock configuration
 */
extern void init_timer(void);


/**
 * @brief Start a repeating interval timer with callback
 *
 * Creates a background timer that calls a function every interval_ms.
 * Each call gets a unique timer, independent of others.
 *
 * @param interval_ms Time between callbacks in milliseconds (INT32U)
 * @param callback Function to call every interval (void (*)(void))
 * @return timer_id ID of created timer, or INVALID_TIMER_ID if failed
 *
 * @note Non-blocking - returns immediately
 * @note Callback runs inside interrupt handler - keep it short
 * @note Up to MAX_TIMERS can be active simultaneously
 * @note Each timer is completely independent
 *
 * @example
 *   // Call my_function() every 5 seconds
 *   timer_id id = add_repeating_timer(5000, my_function);
 *
 *   // Later, stop the timer if needed
 *   if (id != INVALID_TIMER_ID) {
 *       stop_timer(id);
 *   }
 */
extern timer_id start_repeating_timer(INT32U interval_ms, timer_callback callback);


/**
 * @brief Start a single execution timer with callback
 *
 * Creates a background timer that calls a function every interval_ms.
 * Each call gets a unique timer, independent of others.
 *
 * @param interval_ms Time between callbacks in milliseconds (INT32U)
 * @param callback Function to call every interval (void (*)(void))
 * @return timer_id ID of created timer, or INVALID_TIMER_ID if failed
 *
 * @note Non-blocking - returns immediately
 * @note Callback runs inside interrupt handler - keep it short
 * @note Up to MAX_TIMERS can be active simultaneously
 * @note Each timer is completely independent
 */
extern timer_id start_timer(INT32U interval_ms, timer_callback callback);


/**
 * @brief Add a interval timer with callback
 *
 * Creates a background timer that calls a function every interval_ms.
 * Each call gets a unique timer, independent of others.
 *
 * @param interval_ms Time between callbacks in milliseconds (INT32U)
 * @param callback Function to call every interval (void (*)(void))
 * @param repeat Bool to determine to repeat after execution.
 * @return timer_id ID of created timer, or INVALID_TIMER_ID if failed
 *
 * @note Non-blocking - returns immediately
 * @note Callback runs inside interrupt handler - keep it short
 * @note Up to MAX_TIMERS can be active simultaneously
 * @note Each timer is completely independent
 */
extern timer_id add_timer(INT32U interval_ms, timer_callback callback, BOOLEAN repeat);


extern timer_id update_timer(timer_id id, INT32U interval_ms, timer_callback callback);


/**
 * @brief Stop a running interval timer
 *
 * Stops and frees a timer previously created by set_timer().
 *
 * @param id Timer ID returned by set_timer()
 * @return bool true if successfully stopped, false if ID invalid
 *
 * @note Safe to call multiple times with same ID
 *
 * @example
 *   stop_timer(timer_id);
 */
extern bool stop_timer(timer_id id);


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
 * @note Current assignment: Timer 1 subtimer A interrupt
 */
extern void timer_handler(void);
