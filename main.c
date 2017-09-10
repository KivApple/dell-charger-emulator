#include <stddef.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <util/delay.h>
#include "crc8.h"
#include "eeprom_data.h"

enum {
	OW_STATE_IDLE,
	OW_STATE_RESET,
	OW_STATE_PRESENCE,
	OW_STATE_RX,
	OW_STATE_TX
};

static struct {
	uint8_t state;
	uint8_t bit_state;
	uint8_t current_byte;
	uint8_t current_bit;
	uint8_t command;
	union {
		const uint8_t *tx_buffer;
		uint8_t *rx_buffer;
	};
	uint8_t buffer_size;
	uint8_t buffer_in_progmem;
	void (*callback)(void);
	uint8_t selected;
	uint8_t pull_low_next;
	uint8_t arg_buffer[8];
} ow = {
	.state = OW_STATE_IDLE,
	.bit_state = 1
};

#define OW_RELEASE() do { DDRB &= ~_BV(PB2); PORTB |= _BV(PB2); } while (0)
#define OW_PULL_LOW() do { PORTB &= ~_BV(PB2); DDRB |= _BV(PB2); } while (0)

static inline void ow_start_timer(void) {
	TCNT0 = 0;
#if F_CPU == 1000000
	TCCR0B = _BV(CS00);
#elif F_CPU == 8000000
	TCCR0B = _BV(CS01);
#else
#error F_CPU should be 1 MHz or 8 MHz
#endif
}

static inline void ow_rx(uint8_t *buffer, uint8_t count, void (*callback)(void)) {
	ow.state = OW_STATE_RX;
	ow.rx_buffer = buffer;
	ow.buffer_size = count;
	ow.callback = callback;
	ow.current_byte = 0;
	ow.current_bit = 0;
	buffer[0] = 0;
}

static inline void ow_tx(const uint8_t *buffer, uint8_t count, uint8_t in_progmem, void (*callback)(void)) {
	ow.state = OW_STATE_TX;
	ow.tx_buffer = buffer;
	ow.buffer_size = count;
	ow.buffer_in_progmem = in_progmem;
	ow.callback = callback;
	ow.current_byte = 0;
	ow.current_bit = 0;
	ow.pull_low_next = !((in_progmem ? pgm_read_byte(buffer) : buffer[0]) & 1);
}

static void ow_read_real_mem(void) {
	uint16_t offset = (((uint16_t) ow.arg_buffer[1]) << 8) | ow.arg_buffer[0];
	uint8_t max_len = EEPROM_DATA_LENGTH - offset;
	const uint8_t *base = eeprom_data + offset;
	ow_tx(base, max_len, 1, NULL);
}

static void ow_read_mem(void) {
	uint8_t tmp[] = { ow.command, ow.arg_buffer[0], ow.arg_buffer[1] };
	ow.arg_buffer[2] = Crc8(tmp, sizeof(tmp));
	ow_tx(ow.arg_buffer + 2, 1, 0, ow_read_real_mem);
}

static void ow_command_received(void) {
	switch (ow.command) {
		case 0x33: // READ ROM
			ow_tx(ow_address, 8, 1, NULL);
			break;
		case 0xCC: // SKIP ROM
			ow.selected = 1;
			ow_rx(&(ow.command), sizeof(ow.command), ow_command_received);
			break;
		case 0xF0: // READ MEM
			if (ow.selected) {
				ow_rx(ow.arg_buffer, 2, ow_read_mem);
			}
			break;
	}
}

static void ow_bit_change(uint8_t bit) {
	//bit ? (PORTB |= _BV(PB3)) : (PORTB &= ~_BV(PB3));
	switch (ow.state) {
		case OW_STATE_RESET:
			if (bit) {
				ow.state = OW_STATE_PRESENCE;
				OW_PULL_LOW();
				OCR0A = 200;
			}
			break;
		case OW_STATE_RX:
			if (!bit) {
				_delay_us(10);
				uint8_t *buffer = ow.rx_buffer;
				uint8_t cur_byte = ow.current_byte;
				uint8_t cur_bit = ow.current_bit;
				if (PINB & _BV(2)) {
					buffer[cur_byte] |= _BV(cur_bit);
				}
				cur_bit++;
				if (cur_bit == 8) {
					cur_byte++;
					cur_bit = 0;
					if (cur_byte == ow.buffer_size) {
						ow.state = OW_STATE_IDLE;
					}
				}
				ow.current_bit = cur_bit;
				ow.current_byte = cur_byte;
				if (ow.state == OW_STATE_IDLE) {
					if (ow.callback) {
						ow.callback();
					}
				}
			}
			break;
		case OW_STATE_TX:
			if (!bit) {
				_delay_us(30);
				OW_RELEASE();
				const uint8_t *buffer = ow.tx_buffer;
				uint8_t cur_byte = ow.current_byte;
				uint8_t cur_bit = ow.current_bit;
				cur_bit++;
				if (cur_bit == 8) {
					cur_byte++;
					cur_bit = 0;
				}
				if (cur_byte == ow.buffer_size) {
					ow.state = OW_STATE_IDLE;
				} else {
					ow.pull_low_next = !((ow.buffer_in_progmem ? pgm_read_byte(buffer + cur_byte) : buffer[cur_byte]) & _BV(cur_bit));
				}
				ow.current_byte = cur_byte;
				ow.current_bit = cur_bit;
				if (ow.state == OW_STATE_IDLE) {
					if (ow.callback) {
						ow.callback();
					}
				}
			}
			break;
	}
	if (!bit) {
		ow_start_timer();
	}
}

ISR(INT0_vect) {
	GIFR = _BV(INTF0);
	uint8_t bit = ow.bit_state;
	bit = !bit;
	if (!bit && ow.pull_low_next) {
		OW_PULL_LOW();
		ow.pull_low_next = 0;
	}
	ow_bit_change(bit);
	if (GIFR & _BV(INTF0)) {
		bit = !bit;
		ow_bit_change(bit);
	}
	uint8_t new_bit = (PINB & _BV(PB2)) ? 1 : 0;
	while (new_bit != bit) {
		bit = new_bit;
		ow_bit_change(bit);
		new_bit = (PINB & _BV(PB2)) ? 1 : 0;
	}
	ow.bit_state = bit;
}

ISR(TIMER0_OVF_vect) {
	TCCR0B = 0;
	TIFR = _BV(OCF0A);
	if (!ow.bit_state) {
		ow.state = OW_STATE_RESET;
		ow.selected = 0;
	}
}

ISR(TIMER0_COMPA_vect) {
	switch (ow.state) {
		case OW_STATE_PRESENCE:
			OW_RELEASE();
			ow_rx(&ow.command, sizeof(ow.command), ow_command_received);
			break;
	}
}

int main(void) {
	// Disable analog comparator
	ACSR |= _BV(ACD);
	// Disable ADC and TIM1
	PRR |= _BV(PRADC) | _BV(PRTIM1);
	// PB2: Input pullup
	OW_RELEASE();
	// TIM0: overflow and compare A interrupts
	TIMSK |= _BV(TOIE0) | _BV(OCIE0A);
	OCR0A = 0;
	// INT0: Any change
	MCUCR = (MCUCR | _BV(ISC00)) & ~_BV(ISC01);
	GIMSK |= _BV(INT0);
	// Enable interrupts
	sei();
	// Main loop
	set_sleep_mode(SLEEP_MODE_IDLE);
	while (1) {
		sleep_bod_disable();
		sleep_mode();
	}
}
