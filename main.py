import machine
import ubinascii
import network
import time
import json

from umqttsimple import MQTTClient
import secrets

### MQTT SETUP
mqtt_server = secrets.mqtt_server

### Ping interval for Mosquitto >= 2.0
ping_interval = 60
last_ping = 0

### Home Assistant Auto Discovery setup
### Reference: https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery
client_id = ubinascii.hexlify(machine.unique_id()).decode()
cid = client_id[-2:]

node_id = f'motion_sensor_{cid}'
discovery_device = {
  "name":f"Motion Sensor {cid}",
  "identifiers": node_id,
  "manufacturer": 'Infineon',
  "model": 'PSoC6',
  "sw_version": '0.1.0'
  }

discovery_prefix = 'homeassistant'
discovery_entities = {
    'td':{
        'discovery_topic':f'{discovery_prefix}/binary_sensor/{node_id}',
        'conf': {
            "name":"Target Detected",
            "unique_id":"td",
            "state_topic":f'{discovery_prefix}/binary_sensor/{node_id}/state/td',
            "device": discovery_device,
            "device_class":"motion"
            }
        },
    'pd':{
        'discovery_topic':f'{discovery_prefix}/binary_sensor/{node_id}',
        'conf': {
            "name":"Target Approaching",
            "unique_id":"pd",
            "state_topic":f'{discovery_prefix}/binary_sensor/{node_id}/state/pd',
            "device": discovery_device,
            "availability_topic":f'{discovery_prefix}/binary_sensor/{node_id}/avl/pd',
            "icon":"mdi:ray-end-arrow"
            }
        }
}

class BinarySensor:
  def __init__(self, entity, pin, invert=False, pull=None):
    self._entity = entity
    self._pin = machine.Pin(pin, machine.Pin.IN, pull)
    self._invert = invert
    self._isActive = False
    self._isAvailable = False
  def read(self):
    return (self._pin.value() == 1) != self._invert
  def event(self):
    if self.read() and not self._isActive:
      self._isActive = True
      return 'ON'
    if not self.read() and self._isActive:
      self._isActive = False
      return 'OFF'
    return False
  def available(self, available):
    if available and not self._isAvailable:
      self._isAvailable = True
      available = 'online'
    elif not available and self._isAvailable:
      self._isAvailable = False
      available = 'offline'
    else:
      return
    client.publish(discovery_entities[self._entity]['conf']['availability_topic'], available)
  def update(self):
    e = self.event()
    if e: client.publish(discovery_entities[self._entity]['conf']['state_topic'], e)

class RadarSensor:
  def __init__(self, pinTD, pinPD):
    self.targetDet = BinarySensor('td', 'P6_5', invert=True, pull=machine.Pin.PULL_DOWN)
    self.phaseDet = BinarySensor('pd', 'P6_4', invert=False, pull=machine.Pin.PULL_DOWN)
  def update(self):
    self.targetDet.update()
    if self.targetDet.read():
      self.phaseDet.available(True)
      self.phaseDet.update()
    else:
      self.phaseDet.available(False)

def connect_wifi():
  station.active(False)
  time.sleep(0.1)
  station.active(True)
  station.connect(secrets.ssid, secrets.password)

  ### Wait to connect to WiFi (with timeout)
  counter = 0
  while not station.isconnected():
    time.sleep(2)
    if counter > 20:
      machine.reset()
    counter = counter+1
  
  print('Connection successful')
  print(station.ifconfig())

def restart():
  print('Failed to connect to MQTT broker. Restarting...')
  machine.reset()

def connect_and_subscribe():
  global client_id, mqtt_server

  client = MQTTClient(client_id, mqtt_server, user=secrets.mqtt_user, password=secrets.mqtt_password, keepalive=ping_interval+30)
  client.connect()
  
  print('Connected to MQTT broker.')
  return client

station = network.WLAN(network.STA_IF)

connect_wifi()

try:
  client = connect_and_subscribe()
except OSError as e:
  restart()

# Create Radar Sensor entity
radarSensor = RadarSensor('P6_5', 'P6_4')

# Publish discovery message for Home Assistant
for entity in discovery_entities.values():
  client.publish(f'{entity["discovery_topic"]}/{entity["conf"]["unique_id"]}/config', json.dumps(entity['conf']))

while True:
  try:
    if not station.isconnected():
        connect_wifi()
    client.check_msg()

    ### Handle sensor updates
    radarSensor.update()
    
    ### Server ping (required for Mosquitto >= 2.0!)
    now = time.time()
    if (now - last_ping) > ping_interval:
        client.ping()
        last_ping = now

    ### Decelerate loop
    time.sleep(0.01)

  except OSError as e:
    print(e)
    restart()