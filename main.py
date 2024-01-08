import machine
import ubinascii
import network
import time
import json

from umqttsimple import MQTTClient
import secrets

### WIFI SETUP
ssid = secrets.ssid
password = secrets.password

### MQTT SETUP
mqtt_server = secrets.mqtt_server
client_id = ubinascii.hexlify(machine.unique_id()).decode()
cid = client_id[-2:]

msg_interval_usual = 180 # Usual update interval
msg_interval_fast = 2 # Update interval during movement
ping_interval = 60
sleep_timer = 3600

message_interval = msg_interval_usual # Do not change this
last_message = -message_interval
last_ping = 0

### Home Assistant Auto Discovery setup
### Reference: https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery

discovery_prefix = 'homeassistant'
node_id = f'motion_sensor_{client_id}'

discovery_device = {
  "name":f"Motion Sensor {cid}",
  "identifiers": node_id,
  "manufacturer": 'Infineon',
  "model": 'PSoC6',
  "sw_version": '0.1.0'
  }

discovery_entities = [
    {
        'discovery_topic':f'{discovery_prefix}/button/{node_id}',
        'conf': {
            "name":"Identify",
            "unique_id":"identify",
            "icon":"mdi:button-pointer",
            "entity_category":"config",
            "command_topic":f'{discovery_prefix}/button/{node_id}/command/identify',
            "payload_press":"ON",
            "device": discovery_device
            }
        },
    {
        'discovery_topic':f'{discovery_prefix}/binary_sensor/{node_id}',
        'conf': {
            "name":"User Button",
            "unique_id":"userbutton",
            "state_topic":f'{discovery_prefix}/binary_sensor/{node_id}/state/button',
            "device": discovery_device
            }
        }
    ]

class Button:
  def __init__(self, pin):
    self._pin = pin
    self._isPressed = False
    self._btn = machine.Pin(self._pin, machine.Pin.IN, machine.Pin.PULL_UP)
  def read(self):
    return not self._btn.value()
  def event(self):
    if self.read() and not self._isPressed:
      self._isPressed = True
      return 'ON'
    if not self.read() and self._isPressed:
      self._isPressed = False
      return 'OFF'
    return False

class Device:
  def __init__(self, userLedPin):
    self._userLed = machine.Pin(userLedPin, machine.Pin.OUT)
  def identify(self):
    self._userLed.on()
    time.sleep(1)
    self._userLed.off()
  def loop(self):
    e = button.event()
    if e:
      client.publish(discovery_entities[1]['conf']['state_topic'], e)


def connect_wifi():
  global ssid, password
    
  station.active(False)
  time.sleep(0.1)
  station.active(True)
  station.connect(ssid, password)

  ### Wait to connect to WiFi (with timeout)
  counter = 0
  while not station.isconnected():
    time.sleep(2)
    if counter > 20:
      machine.reset()
    counter = counter+1
  
  print('Connection successful')
  print(station.ifconfig())

def mqtt_sub_cb(topic, msg):
  global msg_interval_fast, msg_interval_usual, message_interval
  topic = topic.decode('ascii')
  msg = msg.decode('ascii')
  print((topic, msg))
  if topic == discovery_entities[0]['conf']['command_topic']:
    if msg == 'ON':
      device.identify()

def connect_and_subscribe():
  global client_id, mqtt_server

  client = MQTTClient(client_id, mqtt_server, user=secrets.mqtt_user, password=secrets.mqtt_password, keepalive=ping_interval+30)
  client.set_callback(mqtt_sub_cb)
  client.connect()
  client.subscribe( discovery_entities[0]['conf']['command_topic'] )
  
  print('Connected to MQTT broker')
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Restarting...')
  machine.reset()

station = network.WLAN(network.STA_IF)

button = Button('P0_4')
device = Device('P13_7')

connect_wifi()

try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()

# Publish discovery message for Home Assistant
for entity in discovery_entities:
  client.publish(f'{entity["discovery_topic"]}/{entity["conf"]["unique_id"]}/config', json.dumps(entity['conf']))

while True:
  try:
    if not station.isconnected():
        connect_wifi()
    client.check_msg()

    ### Handle device specific stuff in device loop
    device.loop()
    
    now = time.time()
    ### Server ping (required for Mosquitto >= 2.0!)
    if (now - last_ping) > ping_interval:
        client.ping()
        last_ping = now

    ### Decelerate loop
    time.sleep(0.01)

  except OSError as e:
    print(e)
    restart_and_reconnect()