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
#define ENCODER_STATE           4

// State values
#define SYSTEM_IDLE             0
#define SYSTEM_RUNNING          1
#define MODE_NUMPAD             2
#define MODE_POTENTIOMETER      3
#define MODE_ENCODER            4

/***************************** Semaphores *******************************/
#define NUMPAD_SEMAPHORE    0
#define POTENTIOMETER_SEMAPHORE 1
#define ENCODER_SEMAPHORE   2

