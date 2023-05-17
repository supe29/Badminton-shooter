import json
from MicroSD import MicroSD
from Shooter import Shooter
from AccessPoint import AccessPoint
import _thread

c_speed = 0
c_angle = 0
c_slope = 0
c_height = 0
speed_duty = 0
angle_duty = 0
slope_duty = 0
height_val = 0
sd_location = '/sd'
home = sd_location + '/home.html'
default_config = sd_location + '/default.json'
character_encoding_file = sd_location + '/character-encoding.json'
areas = []
characters_encoding = []

def decode_url(str):
  decoded_string = str

  for c in characters_encoding:
    decoded_string = decoded_string.replace(c['key'], c['value'])

  return decoded_string

def int_val(str, min, max):
  try:
    value = int(str)
  except ValueError:
    value = -1
  if value < min or value > max:
    value = -1
  return value

def get(arr, key, val):
  try:
    return next((a for a in arr if a[key] == val))
  except StopIteration:
    return None

def find_obj(areas, str):
  sp = str.split('/')
  area = get(areas, 'id', int(sp[0]))
  if area is not None:
    if '/' in str:
      print(decode_url(sp[1]))
      shot = get(area['shots'], 'name', decode_url(sp[1]))
      if shot is not None:
        return {'code': 0, 'msg': 'Shot ' + decode_url(sp[1]) + ' was found', 'area': sp[0], 'shot': decode_url(sp[1]), 'obj': shot, 'area': sp[0], 'shot': decode_url(sp[1]), 'par': area['shots']}
      else:
        return {'code': 1, 'msg': 'Shot ' + decode_url(sp[1]) + ' was not found', 'area': sp[0], 'shot': decode_url(sp[1]), 'obj': area}
    else:
      return {'code': 2, 'msg': 'Area ' + sp[0] + ' was found', 'area': str, 'obj': area}
  else:
    return {'code': 3, 'msg': 'Area ' + sp[0] + ' was not found', 'area': str, 'obj': None}

def save(a):
  areas_json = json.dumps(a)
  with open(default_config, 'w') as file:
    file.write(areas_json)
  print('saved')

def run_cycle():
  Shooter.init()

def check_params(param, training=False):
  ret_value = 0

  # Speed
  value = int_val(param['speed'], 0, 100)
  if value == -1:
    ret_value = 1

  # Angle
  value = int_val(param['angle'], 0, 180)
  if value == -1:
    ret_value += 2

  # Slope
  value = int_val(param['slope'], 0, 180)
  if value == -1:
    ret_value += 4

  # Height
  value = int_val(param['height'], 0, 40)
  if value == -1:
    ret_value += 8

  if training:
    # Recovery
    value = int_val(param['recovery'], 0, 60)
    if value == -1:
      ret_value += 16

    # Delay
    value = int_val(param['delay'], 0, 60)
    if value == -1:
      ret_value += 32

  return ret_value

def check_training_parameters(param):
  ret_value = 0

  valid_mode = ['loop', 'once']
  valid_order = ['random', 'normal']

  # Mode
  if param['mode'] not in valid_mode:
    ret_value = 1

  # Order
  if param['order'] not in valid_order:
    ret_value += 2

  # Shots number
  value = int_val(param['shots'], 0, 600)
  if value == -1:
    ret_value += 4

  # Default time between 2 shots
  value = int_val(param['cycle'], 0, 60)
  if value == -1:
    ret_value += 8

  return ret_value

