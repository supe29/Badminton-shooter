import network
import socket
from machine import Pin

ssid = 'BadmintonShooter'
password = '1234567890'

ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)

# Wait for wifi
while ap.active() == False:
  time.sleep(0.5)
  pass

print('WiFi active')
status = ap.ifconfig()

# Open socket
# Default address => 192.168.4.1
addr = (status[0], 80)
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
print('listening on', addr)

led1 = Pin(15, Pin.OUT)
led2 = Pin(16, Pin.OUT)
led1.off()
led2.off()
state1 = False
state2 = False

# main loop
while True:
  client, client_addr = s.accept()
  raw_request = client.recv(1024)

  # translate byte string to normal string variable
  raw_request = raw_request.decode("utf-8")
  split_request = raw_request.split()
  if len(split_request) > 1:
    request_url = raw_request.split()[1]

    # LED 1
    if request_url.find("/led1on") != -1:
      # turn LED on
      led1.on()
      state1 = True
    elif request_url.find("/led1off") != -1:
      # turn LED off
      led1.off()
      state1 = False

    # LED 2
    elif request_url.find("/led2on") != -1:
      # turn LED off
      led2.on()
      state2 = True
    elif request_url.find("/led2off") != -1:
      # turn LED off
      led2.off()
      state2 = False
    else:
      # do nothing
      pass

    led1_str = "ON"
    led2_str = "ON"
    led1_path = "led1on"
    led2_path = "led2on"
    if state1:
      led1_str = "OFF"
      led1_path = "led1off"
    if state2:
      led2_str = "OFF"
      led2_path = "led2off"

    file = open("home.html")
    html = file.read()
    file.close()

    html = html.replace('**state1**', led1_str)
    html = html.replace('**path1**', led1_path)
    html = html.replace('**state2**', led2_str)
    html = html.replace('**path2**', led2_path)
    client.send(html)
  client.close()
