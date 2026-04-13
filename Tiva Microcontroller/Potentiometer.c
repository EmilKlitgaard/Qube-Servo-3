/*****************************************************************************
* Odense University College of Enginerring
* Embedded C Programming (ECP)
*
* MODULENAME.: Potentiometer.c
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
#include "Potentiometer.h"

/*****************************    Defines    *******************************/
#define ADC_MAX_VALUE           4095        // 12-bit ADC
#define POT_ANGLE_MIN           -90
#define POT_ANGLE_MAX           90

/*****************************   Constants   *******************************/

/*****************************   Variables   *******************************/
volatile INT8U potentiometer_input;

/*****************************   Functions   *******************************/
void init_potentiometer(void) {
    // Enable the GPIO port B and ADC0 module in Run Mode
    SYSCTL_RCGC2_R |= SYSCTL_RCGC2_GPIOB;       // Enable GPIO Port B
    SYSCTL_RCGCADC_R |= 0x00000001;             // Enable ADC0

    // Do a dummy read to insert a few cycles after enabling the peripheral
    unsigned long dummy;
    dummy = SYSCTL_RCGC2_R;
    dummy = SYSCTL_RCGCADC_R;

    // Configure PB5 as an analog input (AIN11)
    GPIO_PORTB_AFSEL_R |= POT_GPIO_PIN;         // Enable alternate function on PB5
    GPIO_PORTB_DEN_R &= ~POT_GPIO_PIN;          // Disable digital function on PB5
    GPIO_PORTB_AMSEL_R |= POT_GPIO_PIN;         // Enable analog function on PB5

    // Configure ADC0 Sequencer 3 for single-ended sampling
    ADC0_ACTSS_R &= ~0x08;                      // Disable Sequencer 3 during configuration
    ADC0_EMUX_R &= ~0xF000;                     // Set Sequencer 3 for software trigger (bits 15:12 = 0)
    ADC0_SSMUX3_R = (ADC0_SSMUX3_R & 0xFFF0) | POT_AIN_CHANNEL;  // Select AIN11 (PB5) for first sample
    ADC0_SSCTL3_R = 0x06;                       // Set END bit (sample is last in sequence) and IE bit (interrupt enabled)
    ADC0_IM_R |= 0x08;                          // Enable interrupt for Sequencer 3
    
    // Set average sampling (2x oversampling)
    ADC0_SAC_R = 0x02;                          // Average 4 samples
    
    ADC0_ACTSS_R |= 0x08;                       // Enable Sequencer 3
    
    // Wait for ADC to be ready
    dummy = ADC0_ACTSS_R;
}


INT8U scan_potentiometer(void) {
    unsigned long timeout_count;
    INT16U adc_value;
    INT16S angle;
    
    // Clear any previous conversion result/flag
    ADC0_ISC_R |= 0x08;                         // Clear interrupt flag for SS3
    
    // Initiate ADC conversion on Sequencer 3
    ADC0_PSSI_R |= 0x08;                        // Processor Sample Sequence Initiate for SS3

    // Wait for conversion to complete (poll interrupt status)
    timeout_count = 50000;
    while (((ADC0_RIS_R & 0x08) == 0) && (timeout_count > 0)) {
        timeout_count--;
    }

    // Check if conversion completed or timed out
    if (timeout_count == 0 || (ADC0_RIS_R & 0x08) == 0) {
        ADC0_ISC_R |= 0x08;                     // Clear the flag
        return INVALID_POTENTIOMETER_INPUT;    // Timeout - conversion failed
    }

    // Read the ADC result from FIFO
    adc_value = ADC0_SSFIFO3_R & 0xFFF;         // Get 12-bit result

    // Clear interrupt flag
    ADC0_ISC_R |= 0x08;

    // Map ADC value (0-4095) to angle (-90 to 90 degrees)
    //angle = ((adc_value * 180) / ADC_MAX_VALUE) - 90;
    angle = (adc_value * 100) / ADC_MAX_VALUE;

    // Validate the result is in valid range
    /*if (angle < POT_ANGLE_MIN || angle > POT_ANGLE_MAX) {
        return INVALID_POTENTIOMETER_INPUT;
    }*/

    // Convert signed angle to unsigned (0-180 represents -90 to +90)
    return angle;
}
