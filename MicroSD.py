from machine import Pin, SPI
from sdcard import SDCard
from uos import VfsFat, mount

class MicroSD:
  cs = Pin(1, Pin.OUT)
  spi = SPI(0, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(2), mosi=Pin(3), miso=Pin(0))

  @classmethod
  def init(self):
    # Initialize SD card
    sd = SDCard(self.spi, self.cs)

    # Mount filesystem
    vfs = VfsFat(sd)
    mount(vfs, "/sd")
