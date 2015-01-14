import tornado.ioloop
import tornado.options
import tornado.websocket
import tornado.httpserver
import tornado.web
import RPi.GPIO as GPIO
import Pulee
import time
import thread
import signal
import sys
from tornado.options import define,options
define("port",default=8888,type=int)

clients=[]
client_rfid=[]

temp_sensor = Pulee.temp_sensor()
rtc_mod     = Pulee.RTC()
rfid_read   = Pulee.RFID_Reader()
gpio        = Pulee.gpio()

temp_sw1 = 1
temp_sw2 = 1
run_cont = True


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class JqueryHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('jquery.min.js')

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self,origin):
        return True

    def open(self):
        clients.append(self)
        print 'new connection'
        self.write_message("connected")

    def on_message(self,message):
        print 'message recived %s' % message
        self.write_message(message)
        for c in clients:
            c.write_message(message)
        if message == 'D1_on':
            gpio.LED_ON(1)
        elif message == "D1_off":
            gpio.LED_OFF(1)
        elif message == "D2_on":
            gpio.LED_ON(2)
        elif message == "D2_off":
            gpio.LED_OFF(2)
        elif message == "beep":
            gpio.buzz_beep()
        elif message == "relay_on":
            gpio.relay_on()
        elif message == "relay_off":
            gpio.relay_off()

    def on_close(self):
        clients.remove(self)
        print 'connection closed'

def button_read():
    global temp_sw1
    global temp_sw2
    sw1 = gpio.read_sw1()
    sw2 = gpio.read_sw2()
    if((sw1==0) and (temp_sw1==1)):

        for c in clients:
            c.write_message("sw1_press")
            temp_sw1=0
    elif((sw1==1) and (temp_sw1==0)) :
        for c in clients:
            c.write_message("sw1_unpress")
            temp_sw1=1

    if((sw2==0) and (temp_sw2==1)):
        for c in clients:
            c.write_message("sw2_press")
            temp_sw2=0
    elif((sw2==1) and (temp_sw2==0)) :
        for c in clients:
            c.write_message("sw2_unpress")
            temp_sw2=1

def end_read(signal,frame):
    global run_cont
    run_cont=False
    GPIO.cleanup()
    sys.exit("Ending Test Program")

def temp_thread():
    while run_cont:
        Temp_val = temp_sensor.read_temp()
        for c in clients:
            c.write_message("T"+str(Temp_val))
        time.sleep(0.2)


def rfid_thread():
    while run_cont:
        try:
            rfid_val = rfid_read.read_tag()
        except Exception as err:
            print "Endding Read RFID"

        if rfid_val is not None:
            print rfid_val
            for c in clients:
                c.write_message(str(rfid_val))


def read_rtc():
    time = rtc_mod.read_time()
    for c in clients:
        c.write_message(str(time))

signal.signal(signal.SIGINT,end_read)

if __name__=="__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(
                                handlers = [
                                    (r"/",IndexHandler),
                                    (r"/ws",WebSocketHandler)
                                ]
    )
    print "Test"
    try:
        thread.start_new_thread(rfid_thread,())
    except Exception as err :
        print "End RFID Thread "

    try:
        thread.start_new_thread(temp_thread,())
    except Exception as err :
        print "End Temp Sensor Thread "

    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    print "Listening on port :",options.port
    mainloop = tornado.ioloop.IOLoop.instance()
    sw_scheduler = tornado.ioloop.PeriodicCallback(button_read,50)
    time_scheduler = tornado.ioloop.PeriodicCallback(read_rtc,1000)

    time_scheduler.start()
    sw_scheduler.start()
    mainloop.start()
