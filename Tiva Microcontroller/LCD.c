/****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: LCD.c
*
* PROJECT....:
*
* DESCRIPTION: HD44780U LCD lcd driver (4-bit mode)
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 260422  Copilot  Module created.
*
*****************************************************************************/

/***************************** Include files *******************************/
#include "LCD.h"

/*****************************    Defines    *******************************/
#define LCD_DATA_MASK       (LCD_D4_PIN | LCD_D5_PIN | LCD_D6_PIN | LCD_D7_PIN)
#define LCD_CONTROL_MASK    (LCD_RS_PIN | LCD_E_PIN)

/*****************************   Functions   *******************************/
static void lcd_wait_short(void) {
    volatile INT16U i;
    for (i = 0; i < 1000; i++) {
    }
}


static void lcd_wait_ms(INT32U ms) {
    volatile INT16U i;
    while (ms > 0) {
        for (i=0; i<5000; i++) {}
        ms--;
    }
}


static void wr_ctrl_lcd_low(INT8U ch) {
    INT8U temp;

    temp = GPIO_PORTC_DATA_R & 0x0F;
    temp = temp | ((ch & 0x0F) << 4);
    GPIO_PORTC_DATA_R = temp;

    lcd_wait_short();
    GPIO_PORTD_DATA_R &= (INT8U)~LCD_RS_PIN;   // Control mode
    lcd_wait_short();
    GPIO_PORTD_DATA_R |= LCD_E_PIN;            // E high
    lcd_wait_short();
    GPIO_PORTD_DATA_R &= (INT8U)~LCD_E_PIN;    // E low
    lcd_wait_short();
}


static void wr_ctrl_lcd_high(INT8U ch) {
    wr_ctrl_lcd_low((ch & 0xF0) >> 4);
}


static void out_lcd_low(INT8U ch) {
    INT8U temp;

    temp = GPIO_PORTC_DATA_R & 0x0F;
    GPIO_PORTC_DATA_R = temp | ((ch & 0x0F) << 4);

    GPIO_PORTD_DATA_R |= LCD_RS_PIN;           // Data mode
    GPIO_PORTD_DATA_R |= LCD_E_PIN;            // E high
    GPIO_PORTD_DATA_R &= (INT8U)~LCD_E_PIN;    // E low
}


static void out_lcd_high(INT8U ch) {
    out_lcd_low((ch & 0xF0) >> 4);
}


static void wr_ctrl_lcd(INT8U ch) {
    static INT8U mode_4bit = 0;
    INT16U i;

    wr_ctrl_lcd_high(ch);
    if (mode_4bit) {
        for (i = 0; i < 1000; i++) {
        }
        wr_ctrl_lcd_low(ch);
    } else {
        if ((ch & 0x30) == 0x20) {
            mode_4bit = 1;
        }
    }
}


static void out_lcd(INT8U ch) {
    INT16U i;

    out_lcd_high(ch);
    for (i = 0; i < 1000; i++) {
    }
    out_lcd_low(ch);
}


void lcd_command(INT8U cmd) {
    wr_ctrl_lcd(cmd);

    if ((cmd == 0x01) || (cmd == 0x02)) {
        lcd_wait_ms(2);
    } else {
        lcd_wait_short();
    }
}


void clear_lcd(void) {
    wr_ctrl_lcd(0x01);
}


void write_char(char ch) {
    out_lcd((INT8U)ch);
    lcd_wait_short();
}


void write_str(const char *str) {
    while ((str != 0) && (*str != '\0')) {
        write_char(*str);
        str++;
    }
}


void set_cursor(INT8U x, INT8U y) {
    INT8U pos;

    if (x > 15) {
        x = 15;
    }
    if (y > 1) {
        y = 1;
    }

    pos = y * 0x40 + x;
    pos |= 0x80;
    wr_ctrl_lcd(pos);
}


void write_str_at(INT8U x, INT8U y, const char *str) {
    set_cursor(x, y);
    write_str(str);
}


