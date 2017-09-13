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

def open_serial_port():
	try:
		import serial
		import serial.tools.list_ports
	except Exception as e:
		print(str(e))
		print('Please install pyserial to use this functional!')
		return
	while True:
		ports = serial.tools.list_ports.comports()
		print(' [0] Return to main menu')
		print(' [1] Enter custom serial port name')	
		i = 2
		for port in ports:
			print(' [%i] %s' % (i, port))
			i += 1
		try:
			j = int(input('Select option [0-%i]: ' % (i - 1)))
			if (j < 0) or (j >= i):
				continue
			if j == 0:
				return
			try:
				if j == 1:
					port = input('Enter serial port name (e. g. /dev/ttyUSB0, COM1): ')
					return serial.Serial(port)
				else:
					port = ports[j - 2]
					return serial.Serial(port[0])
			except Exception as e:
				print('Error: %s' % str(e))
		except Exception:
			continue

def ow_reset(port):
	port.timeout = 1
	port.bytesize = 8
	port.parity = 'N'
	port.stopbits = 1
	port.rtscts = 0
	port.xonxoff = 0
	port.baudrate = 9600
	port.write(b'\xF0')
	response = port.read(1)
	port.baudrate = 115200
	if len(response) != 1:
		print('Warning: Timeout! Did you forgot to connect diode RX -|>|- TX?')
	return (len(response) == 1) and (response[0] < 0xF0)

def ow_write(port, byte):
	for i in range(0, 8):
		value = b'\xFF' if byte & (1 << i) else b'\x00'
		port.write(value)
		response = port.read(1)
		if (len(response) != 1) or (response[0] != value[0]):
			return False
	return True

def ow_write_bytes(port, bytes):
	for byte in bytes:
		if not ow_write(port, byte):
			return False
	return True

def ow_read(port):
	value = 0
	for i in range(0, 8):
		port.write(b'\xFF')
		response = port.read(1)
		if len(response) != 1:
			return None
		if response[0] > 0xFE:
			value |= 1 << i
	return value

def ow_read_bytes(port, count):
	bytes = list()
	offset = 0
	while offset < count:
		byte = ow_read(port)
		if byte is None:
			return None
		bytes.append(byte)
		if (offset % 16) != 15:
			print('%02x ' % byte, end='', flush=True)
		else:
			print('%02x' % byte)
		offset += 1
	print('')
	return bytes

def read_eeprom():
	global data
	port = open_serial_port()
	if not port:
		return
	with port as port:
		if not ow_reset(port):
			print('Failed to issue OneWire reset!')
			return
		if not ow_write_bytes(port, b'\xCC\xF0\x00\x00'):
			print('Failed to send READ MEM command!')
			return
		print('Reading EEPROM...')
		bytes = ow_read_bytes(port, 130)
		if bytes is None:
			print('Failed to read data!')
		data = bytes[1:-1]
		print('Done')

def write_eeprom():
	port = open_serial_port()
	if not port:
		return
	with port as port:
		print('Writing...')
		offset = 0
		while offset < len(data):
			byte = data[offset]
			if not ow_reset(port):
				print('Failed to issue OneWire reset (offset = %i)!' % offset)
				return
			if not ow_write_bytes(port, b'\xCC\x0F' + bytes([offset & 0xFF, offset >> 8, byte])):
				print('Failed to issue WRITE MEM command (offset = %i)!' % offset)
				return
			response = ow_read(port)
			if response is None:
				print('Write failed (offset = %i)!' % offset)
			if (offset % 16) != 15:
				print('%02x ' % response, end='', flush=True)
			else:
				print('%02x' % response)
			offset += 1
		print('')
		print('Done')

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
	print(' [8] Read EEPROM data via 1wire')
	print(' [9] Write EEPROM data via 1wire')
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
	elif command == 8:
		read_eeprom()
	elif command == 9:
		write_eeprom()

