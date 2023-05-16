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
home = '/sd/home.html'
default_config = '/sd/default.json'
areas = []

def int_val(str, min, max):
  try:
    s = int(str)
  except ValueError:
    s = -1
  if s < min or s > max:
    s = -1
  return s

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
      shot = get(area['shots'], 'name', sp[1])
      if shot is not None:
        return {'code': 0, 'msg': 'Shot ' + sp[1] + ' was found', 'area': sp[0], 'shot': sp[1], 'obj': shot, 'area': sp[0], 'shot': sp[1], 'par': area['shots']}
      else:
        return {'code': 1, 'msg': 'Shot ' + sp[1] + ' was not found', 'area': sp[0], 'shot': sp[1], 'obj': area}
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

def check_params(p):
  ret_value = 0

  # Speed
  x = int_val(p['speed'], 0, 100)
  if x == -1:
    ret_value = 1

  # Angle
  x = int_val(p['angle'], 0, 180)
  if x == -1:
    ret_value += 2

  # Slope
  x = int_val(p['slope'], 0, 180)
  if x == -1:
    ret_value += 4

  # Height
  x = int_val(p['height'], 0, 40)
  if x == -1:
    ret_value += 8

  return ret_value

def main():
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
      if path == '/':
        with open(home, 'r') as file:
          html = file.read()
        client.sendall(html.encode('utf-8'))
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
              o['obj'].append(to_save)
              msg = '{"msg":"New shot has been saved in area ' + o['area'] + ': ' + o['shot'] + '"}'
              save(areas)
              client.sendall(msg.encode('utf-8'))
            elif o['code'] == 2:
              o['obj']['shots'] = []
              for s in to_save:
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
        client.sendall('End'.encode('utf-8'))
        test = False
        Shooter.kill()
    client.close()


MicroSD.init()
AccessPoint.init()
with open(default_config, 'r') as file:
  areas = json.load(file)
shuttle_handler = _thread.start_new_thread(run_cycle, ())
main()