def main():
  global areas

  test = True
  while test:
    client, client_addr = AccessPoint.sock.accept()
    raw_request = client.recv(1024)

    # translate byte string to normal string variable
    raw_request = raw_request.decode("utf-8")
    split_request = raw_request.split()
    print(raw_request)
    if len(split_request) > 1:
      method = split_request[0]
      path = split_request[1]
      if path in ['/', '/favicon.png', '/style.css', '/main.js']:
        filename = home if path == '/' else sd_location + path
        print(filename)
        with open(filename, 'rb') as file:
          data = file.read()
        client.sendall(data)
      elif path.startswith('/area'):
        if method == 'GET':
          if len(path) == 5:
            client.sendall(json.dumps(areas, separators=(',', ':')).encode('utf-8'))
          else:
            o = find_obj(areas, path[6:])
            if o['code'] | 1 != o['code']:
              client.sendall(json.dumps(o['obj'], separators=(',', ':')).encode('utf-8'))
            else:
              msg = '{"msg":"' + o['msg'] + '}'
              client.sendall(msg.encode('utf-8'))
        elif method == 'POST':
          body = raw_request.splitlines()[-1]
          to_save = json.loads(body)
          if len(path) == 5:
            # Not implemented yet
            client.sendall('{"msg":"Areas update not yet implemented"}'.encode('utf-8'))
          else:
            o = find_obj(areas, path[6:])
            if o['code'] == 0:
              o['obj']['name'] = to_save['name']
              o['obj']['config']['speed'] = to_save['config']['speed']
              o['obj']['config']['angle'] = to_save['config']['angle']
              o['obj']['config']['slope'] = to_save['config']['slope']
              o['obj']['config']['height'] = to_save['config']['height']
              msg = '{"msg":"Shot ' + o['shot'] + ' has been updated in area ' + o['area'] + '"}'
              save(areas)
              client.sendall(msg.encode('utf-8'))
            elif o['code'] == 1:
              if to_save['name'].strip() == '':
                client.sendall('{"msg":"The name is empty"}'.encode('utf-8'))
              else:
                o['obj']['shots'].append(to_save)
                msg = '{"msg":"New shot has been saved in area ' + o['area'] + ': ' + o['shot'] + '"}'
                save(areas)
                client.sendall(msg.encode('utf-8'))
            elif o['code'] == 2:
              o['obj']['shots'] = []
              for _ in to_save:
                o['obj']['shots'].append({
                  'name': to_save['name'],
                  'config': {
                    'speed': to_save['config']['speed'],
                    'angle': to_save['config']['angle'],
                    'slope': to_save['config']['slope'],
                    'height': to_save['config']['height']
                  }
                })
              msg = '{"msg":"New shots have been saved in area ' + o['area'] + '"}'
              save(areas)
              client.sendall(msg.encode('utf-8'))
            elif o['code'] == 3:
              msg = '{"msg":"' + o['msg'] + '}'
              client.sendall(msg.encode('utf-8'))
            else:
              client.sendall('{"msg":"An unexpected error occured"}'.encode('utf-8'))
        elif method == 'DELETE':
          if len(path) == 5:
            client.sendall('{"msg":"Nothing to delete"}'.encode('utf-8'))
          else:
            o = find_obj(areas, path[6:])
            if o['code'] & 1 == 1:
              client.sendall('{"msg":"Nothing to delete"}'.encode('utf-8'))
            elif o['code'] == 0:
              o['par'] = [s for s in o['par'] if s['name'] != o['shot']]
              msg = '{"msg":"Shot ' + o['name'] + ' has been removed from area ' + o['area'] + '"}'
              client.sendall(msg.encode('utf-8'))
            elif o['code'] == 2:
              o['obj']['shots'] = []
              msg = '{"msg":"All shots have been removed from area ' + o['area'] + '"}'
              client.sendall(msg.encode('utf-8'))
        else:
          msg = '{"msg":"The method ' + method + ' is not implemented"}'
          client.sendall(msg.encode('utf-8'))
      elif path.startswith('/preview'):
        if method == 'POST':
          body = raw_request.splitlines()[-1]
          params = json.loads(body)
          if len(path) == 8:
            st = check_params(params)
            if st == 0:
              Shooter.start({
                'seq': [{
                  'speed': int(params['speed']),
                  'angle': int(params['angle']),
                  'slope': int(params['slope']),
                  'height': int(params['height']),
                  'recovery': 0,
                  'delay': 0
                }],
                'mode': 'loop',
                'order': 'normal',
                'shots': 1000000,
                'cycle': 3000
              })
              client.sendall('{"msg":"Started"}'.encode('utf-8'))
            else:
              client.sendall('{"msg":"An error occured"}'.encode('utf-8'))
          else:
            # Not implemented yet
            client.sendall('{"msg":"Start with parameters not yet implemented"}'.encode('utf-8'))
        else:
          msg = '{"msg":"The method ' + method + ' is not implemented"}'
          client.sendall(msg.encode('utf-8'))
      elif path.startswith('/training'):
        if method == 'POST':
          body = raw_request.splitlines()[-1]
          params = json.loads(body)
          if len(path) == 9:
            error_handler = 0
            err_message = []
            err = 0
            for param in params['seq']:
              err = check_params(param, training=True)
              error_handler += err
              if err & 1 == 1:
                err_message.append({
                  'message': 'The speed is incorrect',
                  'value': param['speed']
                })
              if err & 2 == 2:
                err_message.append({
                  'message': 'The angle is incorrect',
                  'value': param['angle']
                })
              if err & 4 == 4:
                err_message.append({
                  'message': 'The slope is incorrect',
                  'value': param['slope']
                })
              if err & 8 == 8:
                err_message.append({
                  'message': 'The height is incorrect',
                  'value': param['height']
                })
              if err & 16 == 16:
                err_message.append({
                  'message': 'The recovery is incorrect',
                  'value': param['recovery']
                })
              if err & 32 == 32:
                err_message.append({
                  'message': 'The delay is incorrect',
                  'value': param['delay']
                })

            err = check_training_parameters(params)
            error_handler += err
            if err & 1 == 1:
              err_message.append({
                'message': 'The mode is incorrect',
                'value': params['mode']
              })
            if err & 2 == 2:
              err_message.append({
                'message': 'The order is incorrect',
                'value': params['order']
              })
            if err & 4 == 4:
              err_message.append({
                'message': 'The shots is incorrect',
                'value': params['shots']
              })
            if err & 8 == 8:
              err_message.append({
                'message': 'The cycle is incorrect',
                'value': params['cycle']
              })


            if error_handler == 0:
              Shooter.start({
                'seq': params['seq'],
                'mode': params['mode'],
                'order': params['order'],
                'shots': int(params['shots']),
                'cycle': int(params['cycle']) * 1000
              })
              client.sendall('{"msg":"Training started"}'.encode('utf-8'))
            else:
              msg = '{"msg":"Error(s) have been detected","errors":' + json.dumps(err_message, separators=(',', ':')) + '}'
              client.sendall(msg.encode('utf-8'))
          else:
            # Not implemented yet
            client.sendall('{"msg":"Training with profile is not yet implemented"}'.encode('utf-8'))
        else:
          msg = '{"msg":"The method ' + method + ' is not implemented"}'
          client.sendall(msg.encode('utf-8'))
      elif path.startswith('/stop'):
        if method == 'GET':
          if len(path) == 5:
            Shooter.stop()
            client.sendall('{"msg":"Stopped"}'.encode('utf-8'))
          else:
            # Not implemented yet
            client.sendall('{"msg":"Stop does not take any url parameters"}'.encode('utf-8'))
        else:
          msg = '{"msg":"The method ' + method + ' is not implemented"}'
          client.sendall(msg.encode('utf-8'))
      elif path == '/quit':
        client.sendall('{"msg":"Quitted"}'.encode('utf-8'))
        test = False
        Shooter.kill()
    client.close()

def run():
  global areas
  global characters_encoding

  MicroSD.init()
  AccessPoint.init()

  with open(default_config, 'r') as file:
    areas = json.load(file)

  with open(character_encoding_file, 'r') as file:
    characters_encoding = json.load(file)

  _thread.start_new_thread(run_cycle, ())
  main()

run()

