/*****************************************************************************
* Odense University College of Enginerring
* Embedded C Programming (ECP)
*
* MODULENAME.: Queue.h
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
#include <stdbool.h>
#include "data_type.h"

/*****************************    Defines    *******************************/
#define MAX_QUEUES          10
#define QUEUE_SIZE          128
#define INVALID_QUEUE_ID    -1

/*****************************   Types   ***********************************/
typedef struct {
    INT8U   active;
    INT8U   head;
    INT8U   tail;
    INT8U   len;
    INT8U   buf[QUEUE_SIZE];
} queue_struct;

/*****************************   Constants   *******************************/
queue_struct queues[MAX_QUEUES];

/*****************************   Functions   *******************************/
extern void init_queue(void);
/*****************************************************************************
*   Input    : -
*   Output   : -
*   Function : Initialize all queues.
******************************************************************************/


extern INT8S open_queue(INT8U);
/*****************************************************************************
*   Input    : -
*   Output   : id
*   Function : Open a new queue and return its id. If no queue avaiable return INVALID_QUEUE_ID.
******************************************************************************/


extern INT8U put_queue(INT8U, INT8U);
/*****************************************************************************
*   Input    : id
*   Output   : id
*   Function : Add
******************************************************************************/


extern INT8U get_queue(INT8U);
/*****************************************************************************
*   Input    : id
*   Output   : id
*   Function : Read a event and reset
******************************************************************************/
