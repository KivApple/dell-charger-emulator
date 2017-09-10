PROJECT=dell-charger-emulator
CFLAGS?=-O2 -ggdb
CFLAGS+=-mmcu=attiny85 -DF_CPU=8000000
SRC=$(wildcard *.c)

all: $(PROJECT).hex

$(PROJECT).hex: $(PROJECT).elf
	avr-objcopy -Oihex $< $@

$(PROJECT).elf: $(SRC) Makefile
	avr-gcc -o $@ $(CFLAGS) $(SRC)
	avr-size $(PROJECT).elf

clean:
	rm -rfv $(PROJECT).hex $(PROJECT).elf

