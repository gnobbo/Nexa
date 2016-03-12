# coding: utf-8

import RPi.GPIO as GPIO
import time   
import sys
import argparse
  
class Command: # class for command to be sent to receiver 

	def __init__(self, id, group, on_off, ch, unit):
		self.id = id  # id in decimal format
		self.group = group	 # 1 bit (1 = no group, 0 = group)
		self.on_off = on_off  # 1 bit (1 = off, 0 = on)
		self.ch = ch  # 2 bits
		self.unit = unit  # 2 bits
		self.command = [] # 32 bits (complete command, created at runtime)
		self.wire_command = [] # 64 bits (command encoded round #1, used in Command.send())
		self.calibrate = 0  # for test purposes, not used otherwise

	def calibrateDelay(self):  # test routine for estimating delay in python execution
		delta_tot = 0
		for i in range(100000):
			start = time.time()
			stop = time.time()
			delta_1 = (stop - start) * 1e6
			start = time.time()
			self.delay(0)
			stop = time.time()
			delta_2 = (stop - start) * 1e6 - delta_1 
			delta_tot += delta_2
		self.calibrate = delta_tot / 100000.0     
		print self.calibrate		

	def makeIdBinary(self):  # encode decimal id to bnary format
		a = list(str(bin(self.id)[2:]).zfill(26))
		self.id = []
		for elem in a:
			self.id.append(int(elem))

	def generate(self):  # concatenate parts to complete command
		self.command = self.id + self.group + self.on_off + self.ch + self.unit

	def encode(self):  # "redundance" coding according to Nexa protocol
		for i in self.command:
			if i == 0:
				self.wire_command += [0,1]  # a "zero" shall be transmitted as "01" according to protocol
			if i == 1:
				self.wire_command += [1,0]	# a "one shall be transmitted as "10" according to protocol

	def delay(self, howlong):  # delay for creating "wire bits" (to transmitter)
		start = time.time() * 1e6
		while (start + howlong) > time.time() * 1e6:
			pass

	def send(self):  # sends command to receiver
		for k in range(3): # send command three times (python/os may distort pulse times)

			for j in range(5): # five "burstar" according to protocol
				
				# send synchronization bit
				GPIO.output(21,1)
				self.delay(220)  # delay becomes approx. (x) + 30 us (250 us) due to program execution delay
				GPIO.output(21,0)
				self.delay(2750)

				# send command
				for i in self.wire_command:
					GPIO.output(21, 1)
					self.delay(220)		
					GPIO.output(21, 0)
					self.delay(200 + 1000 * int(not(i)))		
				
				# send stop bit
				GPIO.output(21,1)
				self.delay(220)
				GPIO.output(21,0)
				self.delay(10500)

			self.delay(1e6)


# ----- MAIN PROGRAM -----
# parse possible input arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--id", type=int, default=48234567, help="unikt ID för sändaren")
parser.add_argument("-u", "--unit", type=int, default=1, choices=[0,1,2], help="enhet att skicka till")
parser.add_argument("-c", "--command", type=str, default="on", choices=["on","off"], help="kommando (on/off)")
parser.add_argument("-g", "--group", type=str, default="off", choices=["on","off"], help="gruppkommando (on/off)")

args = parser.parse_args()

# unit 0 = 11, unit 2 = 10, unit 3 = 01
if args.unit == 0:
	unit = [1,1]
elif args.unit == 1:
	unit = [1,0]
elif args.unit == 2:
	unit = [0,1]

# 0 = on, 1 = off
if args.command == "on":
	on_off = [0]  
if args.command == "off":
	on_off = [1]

# on = on, 1 = off
if args.group == "on":
	group = [0]  
if args.group == "off":
	group = [1]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) 
GPIO.setup(21, GPIO.OUT, initial=0)  

id = args.id  # between 0 and 67108863
group = [1] # 1 = off
ch = [1,1]  # 11 for Nexa system 

try:
	objCommand = Command(id, group, on_off, ch, unit)
	# objCommand.calibrateDelay() # for test purposes
	objCommand.makeIdBinary()
	objCommand.generate()
	objCommand.encode()	
	print "Sending \"" + args.command + "\" to unit " + str(args.unit) + " from transmitter " + \
			str(args.id) + ", group command " + args.group + "..."
	objCommand.send()
	print "...finished"

except KeyboardInterrupt:
	print "stopped"
	GPIO.cleanup()  # tidy up
