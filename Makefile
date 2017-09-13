PROJECT=dell-charger-emulator
GCC_MCU?=attiny85
AVRDUDE_MCU?=t85

CFLAGS?=-O2 -ggdb
CFLAGS+=-mmcu=$(GCC_MCU) -DF_CPU=8000000

AVRDUDE_FLAGS?=-c buspirate -P /dev/ttyUSB0
AVRDUDE_FLAGS+=-p $(AVRDUDE_MCU)

FUSES?=-U lfuse:w:0xd2:m -U hfuse:w:0xd7:m -U efuse:w:0xff:m

SRC=$(wildcard *.c)

all: $(PROJECT).hex

$(PROJECT).hex: $(PROJECT).elf
	avr-objcopy -Oihex $< $@

$(PROJECT).elf: $(SRC) Makefile
	avr-gcc -o $@ $(CFLAGS) $(SRC)
	avr-size $(PROJECT).elf

clean:
	rm -rfv $(PROJECT).hex $(PROJECT).elf

load: load_rom load_eeprom

load_rom: $(PROJECT).hex
	avrdude $(AVRDUDE_FLAGS) -U flash:w:$<

load_eeprom: eeprom-data.hex
	avrdude $(AVRDUDE_FLAGS) -U eeprom:w:$<

fuses:
	avrdude $(AVRDUDE_FLAGS) $(FUSES)
