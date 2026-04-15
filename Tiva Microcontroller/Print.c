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

/*****************************   UART Helper Functions   *****************************/

/**
 * Helper: Calculate line control data bits
 */
static INT32U lcrh_databits(INT8U antal_databits) {
    if ((antal_databits < 5) || (antal_databits > 8))
        antal_databits = 8;
    return ((INT32U)antal_databits - 5) << 5;  // Control bit 5-6, WLEN
}

/**
 * Helper: Calculate line control stop bits
 */
static INT32U lcrh_stopbits(INT8U antal_stopbits) {
    if (antal_stopbits == 2)
        return 0x00000008;      // return bit 3 = 1
    else
        return 0x00000000;      // return all zeros
}

/**
 * Helper: Calculate line control parity
 */
static INT32U lcrh_parity(INT8U parity) {
    INT32U result;
    switch (parity) {
        case 'e':
            result = 0x00000006;
            break;
        case 'o':
            result = 0x00000002;
            break;
        case '0':
            result = 0x00000086;
            break;
        case '1':
            result = 0x00000082;
            break;
        case 'n':
        default:
            result = 0x00000000;
    }
    return result;
}

/**
 * Enable UART0 FIFOs
 */
static void uart0_fifos_enable(void) {
    UART0_LCRH_R |= 0x00000010;
}

/**
 * Disable UART0 FIFOs
 */
static void uart0_fifos_disable(void) {
    UART0_LCRH_R &= 0xFFFFFFEF;
}

/**
 * Check if character ready at UART0 RX
 */
static BOOLEAN uart0_rx_rdy(void) {
    return (UART0_FR_R & UART_FR_RXFF);
}

/**
 * Get character from UART0 RX
 */
static INT8U uart0_getc(void) {
    return (UART0_DR_R);
}

/**
 * Check if UART0 TX is ready
 */
static BOOLEAN uart0_tx_rdy(void) {
    return (UART0_FR_R & UART_FR_TXFE);
}

/**
 * Put character to UART0 TX
 */
static void uart0_putc(INT8U ch) {
    UART0_DR_R = ch;
}

/**
 * Initialize UART0 with specified parameters
 */
static void uart0_init(INT32U baud_rate, INT8U databits, INT8U stopbits, INT8U parity) {
    INT32U BRD;

    // Enable clock for Port A
    SYSCTL_RCGC2_R |= SYSCTL_RCGC2_GPIOA;

    // Enable clock for UART 0
    SYSCTL_RCGC1_R |= SYSCTL_RCGC1_UART0;

    // Set PA0 and PA1 to alternate function (uart0)
    GPIO_PORTA_AFSEL_R |= 0x00000003;
    GPIO_PORTA_DIR_R |= 0x00000002;      // PA1 (uart0 tx) to output
    GPIO_PORTA_DIR_R &= 0xFFFFFFFE;      // PA0 (uart0 rx) to input
    GPIO_PORTA_DEN_R |= 0x00000003;      // Enable digital operation of PA0 and PA1

    // Configure baud rate: BRD = X-sys*64/(16*baudrate) = 16M*4/baudrate
    BRD = 64000000 / baud_rate;
    UART0_IBRD_R = BRD / 64;
    UART0_FBRD_R = BRD & 0x0000003F;

    // Configure line control
    UART0_LCRH_R = lcrh_databits(databits);
    UART0_LCRH_R += lcrh_stopbits(stopbits);
    UART0_LCRH_R += lcrh_parity(parity);

    uart0_fifos_disable();

    // Enable UART
    UART0_CTL_R |= (UART_CTL_UARTEN | UART_CTL_TXE);
}

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
