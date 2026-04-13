/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Print.c
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
* 080219  MoH    Module created.
*
*****************************************************************************/

/***************************** Include files *******************************/
#include "Print.h"


/*****************************   Functions   *******************************/
void init_print(void) {
    const INT32U baud_rate = 230400;
    const INT32U databits = 8;
    const INT32U stopbits = 1;
    const INT32U parity = 0;
    uart0_init(baud_rate, databits, stopbits, parity);
}


void print_str(const char *msg) {
    while (*msg) {
        while (!uart0_tx_rdy());
        uart0_putc((INT32U)*msg++);
    }
    while (!uart0_tx_rdy());
    uart0_putc('\n');
}


void print_var(INT32U var) {
    char buffer[255];
    INT32U length = 0;
    INT32U temp = var;

    if (temp == 0) {
        buffer[0] = '0';
        length = 1;
    } else {
        INT32U digits = 0;
        while (temp > 0) {
            temp /= 10;
            digits++;
        }
        length = digits;
        temp = var;
        while (temp > 0) {
            buffer[digits - 1] = '0' + (temp % 10);
            temp /= 10;
            digits--;
        }
    }

    INT32U i;
    for (i = 0; i < length; i++) {
        while (!uart0_tx_rdy());
        uart0_putc((INT32U)buffer[i]);
    }
    while (!uart0_tx_rdy());
    uart0_putc('\n');
}


void print_char(char ch) {
    char buffer[255];
    INT32U length = 0;
    INT32U temp = ch;

    if (temp == 0) {
        buffer[0] = '0';
        length = 1;
    } else {
        INT32U digits = 0;
        while (temp > 0) {
            temp /= 10;
            digits++;
        }
        length = digits;
        temp = ch;
        while (temp > 0) {
            buffer[digits - 1] = '0' + (temp % 10);
            temp /= 10;
            digits--;
        }
    }

    INT32U i;
    for (i = 0; i < length; i++) {
        while (!uart0_tx_rdy());
        uart0_putc((INT32U)buffer[i]);
    }
    while (!uart0_tx_rdy());
    uart0_putc('\n');
}



void print_str_var(const char *msg, INT32U var) {
    while (*msg) {
        while (!uart0_tx_rdy());
        uart0_putc((INT32U)*msg++);
    }
    print_var(var);
}



void print_str_char(const char *msg, char ch) {
    while (*msg) {
        while (!uart0_tx_rdy());
        uart0_putc((INT32U)*msg++);
    }
    print_char(ch);
}
