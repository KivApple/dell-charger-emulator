PROJECT=dell-charger-emulator
CFLAGS?=-O2 -ggdb
CFLAGS+=-mmcu=attiny85 -DF_CPU=8000000
FUSES=-U lfuse:w:0xd2:m -U hfuse:w:0xd7:m -U efuse:w:0xff:m
SRC=$(wildcard *.c)

all: $(PROJECT).hex

$(PROJECT).hex: $(PROJECT).elf
	avr-objcopy -Oihex $< $@

$(PROJECT).elf: $(SRC) Makefile
	avr-gcc -o $@ $(CFLAGS) $(SRC)
	avr-size $(PROJECT).elf

clean:
	rm -rfv $(PROJECT).hex $(PROJECT).elf

load: $(PROJECT).hex
	avrdude -c buspirate -P /dev/ttyUSB0 -p t85 -U flash:w:$<

fuses:
	avrdude -c buspirate -P /dev/ttyUSB0 -p t85 $(FUSES)

