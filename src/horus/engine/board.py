#!/usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------#
#                                                                       #
# This file is part of the Horus Project                                #
#                                                                       #
# Copyright (C) 2014 Mundo Reader S.L.                                  #
#                                                                       #
# Date: August 2014                                                     #
# Author: Jesús Arroyo Torrens <jesus.arroyo@bq.com>                    #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 2 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                       #
#-----------------------------------------------------------------------#

__author__ = "Jesús Arroyo Torrens <jesus.arroyo@bq.com>"
__license__ = "GNU General Public License v2 http://www.gnu.org/licenses/gpl.html"

import time
import serial


class Error(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return repr(self.msg)

class WrongFirmware(Error):
	def __init__(self, msg="WrongFirmware"):
		super(Error, self).__init__(msg)

class BoardNotConnected(Error):
	def __init__(self, msg="BoardNotConnected"):
		super(Error, self).__init__(msg)


class Board:
	"""Board class. For accessing to the scanner board"""
	"""
	Gcode commands:

		G1 Fnnn : feed rate
		G1 Xnnn : move motor

		M70 Tn  : switch off laser n
		M71 Tn  : switch on laser n

	"""
	def __init__(self, serialName='/dev/ttyUSB0', baudRate=115200):
		self.serialName = serialName
		self.baudRate = baudRate
		self.serialPort = None
		self.isConnected = False
		self._position = 0

	def setSerialName(self, serialName):
		self.serialName = serialName

	def setBaudRate(self, baudRate):
		self.baudRate = baudRate

	def connect(self):
		""" Opens serial port and performs handshake"""
		print ">>> Connecting board {0} {1}".format(self.serialName, self.baudRate)
		self.isConnected = False
		try:
			self.serialPort = serial.Serial(self.serialName, self.baudRate, timeout=2)
			if self.serialPort.isOpen():
				#-- Force Reset and flush
				self._reset()
				tries = 3
				#-- Check Handshake
				while tries:
					version = self.serialPort.readline()
					if len(version) > 20:
						break
					tries -= 1
					time.sleep(0.2)
				if version == "Horus 0.1 ['$' for help]\r\n":
					self.setSpeedMotor(1)
					self.setAbsolutePosition(0)
					#self.enableMotor()
					print ">>> Done"
					self.isConnected = True
				else:
					raise WrongFirmware()
			else:
				raise BoardNotConnected()
		except serial.SerialException:
			print "Error opening the port {0}\n".format(self.serialName)
			self.serialPort = None
			raise BoardNotConnected()

	def disconnect(self):
		""" Closes serial port """
		print ">>> Disconnecting board {0}".format(self.serialName)
		try:
			if self.serialPort is not None:
				self.serialPort.close()
		except serial.SerialException:
			print "Error closing the port {0}\n".format(self.serialName)
			print ">>> Error"
		print ">>> Done"

	def enableMotor(self):
		return self._sendCommand("M17")

	def disableMotor(self):
		return self._sendCommand("M18")

	def setSpeedMotor(self, feedRate):
		self.feedRate = feedRate
		return self._sendCommand("G1F{0}".format(self.feedRate))

	def setAccelerationMotor(self, acceleration):
		self.acceleration = acceleration
		return self._sendCommand("$120={0}".format(self.acceleration))

	def setRelativePosition(self, pos):
		self._posIncrement = pos

	def setAbsolutePosition(self, pos):
		self._posIncrement = 0
		self._position = pos

	def moveMotor(self):
		self._position += self._posIncrement
		return self._sendCommand("G1X{0}".format(self._position))

	def setRightLaserOn(self):
		return self._sendCommand("M71T2")
	 
	def setLeftLaserOn(self):
		return self._sendCommand("M71T1")
	
	def setRightLaserOff(self):
		return self._sendCommand("M70T2")
	 
	def setLeftLaserOff(self):
		return self._sendCommand("M70T1")

	def sendRequest(self, req, readLines=False):
		"""Sends the request and returns the response"""
		if self.serialPort is not None and self.serialPort.isOpen():
			try:
				self.serialPort.flushInput()
				self.serialPort.flushOutput()
				self.serialPort.write(req+"\r\n")
				if readLines:
					return ''.join(self.serialPort.readlines())
				else:
					return ''.join(self.serialPort.readline())
			except:
				pass

	def _checkAcknowledge(self, ack):
		if ack is not None:
			return ack.endswith("ok\r\n")
		else:
			return False

	def _sendCommand(self, cmd):
		return self._checkAcknowledge(self.sendRequest(cmd))

	def _reset(self):
		self.serialPort.setDTR(False)
		time.sleep(0.022)
		self.serialPort.flushInput()
		self.serialPort.flushOutput()
		self.serialPort.setDTR(True)
