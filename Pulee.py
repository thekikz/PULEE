import RPi.GPIO as GPIO
import time
import glob
import os
import MFRC522
import signal


class gpio:
#====== GPIO =======
    BuzzPin  = 13
    LEDPin1  = 27
    LEDPin2  = 22
    SwPin1   = 23
    SwPin2   = 24
    RelayPin = 17

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BuzzPin,GPIO.OUT)
        GPIO.setup(self.LEDPin1,GPIO.OUT)
        GPIO.setup(self.LEDPin2,GPIO.OUT)
        GPIO.setup(self.RelayPin,GPIO.OUT)
        GPIO.setup(self.SwPin1,GPIO.IN)
        GPIO.setup(self.SwPin2,GPIO.IN)
        GPIO.output(self.LEDPin1,GPIO.HIGH)
        GPIO.output(self.LEDPin2,GPIO.HIGH)

    def LED_ON(self,pin):
        if pin==1:
            GPIO.output(self.LEDPin1,GPIO.LOW)
        elif pin==2:
            GPIO.output(self.LEDPin2,GPIO.LOW)

    def LED_OFF(self,pin):
        if pin==1:
            GPIO.output(self.LEDPin1,GPIO.HIGH)
        elif pin==2:
            GPIO.output(self.LEDPin2,GPIO.HIGH)

    def read_sw1(self):
        return GPIO.input(self.SwPin1)

    def read_sw2(self):
        return GPIO.input(self.SwPin2)

    def relay_on(self):
        GPIO.output(self.RelayPin,True)

    def relay_off(self):
        GPIO.output(self.RelayPin,False)

    def buzz_beep(self):
        GPIO.output(self.BuzzPin,True)
        time.sleep(1)
        GPIO.output(self.BuzzPin,False)

#======== one wire temp sensor =======
class temp_sensor:
    def __init__(self):
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        time.sleep(0.3)
        self.init_file()

    def init_file(self):
        base_dir='/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir+'28*')[0]
        self.device_file = device_folder + '/w1_slave'

    def read_temp_raw(self):

        f = open(self.device_file,'r')
        lines = f.readlines()
        f.close()
        return lines

    def read_temp(self):
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:]!='YES':
            time.sleep(0.2)
            lines = self.read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string)/1000.0
            return temp_c


#======== RTC Clock ========
class RTC:

    def __init__(self):
        os.system('modprobe rtc-ds1307')
        os.system('echo mcp7941x 0x6f > /sys/bus/i2c/devices/i2c-1/new_device')

    def read_time(self):
        return time.strftime("DATE:%d/%m/%y TIME:%H:%M:%S")


#======== MFRC522 RFID ======
class RFID_Reader:

    MIFAREReader = MFRC522.MFRC522()

    def read_tag(self):

  # Scan for cards
        (status,TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)

        # If a card is found
        if status == self.MIFAREReader.MI_OK:
            print "Card detected"

  # Get the UID of the card
        (status,uid) = self.MIFAREReader.MFRC522_Anticoll()

        # If we have the UID, continue
        if status == self.MIFAREReader.MI_OK:

            # Print UID
            card_uid = "Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3])

            # This is the default key for authentication
            key = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]

            # Select the scanned tag
            self.MIFAREReader.MFRC522_SelectTag(uid)

            # Authenticate
            status = self.MIFAREReader.MFRC522_Auth(self.MIFAREReader.PICC_AUTHENT1A, 8, key, uid)

            # Check if authenticated
            if status == self.MIFAREReader.MI_OK:
                val = self.MIFAREReader.MFRC522_Read(8)
                self.MIFAREReader.MFRC522_StopCrypto1()
            else:
                return "Authentication error"
            return card_uid
