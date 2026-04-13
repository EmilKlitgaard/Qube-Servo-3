/****************************   Include files   ******************************/
#include <stdint.h>
#include <stdbool.h>

#include "global_variables.h"
#include "tm4c123gh6pm.h"
#include "data_type.h"
#include "uart0.h"

#include "GPIO.h"
#include "Numpad.h"
#include "Potentiometer.h"
#include "Print.h"
#include "Events.h"
#include "Queue.h"
#include "Sleep.h"
#include "Timer.h"
#include "Button.h"

/*****************************   Functions   *******************************/
void led_callback(void) {
    toggle_led(BLUE);
}


void controller_loop(void) {
    // Define variables
    INT8U system_state;
    INT8U system_mode;
    INT8U input;
    INT8U last_input;

    // Set startup states
    set_state(SYSTEM_STATE, SYSTEM_IDLE);
    set_state(SYSTEM_MODE, MODE_NUMPAD);
    set_led(RED); // Idle on startup

    // Main loop
    while (true) {
        // Get system state
        system_state = read_state(SYSTEM_STATE);

        if (system_state == SYSTEM_RUNNING) {
            // Get system mode
            system_mode = read_state(SYSTEM_MODE);

            switch (system_mode) {
                case MODE_NUMPAD:
                    set_led(GREEN);
                    //event = read_state(NUMPAD_STATE);
                    input = scan_numpad();
                    if ((input != INVALID_NUMPAD_INPUT) && (input != last_input)) {
                        last_input = input;
                        print_var(input);
                    }
                    break;

                case MODE_POTENTIOMETER:
                    set_led(BLUE);
                    //input = read_state(POTENTIOMETER_STATE);
                    input = scan_potentiometer();
                    if ((input != INVALID_POTENTIOMETER_INPUT) && (input != last_input)) {
                        last_input = input;
                        print_var(input);
                    }
                    sleep_ms(100); // Congestion control: Delay for not overflowing receiver.
                    break;
            }
        } else {
            // Indicate idle
            toggle_led(RED);
            print_var(0);
            sleep_ms(100);
        }
    }
}


int main(void) {
    // Initialize
    init_gpio();
    init_numpad();
    init_potentiometer();
    init_print();
    init_queue();
    init_sleep();
    init_timer();
    init_button_handler();

    // Startup
    print_str("STARTING...\n");
    blink_led(WHITE);
    set_led(WHITE);

    // Setup timers
    //start_repeating_timer(1000, led_callback);

    // Loop forever.
    controller_loop();
}
