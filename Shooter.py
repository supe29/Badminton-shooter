from machine import Pin, PWM
from utime import sleep, sleep_ms, sleep_us, ticks_ms, ticks_us, ticks_diff
from random import randrange



class Shooter:
  run = False
  hold_shuttle_motor = PWM(Pin(6)) # For x the angle in °, duty(x) = 36x + 1600
  push_shuttle_motor = PWM(Pin(7)) # For x the angle in °, duty(x) = 36x + 1600
  angle_motor = PWM(Pin(10)) # For x the angle in °, duty(x) = 24x + 1826
  slope_motor = PWM(Pin(11)) # For x the angle in °, duty(x) = 24x + 1826
  right_motor_in1 = Pin(17, Pin.OUT)
  right_motor_in2 = Pin(18, Pin.OUT)
  left_motor_in1 = Pin(19, Pin.OUT)
  left_motor_in2 = Pin(20, Pin.OUT)
  right_motor_en = PWM(Pin(16))
  left_motor_en = PWM(Pin(21))
  cylinder_in1 = Pin(14, Pin.OUT)
  cylinder_in2 = Pin(15, Pin.OUT)
  distance_sensor_trigger = Pin(13, Pin.OUT)
  distance_sensor_echo = Pin(12, Pin.IN)
  height_offset = 5
  delay_offset = 600
  default_cycle = 3000
  cycle = 3000
  max_shots = 300
  current_shot = None
  shots = []
  mode = 'once'
  order = 'normal'
  alive = True


  @classmethod
  def __check_height_distance(self):
    error_counter = 0
    height = 0
    while error_counter < 10:
      self.distance_sensor_trigger.low()
      sleep_us(2)
      self.distance_sensor_trigger.high()
      sleep_us(5)
      self.distance_sensor_trigger.low()
      counter = 0
      abort = False
      while self.distance_sensor_echo.value() == 0 and not abort:
        signal_off = ticks_us()
        counter += 1
        if counter > 2000: abort = True
      while self.distance_sensor_echo.value() == 1 and not abort:
        signal_on = ticks_us()
        counter += 1
        if counter > 2000: abort = True
      if not abort:
        try:
          height = ticks_diff(signal_on, signal_off) * 0.01715
        except:
          height = -1
        if height != -1:
          return height
      else:
        height = -2
      error_counter += 1
    return height


  @classmethod
  def __move_up(self):
    self.cylinder_in1.high()
    self.cylinder_in2.low()


  @classmethod
  def __move_down(self):
    self.cylinder_in1.low()
    self.cylinder_in2.high()


  @classmethod
  def __move_stop(self):
    self.cylinder_in1.low()
    self.cylinder_in2.low()


  @classmethod
  def __set_height(self, new_height):
    height = self.__check_height_distance()
    print(height)
    if height != -1 and height != -2:
      delta = height - new_height
      if delta < -2 or delta > 2:
        if height < new_height:
          self.__move_up()
          while height < new_height and height != -1 and height != -2:
            sleep_us(5000)
            height = self.__check_height_distance()
        elif height > new_height:
          self.__move_down()
          while height > new_height and height != -1 and height != -2:
            sleep_us(5000)
            height = self.__check_height_distance()
        self.__move_stop()
    if height == -1:
      print('The sensor is not cleaned')
    elif height == -2:
      print('The sensor did not receive any echo')


  @classmethod
  def __throw_start(self):
    self.right_motor_in1.high()
    self.right_motor_in2.low()
    self.left_motor_in1.low()
    self.left_motor_in2.high()

  @classmethod
  def __throw_stop(self):
    self.right_motor_in1.low()
    self.right_motor_in2.low()
    self.left_motor_in1.low()
    self.left_motor_in2.low()


  @classmethod
  def __set_speed(self, speed):
    duty = 455 * speed + 20000
    self.right_motor_en.duty_u16(duty)
    self.left_motor_en.duty_u16(duty)


  @classmethod
  def __set_angle(self, angle):
    duty = 24 * angle + 1826
    self.angle_motor.duty_u16(duty)


  @classmethod
  def __set_slope(self, slope):
    duty = 24 * slope + 1826
    self.slope_motor.duty_u16(duty)


  @classmethod
  def __set_program(self, program):
    sequence = program['seq']
    shots_number = int(program['shots'])
    shots_number = shots_number if shots_number > 0 and shots_number < self.max_shots else self.max_shots
    self.shots = []
    self.default_cycle = int(program['cycle'])
    self.cycle = self.default_cycle
    self.mode = program['mode']
    self.order = program['order']
    seq_length = len(sequence)
    if program['order'] == 'random':
      for _ in range(shots_number):
        ind = randrange(seq_length)
        self.shots.append({
          'speed': int(sequence[ind]['speed']),
          'angle': int(sequence[ind]['angle']),
          'slope': int(sequence[ind]['slope']),
          'height': int(sequence[ind]['height']),
          'recovery': int(sequence[ind]['recovery']),
          'delay': int(sequence[ind]['delay'])
        })
    elif program['mode'] == 'loop':
      for i in range(shots_number):
        ind = i % seq_length
        self.shots.append({
          'speed': int(sequence[ind]['speed']),
          'angle': int(sequence[ind]['angle']),
          'slope': int(sequence[ind]['slope']),
          'height': int(sequence[ind]['height']),
          'recovery': int(sequence[ind]['recovery']),
          'delay': int(sequence[ind]['delay'])
        })
    else:
      for seq in sequence:
        self.shots.append({
          'speed': int(seq['speed']),
          'angle': int(seq['angle']),
          'slope': int(seq['slope']),
          'height': int(seq['height']),
          'recovery': int(seq['recovery']),
          'delay': int(seq['delay'])
        })
    self.current_shot = self.shots.pop(0)


  @classmethod
  def __set_shot_position(self):
    print('set_position')
    delay_start = ticks_ms()

    self.cycle = self.default_cycle
    self.__set_height(self.current_shot['height'])
    self.__set_speed(self.current_shot['speed'])
    self.__set_angle(self.current_shot['angle'])
    self.__set_slope(self.current_shot['slope'])

    delay_end = ticks_ms()

    if self.current_shot['delay'] != 0:
      remaining_time = self.current_shot['delay'] - ticks_diff(delay_start, delay_end) - self.delay_offset
      if remaining_time > 0:
        sleep_ms(remaining_time)


  @classmethod
  def __next_shot(self):
    print('next_position')
    if self.current_shot['recovery'] != 0:
      sleep_ms(self.current_shot['recovery'])
      self.cycle = 0

    if len(self.shots) > 0:
      self.current_shot = self.shots.pop(0)
    else:
      self.current_shot = None


  @classmethod
  def init(self):
    self.right_motor_en.freq(1000)
    self.left_motor_en.freq(1000)
    self.angle_motor.freq(50)
    self.slope_motor.freq(50)
    self.hold_shuttle_motor.freq(50)
    self.push_shuttle_motor.freq(50)

    # Move to home position: 20°
    # For 20° as a home position for both motor the duty is:
    # duty(20) = int(((320 x 20) / 9) + 1600) = 2311
    self.hold_shuttle_motor.duty_u16(2311)
    self.push_shuttle_motor.duty_u16(2311)


    # Move to home position: 90°
    # For 90° as a home position for both motors, the duty is:
    # duty(90) = 24x + 1826 = 3986
    self.angle_motor.duty_u16(3986)
    self.slope_motor.duty_u16(3986)

    # Move cylinder to home position: 20
    # Do not forget to apply the offset of the sensor
    self.__set_height(20 + self.height_offset)

    print('Initialization done')

    self.alive = True
    while self.alive:
      if self.run:
        while self.alive and self.run and self.current_shot is not None:
          print('start_cycle')

          self.__set_shot_position()

          cycle_start = ticks_ms()
          # Release the shuttle, then block the upcoming shuttle after 0.2 second
          # Motor position for releasing the shuttle: 80°
          # duty(80) = int(((320 x 80) / 9) + 1600) = 4444
          self.hold_shuttle_motor.duty_u16(4444)
          sleep_ms(self.delay_offset)
          self.hold_shuttle_motor.duty_u16(2311)

          # Release the shuttle, then block the upcoming shuttle after 0.4 second
          # Motor position for releasing the shuttle: 120°
          # duty(120) = int(((320 x 120) / 9) + 1600) = 5867
          self.push_shuttle_motor.duty_u16(5867)
          sleep(.8)
          self.push_shuttle_motor.duty_u16(2311)
          sleep(.8)

          self.__next_shot()

          # Wait the next cycle
          cycle_end = ticks_ms()
          remaining_time = self.cycle - ticks_diff(cycle_end, cycle_start)
          print('remaining_time')
          print(remaining_time)
          if remaining_time > 0:
            sleep_ms(remaining_time)
          print('end_cycle')
        sleep(1)
      else:
        sleep(1)
    print('Thread dead')


  @classmethod
  def start(self, program):
    self.__set_program(program)
    self.__throw_start()
    self.run = True


  @classmethod
  def stop(self):
    self.run = False
    self.__throw_stop()
    self.__move_stop()


  @classmethod
  def kill(self):
    self.alive = False
    self.__throw_stop()
    self.__move_stop()

