/*****************************************************************************
* University of Southern Denmark
* Embedded C Programming (ECP)
*
* MODULENAME.: global_variables.h
*
* PROJECT....:
*
* DESCRIPTION: Defines the elements of the task model..
*
* Change Log:
******************************************************************************
* Date    Id    Change
* YYMMDD
* --------------------
* 101004  MoH   Module created.
*
*****************************************************************************/

#pragma once

/***************************** Events *******************************/
// State ID's
#define SYSTEM_STATE            0
#define SYSTEM_MODE             1

#define NUMPAD_STATE            2
#define POTENTIOMETER_STATE     3

// State states
#define BUTTON_SINGLE_PRESS     0
#define BUTTON_DOUBBLE_PRESS    1
#define BUTTON_LONG_PRESS       2

#define SYSTEM_IDLE             3
#define SYSTEM_RUNNING          4

#define MODE_NUMPAD             5
#define MODE_POTENTIOMETER      6

// Event ID's
#define BUTTON_TIMEOUT          0



/***************************** Semaphores *******************************/
#define NUMPAD_SEMAPHORE    0

/***************************** QUEUEs *******************************/
#define NUMPAD_QUEUE        0