void init_lcd(void) {
    // Enable clock for Port C (data) and Port D (control)
    SYSCTL_RCGC2_R |= (SYSCTL_RCGC2_GPIOC | SYSCTL_RCGC2_GPIOD);

    // Wait until both peripherals are ready
    while ((SYSCTL_PRGPIO_R & (SYSCTL_PRGPIO_R2 | SYSCTL_PRGPIO_R3)) != (SYSCTL_PRGPIO_R2 | SYSCTL_PRGPIO_R3)) {}

    // Unlock and commit LCD pins
    GPIO_PORTC_LOCK_R = GPIO_LOCK_KEY;
    GPIO_PORTC_CR_R |= LCD_DATA_MASK;
    GPIO_PORTD_LOCK_R = GPIO_LOCK_KEY;
    GPIO_PORTD_CR_R |= LCD_CONTROL_MASK;

    // Configure Port C upper nibble for LCD data
    GPIO_PORTC_AFSEL_R &= ~LCD_DATA_MASK;
    GPIO_PORTC_PCTL_R &= ~0xFFFF0000;
    GPIO_PORTC_AMSEL_R &= ~LCD_DATA_MASK;
    GPIO_PORTC_DIR_R |= LCD_DATA_MASK;
    GPIO_PORTC_DEN_R |= LCD_DATA_MASK;

    // Configure Port D control pins for RS and E
    GPIO_PORTD_AFSEL_R &= ~LCD_CONTROL_MASK;
    GPIO_PORTD_PCTL_R &= ~0x0000FF00;
    GPIO_PORTD_AMSEL_R &= ~LCD_CONTROL_MASK;
    GPIO_PORTD_DIR_R |= LCD_CONTROL_MASK;
    GPIO_PORTD_DEN_R |= LCD_CONTROL_MASK;

    // Known idle output state
    GPIO_PORTC_DATA_R &= ~LCD_DATA_MASK;
    GPIO_PORTD_DATA_R &= ~LCD_CONTROL_MASK;

    // Init sequence
    lcd_wait_ms(40);
    wr_ctrl_lcd(0x30);
    lcd_wait_ms(5);
    wr_ctrl_lcd(0x30);
    lcd_wait_short();
    wr_ctrl_lcd(0x30);
    lcd_wait_short();
    wr_ctrl_lcd(0x20);   // Set 4-bit mode
    lcd_wait_short();
    wr_ctrl_lcd(0x28);   // 2 line lcd
    wr_ctrl_lcd(0x0C);   // LCD on, cursor off
    wr_ctrl_lcd(0x06);   // Cursor increment
    wr_ctrl_lcd(0x01);   // Clear
    wr_ctrl_lcd(0x02);   // Home
}

void lcd_task(void) {
    init_lcd();
    clear_lcd();

    INT8U system_state;
    INT8U last_system_state = 0xFF;
    INT8U system_mode;
    INT8U last_system_mode = 0xFF;

    while (true) {
        system_state = read_state(SYSTEM_STATE);
        
        if (system_state == SYSTEM_RUNNING) {
            system_mode = read_state(SYSTEM_MODE);

            if (system_mode == MODE_NUMPAD && last_system_mode != MODE_NUMPAD) {
                clear_lcd();
                write_str_at(0, 0, "System Running!");
                write_str_at(0, 1, "Numpad Mode");
                last_system_mode = system_mode;
            } else if (system_mode == MODE_POTENTIOMETER && last_system_mode != MODE_POTENTIOMETER) {
                clear_lcd();
                write_str_at(0, 0, "System Running!");
                write_str_at(0, 1, "Pot Mode");
                last_system_mode = system_mode;
            } else if (system_mode == MODE_ENCODER && last_system_mode != MODE_ENCODER) {
                clear_lcd();
                write_str_at(0, 0, "System Running!");
                write_str_at(0, 1, "Encoder Mode");
                last_system_mode = system_mode;
            }
            last_system_state = system_state;

        } else if (system_state == SYSTEM_IDLE && last_system_state != SYSTEM_IDLE) {
            clear_lcd();
            write_str_at(0, 0, "System Idle...");
            last_system_state = system_state;
            last_system_mode = 0xFF;
        }
    }
}