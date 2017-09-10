# dell-charger-emulator
Emulator of original Dell charger using ATTINY85

Power adapter for Dell laptops contains IC to determine adapter capabilities (watts, voltage, current).
If you connect an unoriginal adapter, the laptop refuses to charge the battery.
This project allows to use the cheap and small microcontroller ATTINY85 for emulating the answers
of the original adapter to the requests of the laptop.

You can configure adapter settings in the file eeprom_data.c. It contains the following string:

    DELL00AC045195023CN ... something like serial number ...

Here:

    045: 45 watts
    1950: 19.50 volts
    23: 2.3 amps

The description may not be entirely accurate. I'll be glad if you clarify.

**Warning: do not mask the weak power adapter to a more powerful one. This can lead to hardware damage.**

You need ATTINY25, ATTINY45 or ATTINY85 MCU (you may need to change compiler flags in Makefile) running at 8 MHz (the internal RC-oscillator is suitable, but if desired, you can use an external crystal - adjust the fuses accordingly). The Dell power adapter connector has three pins - GND, VOUT (19V) and ID. Connect the ID to the PB2 pin of the microcontroller. Also provide 3.3V power for MCU (you can use a simple linear regulator 78L33 to make the desired voltage from 19V).
