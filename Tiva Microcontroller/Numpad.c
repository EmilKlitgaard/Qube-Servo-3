/*****************************************************************************
* Odense University College of Enginerring
* Embedded C Programming (ECP)
*
* MODULENAME.: Numpad.c
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
#include "Numpad.h"

/*****************************    Defines    *******************************/
/*****************************   Constants   *******************************/
static const INT8U keymap[NUMPAD_ROWS][NUMPAD_COLS] = {
    {1,  2,  3},      // Row 0 (K): 1, 2, 3
    {4,  5,  6},      // Row 1 (J): 4, 5, 6
    {7,  8,  9},      // Row 2 (H): 7, 8, 9
    {10, 11, 12}      // Row 3 (G): *, 0, #
};

/*****************************   Variables   *******************************/
/*****************************   Functions   *******************************/
void init_numpad(void) {
    // Enable the GPIO port A and E, that is used for the external numpad.
    SYSCTL_RCGC2_R |= SYSCTL_RCGC2_GPIOA;
    SYSCTL_RCGC2_R |= SYSCTL_RCGC2_GPIOE;

    // Do a dummy read to insert a few cycles after enabling the peripheral.
    int dummy;
    dummy = SYSCTL_RCGC2_R;

    // Configure COLUMNS (PA2, PA3, PA4) as INPUTS with pull-downs
    GPIO_PORTA_DIR_R &= ~COL_MASK;      // Input
    GPIO_PORTA_DEN_R |= COL_MASK;       // Digital enable
    GPIO_PORTA_PUR_R |= COL_MASK;       // Enable Pull-up resistor

    // Configure ROWS (PE0, PE1, PE2, PE3) as OUTPUTS
    GPIO_PORTE_DIR_R |= ROW_MASK;       // Output
    GPIO_PORTE_DEN_R |= ROW_MASK;       // Digital enable
    GPIO_PORTE_DATA_R &= ~ROW_MASK;     // Start with all rows LOW
}


INT8U scan_numpad(void) {
    // Determine which column is pressed
    INT8U col = 0xFF;
    INT8U col_pins[NUMPAD_COLS] = {PA4, PA3, PA2};
    
    if (!(GPIO_PORTA_DATA_R & PA4))         col = 0;  // Col0 (F)
    else if (!(GPIO_PORTA_DATA_R & PA3))    col = 1;  // Col1 (E)
    else if (!(GPIO_PORTA_DATA_R & PA2))    col = 2;  // Col2 (D)
    else {
        sleep_ms(NUMPAD_DEBOUNCE_MS);   // Debounce delay
        return 0;                       // Nothing pressed
    }

    // Determine which row is pressed
    INT8U row;
    INT8U row_pins[NUMPAD_ROWS] = {PE3, PE2, PE1, PE0};
    for (row=0; row<NUMPAD_ROWS; row++) {
        // Drive the row HIGH, all others LOW
        GPIO_PORTE_DATA_R = row_pins[row];

        // Check if the column is HIGH (meaning button is pressed on this row)
        if (GPIO_PORTA_DATA_R & col_pins[col]) {
            // Turn off all rows
            GPIO_PORTE_DATA_R &= ~ROW_MASK;

            // Verify that the button is still pressed for redundancy
            if (GPIO_PORTA_DATA_R & col_pins[col]) return INVALID_NUMPAD_INPUT;

            // Key press detected
            sleep_ms(NUMPAD_DEBOUNCE_MS);   // Debounce delay
            return keymap[row][col];        // Return key from matrix
        }
    }

    GPIO_PORTE_DATA_R &= ~ROW_MASK;     // Turn off all rows
    return INVALID_NUMPAD_INPUT;
}


/*****************************   Numpad Task   *****************************/
void numpad_task(void *pvParameters) {
    INT8U input;
    INT8U last_input = INVALID_NUMPAD_INPUT;
    INT8U system_state;
    INT8U system_mode;

    while (true) {
        system_state = read_state(SYSTEM_STATE);
        
        if (system_state == SYSTEM_RUNNING) {
            system_mode = read_state(SYSTEM_MODE);
            
            if (system_mode == MODE_NUMPAD) {
                input = scan_numpad();
                
                if ((input != INVALID_NUMPAD_INPUT) && (input != last_input)) {
                    last_input = input;
                    set_state(NUMPAD_STATE, input);
                    print_var(input);
                }
            } else {
                // Not in numpad mode, reset last input
                last_input = INVALID_NUMPAD_INPUT;
            }
        }
        
        // Scan every 50ms when in numpad mode, less frequently otherwise
        sleep_ms(NUMPAD_SCAN_MS);
    }
}
