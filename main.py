import time
import sys
import json
import ble2
import config

if config.get_config('bleDevice')['bleDevice'] == 1:
    # Import Receiver for nRF module
    from beaconscanner import BeaconReceiver
else:
    # Import bluez scanner
    from beaconscanner import BeaconScanner

mqttEnabled = config.get_config('endpoints')['mqttEnabled']
httpEnabled = config.get_config('endpoints')['httpEnabled']
influxEnabled = config.get_config('endpoints')['influxEnabled']

if mqttEnabled:
    import ble2mqtt
if httpEnabled:
    import ble2http
if influxEnabled:
    import ble2influx

mFen = config.get_config('filters')['macFilterEnabled']
if mFen:
    mF = config.get_config('filters')['macFilter']

def callback(bt_addr, rssi, packet, dec, smoothedRSSI):
    if mFen == True:
        for i in mF:
            if str.upper(i) == bt_addr:
                if mqttEnabled:
                    ble2mqtt.send_bt(bt_addr, json.dumps(ble2.ble_message\
                        (bt_addr, rssi, packet, dec, smoothedRSSI)))
    else:
        if mqttEnabled:
            ble2mqtt.send_bt(bt_addr, json.dumps(ble2.ble_message\
                (bt_addr, rssi, packet, dec, smoothedRSSI)))
   

def main_loop():
    RSSIen = config.get_config('filters')['rssiThreshold']
    if (RSSIen):
        RSSI = config.get_config('filters')['rssi']
    else:
        RSSI = -999
    
    ble2mqtt.MQTT()
    global scanner
    f = config.get_config('filters')
    if config.get_config('bleDevice')['bleDevice'] == 1:
        scanner = BeaconReceiver(callback, config.get_config('bleDevice')['serialPort'], \
                                config.get_config('bleDevice')['baudrate'], \
                                config.get_config('bleDevice')['timeout'],\
                                rssiThreshold=RSSI,\
                                ruuvi=f['ruuvi'], ruuviPlus=f['ruuviPlus'], \
                                eddystone=f['eddystone'], ibeacon=f['ibeacon'], unknown=f['unknown'])
    else:
        scanner = BeaconScanner(callback, rssiThreshold=RSSI,\
                                ruuvi=f['ruuvi'], ruuviPlus=f['ruuviPlus'], \
                                eddystone=f['eddystone'], ibeacon=f['ibeacon'], unknown=f['unknown'])
    scanner.start()
    while True:
        if config.get_config('bleDevice')['bleDevice'] == 1:
            time.sleep(30)
            ble2mqtt.heartbeat()
        else:
            time.sleep(30)
            scanner._mon.toggle_scan(False)
            ble2mqtt.heartbeat()
            scanner._mon.toggle_scan(True)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        scanner.stop()
        ble2mqtt.end()
        print("\nExiting application\n")
        sys.exit(0)
