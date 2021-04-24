import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(25, GPIO.OUT)
#GPIO.setup(17, GPIO.OUT)
GPIO.output(12, True)
GPIO.output(25, True)
#GPIO.output(17, True)
