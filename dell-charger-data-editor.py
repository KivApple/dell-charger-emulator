#!/usr/bin/env python 
import sys, math

if len(sys.argv) >= 2:
	filename = sys.argv[1]
else:
	filename = 'eeprom-data.hex'

EEPROM_SIZE = 128
try:
	with open(filename) as f:
		data = [0xFF] * EEPROM_SIZE
		for l in f:
			if l[0] != ':':
				raise Exception('Invalid input file format')
			length = int(l[1:1 + 2], 16)
			offset = int(l[3:3 + 4], 16)
			t = int(l[7:7 + 2], 16)			
			if t == 1:
				break
			elif t == 0:
				i = 0
				while i < length:
					j = 9 + i * 2
					byte = int(l[j:j + 2], 16)
					data[offset + i] = byte
					i += 1
except Exception as e:
	print('Warning: %s' % str(e))
	data = [ord(char) for char in 'DELL00AC045195023CN0CDF577243865Q27F2A05'] + [0x3D, 0x94] + [0xFF] * (EEPROM_SIZE - 42)

def get_manufacturer():
	try:
		return ''.join([chr(code if (((code >= ord('0')) and (code <= ord('9'))) or ((code >= ord('A')) and (code <= ord('Z')))) else None) for code in data[0:4]])
	except:
		print('Warning: invalid manufacturer')
		return '????'

def get_adapter_type():
	try:
		return ''.join([chr(code if (((code >= ord('0')) and (code <= ord('9'))) or ((code >= ord('A')) and (code <= ord('Z')))) else None) for code in data[4:8]])
	except:
		print('Warning: invalid adapter type')
		return '????'

def get_watts():
	try:
		return int(''.join(chr(code) for code in data[8:8 + 3]))
	except:
		print('Warning: invalid wattage value')
		return 0

def get_volts():
	try:
		return int(''.join([chr(code) for code in data[11:11 + 3]])) / 10
	except:
		print('Warning: invalid voltage value')
		return 0

def get_amps():
	try:
		return int(''.join([chr(code) for code in data[14:14 + 3]])) / 10
	except:
		print('Warning: invalid amperage value')
		return 0.0

def get_serial_number():
	try:
		return ''.join([chr(code if (((code >= ord('0')) and (code <= ord('9'))) or ((code >= ord('A')) and (code <= ord('Z')))) else None) for code in data[17:17 + 23]])
	except:
		print('Warning: invalid serial number')
		return '???????????????????????'

def set_data(offset, s):
	for char in s:
		data[offset] = ord(char)
		offset += 1

def save_data(filename):
	crc = 0
	for offset in range(0, 40):
		byte = data[offset]
		crc ^= byte
		for i in range(0, 8):
			if crc & 1:
				crc = crc = (crc >> 1) ^ 0xA001;
			else:
				crc >>= 1
	crc_l = crc & 0xFF
	crc_h = crc >> 8
	if (crc_l != data[40]) or (crc_h != data[41]):
		print('Info: checksum changed. Updating...')
		data[40] = crc_l
		data[41] = crc_h
	with open(filename, 'w') as f:
		offset = 0
		while offset < EEPROM_SIZE:
			chunk = data[offset:offset + 16]
			chunk = [len(chunk), offset >> 8, offset & 0xFF, 0] + chunk
			checksum = 0
			for byte in chunk:
				checksum = (checksum + byte) & 0xFF
			checksum = (0x100 - checksum) & 0xFF
			f.write((':%s%02x\n' % (''.join(['%02x' % code for code in chunk]), checksum)).upper())
			offset += 16
		f.write(':00000001FF\n')

def print_menu():
	m = get_manufacturer()
	t = get_adapter_type()
	w = get_watts()
	v = get_volts()
	a = get_amps()
	sn = get_serial_number()
	print(' [0] Manufacturer  : %s' % m)
	print(' [1] Adapter type  : %s' % t)
	print(' [2] Watts         : %s' % w)
	print(' [3] Volts         : %s' % v)
	print(' [4] Amps          : %s' % a)
	print(' [5] Serial number : %s' % sn)
	print(' [6] Save changes and exit')
	print(' [7] Exit without saving changes')
	while True:
		try:
			return int(input('Select option [0-7]: '))
		except Exception:
			continue

while True:
	command = print_menu()
	if (command == 0) or (command == 1):
		value = input('Enter new value (4 chars): ')
		if len(value) != 4:
			print('Value shoud be 4 chars long!')
			continue
		valid = True
		for char in value:
			if not (((char >= '0') and (char <= '9')) or ((char >= 'A') and (char <= 'Z'))):
				valid = False
				break
		if not valid:
			print('Invalid value!')
			continue
		set_data(command * 4, value)
	elif command == 2:
		try:
			value = int(input('Enter new value [0-999]: '))
		except Exception:
			print('Invalid value!')
			continue
		if (value < 0) or (value > 999):
			print('Invalid value!')
			continue
		set_data(8, '%03d' % value)
	elif (command == 3) or (command == 4):
		try:
			value = float(input('Enter new value[0-99.9]: '))
		except Exception:
			print('Invalid value')
			continue
		if math.isnan(value) or (value < 0) or (value > 99.9):
			print('Invalid value')
			continue
		value = int(value * 10)
		set_data(11 if command == 3 else 14, '%03d' % value)
	elif command == 5:
		value = input('Enter new value (23 chars): ')
		if len(value) == 0:
			continue
		elif (len(value) != 23):
			print('Value shoud be 23 chars long!')
			continue
		valid = True
		for char in value:
			if not (((char >= '0') and (char <= '9')) or ((char >= 'A') and (char <= 'Z'))):
				valid = False
				break
		if not valid:
			print('Invalid value!')
			continue
		set_data(17, value)
	elif command == 6:
		save_data(filename)
		break
	elif command == 7:
		break

