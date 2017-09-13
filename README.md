# dell-charger-emulator
Emulator of original Dell charger using ATTINY85

Power adapter for Dell laptops contains IC to determine adapter capabilities (watts, voltage, current).
If you connect an unoriginal adapter, the laptop refuses to charge the battery.
This project allows to use the cheap and small microcontroller ATTINY85 for emulating the answers
of the original adapter to the requests of the laptop.

You can configure adapter settings in the file eeprom-data.hex. This file contains EEPROM data in Intel Hex format.
Format of Dell charger identification shown below:

| Offset | Length | Content                 | Description              |
|--------|--------|-------------------------|--------------------------|
|      0 |      4 | DELL                    | Manufacturer identifier  |
|      4 |      4 | 00AC                    | Adapter type             |
|      8 |      3 | 045                     | Watts (45W)              |
|     11 |      3 | 195                     | Tenths of a volt (19.5V) |
|     14 |      3 | 023                     | Tenths of amps (2.3A)    |
|     17 |     23 | CN0CDF577243865Q27F2A05 | Serial number            |
|     40 |      2 | 0x3D 0x94               | CRC-16/ARC (LSB first)   |

The description may not be entirely accurate. I'll be glad if you clarify.

You can use Python utility dell-charger-data-editor.py to easily change this values.

You must flash the EEPROM data together with the program code. Later you can only re-write EEPROM.

**Warning: do not mask the weak power adapter to a more powerful one. This can lead to hardware damage.**

You need ATTINY25, ATTINY45 or ATTINY85 MCU (you may need to change compiler flags in Makefile) running at 8 MHz (the internal RC-oscillator is suitable, but if desired, you can use an external crystal - adjust the fuses accordingly). The Dell power adapter connector has three pins - GND, VOUT (19V) and ID. Connect the ID to the PB2 pin of the microcontroller. Also provide 3.3V power for MCU (you can use a simple linear regulator 78L33 to make the desired voltage from 19V).

## Reading and writing EEPROM

You can read and write EEPROM using dell-charger-data-editor.py (see console menu of this utility).

You need connect OneWire bus to any USB-UART adapter using simple schematic with diode:

    TXD --------|<|----*-------- ID
                       |
    RXD ----------------

    GND ------------------------ GND

**Warning: USB-UART adapter should use 3.3V or 5V logic levels. 12V levels will damage EEPROM IC.**

You can read by this utility both original EEPROM and emulated by AVR. You can write only emulated EEPROM.
