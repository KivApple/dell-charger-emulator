#pragma once

#include <stdint.h>
#include <avr/pgmspace.h>

#define EEPROM_DATA_LENGTH 128

extern const uint8_t ow_address[8] PROGMEM;
extern const uint8_t eeprom_data[EEPROM_DATA_LENGTH] PROGMEM;

