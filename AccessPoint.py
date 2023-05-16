import network
import socket
from utime import sleep

class AccessPoint:
  ssid = 'BadmintonShooter'
  password = '1234567890'
  sock = socket.socket()

  @classmethod
  def init(self):
    access_point = network.WLAN(network.AP_IF)
    access_point.config(essid=self.ssid, password=self.password)
    access_point.active(True)

    # Wait for wifi
    while access_point.active() == False:
      sleep(0.5)

    print('WiFi active')
    status = access_point.ifconfig()

    # Open socket
    # Default address => 192.168.4.1
    ip = status[0]
    addr = (ip, 80)
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sock.bind(addr)
    self.sock.listen(1)
    print('listening on', addr)
