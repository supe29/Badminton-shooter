import network
import socket
import Credentials
from utime import sleep



class AccessPoint:

  @classmethod
  def init(self):
    self._access_point = network.WLAN(network.AP_IF)
    self._access_point.config(essid=Credentials.ssid, password=Credentials.password)
    self._access_point.active(True)

    # Wait for wifi
    while self._access_point.active() == False:
      sleep(0.5)

    print('WiFi active')
    status = self._access_point.ifconfig()

    # Open socket
    # Default address => 192.168.4.1
    ip = status[0]
    addr = (ip, 80)
    self.sock = socket.socket()
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sock.bind(addr)
    self.sock.listen(1)
    print('listening on', addr)


  @classmethod
  def close(self):
    self._access_point.active(False)
