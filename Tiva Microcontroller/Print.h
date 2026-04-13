/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: Print.h
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
* 050128  KA    Module created.
*
*****************************************************************************/

#pragma once

/***************************** Include files *******************************/
#include <string.h>
#include <stdbool.h>
#include "global_variables.h"
#include "data_type.h"
#include "uart0.h"

/*****************************    Defines    *******************************/

/*****************************   Constants   *******************************/

/*****************************   Functions   *******************************/
extern void init_print(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Initialize uart0 communication
******************************************************************************/


/**
 * @brief Print functions
 *
 * Usage:
 *   print_msg("Hello");                // String
 *   print_var("2000");                 // Variable
 *   print_char(42);                    // Character
 *   print_msg_var("Value: ", 2000);    // String + Variable
 *   print_msg_char("Value: ", 42);     // String + Character
 */
extern void print_str(const char *msg);
/*****************************************************************************
*   Input    : String
*   Output   : -
*   Function : Print string to uart0
******************************************************************************/


extern void print_var(INT32U var);
/*****************************************************************************
*   Input    : Variable
*   Output   : -
*   Function : Print variable to uart0
******************************************************************************/


extern void print_char(char ch);
/*****************************************************************************
*   Input    : Variable
*   Output   : -
*   Function : Print char to uart0
******************************************************************************/


extern void print_str_var(const char *msg, INT32U var);
/*****************************************************************************
*   Input    : String, Variable
*   Output   : -
*   Function : Print sting and variable to uart0
******************************************************************************/


extern void print_str_char(const char *msg, char ch);
/*****************************************************************************
*   Input    : String, Variable
*   Output   : -
*   Function : Print sting and char to uart0
******************************************************************************/
