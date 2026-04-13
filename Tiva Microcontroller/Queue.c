/*****************************************************************************
* Odense University College of Enginerring
* Embedded C Programming (ECP)
*
* MODULENAME.: Queue.c
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
#include "Queue.h"

/*****************************    Defines    *******************************/

/*****************************   Constants   *******************************/

/*****************************   Variables   *******************************/

/*****************************   Functions   *******************************/
void init_queue(void) {
    INT8U i;
    for (i=0; i<MAX_QUEUES; i++) {
        queues[i].active = false;
        queues[i].head = 0;
        queues[i].tail = 0;
        queues[i].len  = 0;
    }
}


INT8S open_queue(INT8U id) {
    if (id < MAX_QUEUES && !queues[id].active) {
        queues[id].active = true;
        return id;  // Return queue ID
    }

    // No free timers available
    return INVALID_QUEUE_ID;
}


INT8U put_queue(INT8U id, INT8U ch) {
    if (id < MAX_QUEUES && queues[id].active) {
        if (queues[id].len < QUEUE_SIZE) {
            queues[id].buf[queues[id].head++] = ch;
            queues[id].head &= 0x7F;
            queues[id].len++;
            return (true);
        }
    }
    return (false);
}


INT8U get_queue(INT8U id) {
    INT8U ch = '\0';
    if (id < MAX_QUEUES && queues[id].active) {
        if (queues[id].len) {
            ch = queues[id].buf[queues[id].tail++];
            queues[id].tail &= 0x7F;
            queues[id].len--;
        }
    }
    return (ch);
}





