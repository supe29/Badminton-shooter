import network
import socket
import json
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
ip = status[0]
addr = (ip, 80)
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
print('listening on', addr)
home = 'home.html'

areas = []
for i in range(49):
  areas.append({
    'id': i + 1,
    'shots': [{
      'name': 'lob',
      'config': {
        'speed': 0,
        'angle': 0,
        'slope': 0,
        'height': 0
      }
    },{
      'name': 'drive',
      'config': {
        'speed': 0,
        'angle': 0,
        'slope': 0,
        'height': 0
      }
    },{
      'name': 'smash',
      'config': {
        'speed': 0,
        'angle': 0,
        'slope': 0,
        'height': 0
      }
    }]
  })

# Main loop
test = True
while test:
  client, client_addr = s.accept()
  raw_request = client.recv(1024)

  # translate byte string to normal string variable
  raw_request = raw_request.decode("utf-8")
  split_request = raw_request.split()
  print(raw_request)
  if len(split_request) > 1:
    method = split_request[0]
    path = split_request[1]
    if path == '/':
      file = open(home, 'r')
      html = file.read()
      file.close()
      client.sendall(html.encode('utf-8'))
    elif path.startswith('/area'):
      if method == 'GET':
        if len(path) == 5:
          client.sendall(json.dumps(areas, separators=(',', ':')).encode('utf-8'))
        else:
          rpath = path[6:]
          if '/' in rpath:
            sp = rpath.split('/')
            try:
              area = next((a for a in areas if a['id'] == int(sp[0])), None)
            except StopIteration:
              area = None
            if area is not None:
              try:
                shot = next((s for s in area['shots'] if s['name'] == sp[1]), None)
              except StopIteration:
                shot = None
              if shot is not None:
                client.sendall(json.dumps(shot, separators=(',', ':')).encode('utf-8'))
          else:
            try:
              area = next(a for a in areas if a['id'] == int(rpath))
            except StopIteration:
              area = None
            if area is not None:
              client.sendall(json.dumps(area, separators=(',', ':')).encode('utf-8'))
            else:
              # To be more precise: id not valid
              msg = '{"message":"Area ID not valid"}'
              client.sendall(msg.encode('utf-8'))
      if method == 'POST':
        body = raw_request.splitlines()[-1]
        shot_to_save = json.loads(body)
        if len(path) == 5:
          # Not implemented yet
          msg = '{"message":"Areas update not yet implemented"}'
          client.sendall(msg.encode('utf-8'))
        else:
          rpath = path[6:]
          if '/' in rpath:
            sp = rpath.split('/')
            try:
              area = next((a for a in areas if a['id'] == int(sp[0])))
            except StopIteration:
              area = None
            if area is not None:
              try:
                shot = next((s for s in area['shots'] if s['name'] == sp[1]))
              except StopIteration:
                shot = None
              if shot is not None:
                shot['name'] = shot_to_save['name']
                shot['config']['speed'] = shot_to_save['config']['speed']
                shot['config']['angle'] = shot_to_save['config']['angle']
                shot['config']['slope'] = shot_to_save['config']['slope']
                shot['config']['height'] = shot_to_save['config']['height']
                msg = '{"message":"Shot has been updated: ' + sp[1] + '"}'
                client.sendall(msg.encode('utf-8'))
              else:
                area['shots'].append(shot_to_save)
                msg = '{"message":"New shot has been saved: ' + sp[1] + '"}'
                client.sendall(msg.encode('utf-8'))
            else:
              # To be more precise: id not valid
              msg = '{"message":"Area ID not valid"}'
              client.sendall(msg.encode('utf-8'))
          else:
            # Not implemented yet
            msg = '{"message":"Shots update not yet implemented"}'
            client.sendall(msg.encode('utf-8'))
    elif path == '/quit':
      client.sendall('End'.encode('utf-8'))
      test = False
  client.close()
