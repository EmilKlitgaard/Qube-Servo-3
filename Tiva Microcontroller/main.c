/****************************   FREERTOS RTOS VERSION   ****************************/
/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: main.c (FreeRTOS version)
*
* PROJECT....: Tiva Microcontroller with FreeRTOS
*
* DESCRIPTION: Main application with FreeRTOS task scheduler
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 260415  User  Complete FreeRTOS conversion
*
*****************************************************************************/

/***************************** Include files *******************************/
#include <stdint.h>
#include <stdbool.h>

#include "tm4c123gh6pm.h"
#include "data_type.h"

// FreeRTOS includes
#include <FreeRTOS.h>
#include <task.h>
#include "systick_frt.h"

// Hardware modules
#include "GPIO.h"
#include "Print.h"
#include "Sleep.h"

// Application includes
#include "Button.h"
#include "Numpad.h"
#include "Potentiometer.h"
#include "Encoder.h"
#include "StateManager.h"
#include "LedManager.h"

/*****************************    Defines    *******************************/
#define USERTASK_STACK_SIZE     configMINIMAL_STACK_SIZE
#define IDLE_PRIO               0
#define LOW_PRIO                1
#define MED_PRIO                2
#define HIGH_PRIO               3

/*****************************   Functions   *****************************/
static void init_hardware(void) {
    // Initialize system clock and SysTick for FreeRTOS
    init_systick();
    
    // Initialize GPIO (LEDs and buttons)
    init_gpio();
    
    // Initialize UART for printing
    init_print();
    
    // Initialize hardware modules
    init_numpad();
    init_potentiometer();
    init_encoder();
    init_button_handler();
    
    // Initialize state manager
    init_state_manager();
}


int main(void) {
    // Setup all hardware
    init_hardware();
    
    // Print startup message
    print_str("\n===== SYSTEM STARTING =====\n");

    // Create FreeRTOS Tasks:
    print_str("Creating tasks...");
    xTaskCreate(button_task, "Button", USERTASK_STACK_SIZE, NULL, HIGH_PRIO, NULL);                     // Button task - handles button presses and state changes   
    xTaskCreate(led_manager_task, "LED_Manager", USERTASK_STACK_SIZE, NULL, LOW_PRIO, NULL);            // LED Manager task - handles status blinking and mode color indication
    xTaskCreate(numpad_task, "Numpad", USERTASK_STACK_SIZE * 2, NULL, MED_PRIO, NULL);                  // Numpad input task - scan and process numpad
    xTaskCreate(potentiometer_task, "Potentiometer", USERTASK_STACK_SIZE * 2, NULL, MED_PRIO, NULL);    // Potentiometer input task - read and process potentiometer
    xTaskCreate(encoder_task, "Encoder", USERTASK_STACK_SIZE * 2, NULL, MED_PRIO, NULL);                // Encoder input task - read and process encoder
    // Start the FreeRTOS scheduler
    print_str("Starting scheduler...\n");
    vTaskStartScheduler();

    return 0;
}
