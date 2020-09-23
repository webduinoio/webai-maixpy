#ifndef __HCSR04_H
#define __HCSR04_H

#include "stdint.h"

/**
 * @param gpio: gpio resource, not pin
 * @attention register fpioa first
 * @return -1: param error
 *          0: timeout
 *         >0: distance
 */
long hcsr04_measure_cm(uint8_t trig,uint8_t echo, uint32_t timeout_us);
long hcsr04_measure_inch(uint8_t trig,uint8_t echo, uint32_t timeout_us);


#endif

