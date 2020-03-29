#!/usr/bin/python3

"""
           Smartport bluetooth client
           
                 Daniel GeA

 License https://www.gnu.org/licenses/gpl-3.0.en.html

"""

__version__ = "0.1"

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.factory import Factory
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.utils import platform
import json
import uuid
#import time
import logging
Builder.load_file('smartportbt_kv.kv')


class Bluetooth2Error(Exception):
        pass


class Bluetooth2():

    def __init__(self, **kwargs):
        if platform  == 'win' or platform  == 'linux' or platform  ==  'macosx':
            import bluetooth
            from bluetooth import BluetoothError
            self.bluetooth = bluetooth
            self.error = BluetoothError
        if platform  == 'android':
            from jnius import JavaException
            from jnius import autoclass
            self.bluetooth = autoclass('android.bluetooth.BluetoothAdapter')
            self.UUID = autoclass('java.util.UUID')
            self.error = JavaException

    def get_bonded_devices(self):
        if platform  == 'android':
            if self.bluetooth.getDefaultAdapter().isEnabled() == False:
                raise Bluetooth2Error(1, 'Bluetooth not enabled')
            return self.bluetooth.getDefaultAdapter().getBondedDevices().toArray()

    def scan_devices(self):
        if platform  == 'win' or platform  == 'linux' or platform  ==  'macosx':
            try:
                devices = self.bluetooth.discover_devices(
                    duration=4,
                    lookup_names=True,
                    flush_cache=True,
                    lookup_class=False)
            except OSError:
                raise Bluetooth2Error(1, 'Bluetooth not enabled')
            return devices

    def connect(self, device):
        if platform  == 'win' or platform  == 'linux' or platform  ==  'macosx':
            port = 1
            self.socket = self.bluetooth.BluetoothSocket(self.bluetooth.RFCOMM)
            try:
                self.socket.connect((device['address'], port))
            except self.error:
                raise Bluetooth2Error(2, 'Couldn\'t connect')
            else:
                self.socket.settimeout(0.1)
                return True
        if platform  == 'android':
            try:
                self.socket = device.createRfcommSocketToServiceRecord(
                    self.UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                self.socket.connect()
            except self.error:
                raise Bluetooth2Error(2, 'Couldn\'t connect')
        return True

    def read(self):
        if platform  == 'win' or platform  == 'linux' or platform  ==  'macosx':
            try:
                c = self.socket.recv(1)
            except self.error:
                raise Bluetooth2Error(3, 'Read timeout')
            return c
        if platform  == 'android':
            if self.socket.getInputStream().available():
                c = [0]
                self.socket.read(c,0,1)
                return c[0].to_bytes(1, 'big')       
            raise Bluetooth2Error(3, 'Read timeout')


class LongpressButton(Button):
    __events__ = ('on_short_press', 'on_long_press',)

    long_press_time = Factory.NumericProperty(1)

    def on_state(self, instance, value):
        if value == 'down':
            lpt = self.long_press_time
            self._clockev = Clock.schedule_once(self._do_long_press, lpt)
        else:
            state = self._clockev.is_triggered
            self._clockev.cancel()
            if state:
                self.dispatch('on_short_press')

    def _do_long_press(self, dt):
        self.dispatch('on_long_press')

    def on_long_press(self, *largs):
        pass

    def on_short_press(self, *largs):
        pass


class ButtonSensor(LongpressButton):
    pass


class ScreenMonitors(Screen):

    def add_monitor(self):
        button = Factory.ButtonList(text='')
        button.uuid = str(uuid.uuid1())
        button.bind(on_long_press=self.show_popup_monitors)
        button.bind(on_short_press=screen_monitors.show_screen_monitor)
        self.ids.list_config.add_widget(button)
        screen_edit_name.origin = button
        screen_edit_name.ids.text_name.text = ''
        config[button.uuid] = monitor
        screen_manager.current = 'screen_edit_name'

    def delete_monitor(self, obj):
        self.ids.list_config.remove_widget(self.popup.origin)
        if self.popup.origin.uuid in config:
            del config[self.popup.origin.uuid]
            store.delete(self.popup.origin.uuid)
        self.popup.dismiss()

    def show_popup_monitors(self, obj):
        popup_list = Factory.PopupMonitors()
        self.popup = popup_list
        popup_list.origin = obj
        popup_list.ids.rename.bind(on_release=self.show_screen_edit_name)
        popup_list.ids.delete.bind(on_release=self.delete_monitor)
        popup_list.open()

    def show_popup_about(self):
        popup_about = Factory.PopupAbout()
        popup_about.open()

    def show_screen_edit_name(self, obj):
        screen_edit_name.origin = self.popup.origin
        screen_edit_name.ids.text_name.text = self.popup.origin.text
        screen_manager.current = 'screen_edit_name'
        self.popup.dismiss()

    def show_screen_monitor(self, obj):
        screen_monitor.uuid = obj.uuid
        screen_monitor.ids.sensor1.sensor_name = config[obj.uuid]['sensor1']['name']
        screen_monitor.ids.sensor1.sensor_unit = config[obj.uuid]['sensor1']['unit']
        screen_monitor.ids.sensor1.sensor_data_id = config[obj.uuid]['sensor1']['data_id']
        screen_monitor.ids.sensor1.sensor_index = config[obj.uuid]['sensor1']['index']
        screen_monitor.ids.sensor1.sensor_id = config[obj.uuid]['sensor1']['sensor_id']
        screen_monitor.ids.sensor2.sensor_name = config[obj.uuid]['sensor2']['name']
        screen_monitor.ids.sensor2.sensor_unit = config[obj.uuid]['sensor2']['unit']
        screen_monitor.ids.sensor2.sensor_data_id = config[obj.uuid]['sensor2']['data_id']
        screen_monitor.ids.sensor2.sensor_index = config[obj.uuid]['sensor2']['index']
        screen_monitor.ids.sensor2.sensor_id = config[obj.uuid]['sensor2']['sensor_id']
        screen_monitor.ids.sensor3.sensor_name = config[obj.uuid]['sensor3']['name']
        screen_monitor.ids.sensor3.sensor_unit = config[obj.uuid]['sensor3']['unit']
        screen_monitor.ids.sensor3.sensor_data_id = config[obj.uuid]['sensor3']['data_id']
        screen_monitor.ids.sensor3.sensor_index = config[obj.uuid]['sensor3']['index']
        screen_monitor.ids.sensor3.sensor_id = config[obj.uuid]['sensor3']['sensor_id']
        screen_monitor.ids.sensor4.sensor_name = config[obj.uuid]['sensor4']['name']
        screen_monitor.ids.sensor4.sensor_unit = config[obj.uuid]['sensor4']['unit']
        screen_monitor.ids.sensor4.sensor_data_id = config[obj.uuid]['sensor4']['data_id']
        screen_monitor.ids.sensor4.sensor_index = config[obj.uuid]['sensor4']['index']
        screen_monitor.ids.sensor4.sensor_id = config[obj.uuid]['sensor4']['sensor_id']
        screen_monitor.ids.sensor5.sensor_name = config[obj.uuid]['sensor5']['name']
        screen_monitor.ids.sensor5.sensor_unit = config[obj.uuid]['sensor5']['unit']
        screen_monitor.ids.sensor5.sensor_data_id = config[obj.uuid]['sensor5']['data_id']
        screen_monitor.ids.sensor5.sensor_index = config[obj.uuid]['sensor5']['index']
        screen_monitor.ids.sensor5.sensor_id = config[obj.uuid]['sensor5']['sensor_id']
        screen_monitor.ids.sensor6.sensor_name = config[obj.uuid]['sensor6']['name']
        screen_monitor.ids.sensor6.sensor_unit = config[obj.uuid]['sensor6']['unit']
        screen_monitor.ids.sensor6.sensor_data_id = config[obj.uuid]['sensor6']['data_id']
        screen_monitor.ids.sensor6.sensor_index = config[obj.uuid]['sensor6']['index']
        screen_monitor.ids.sensor6.sensor_id = config[obj.uuid]['sensor6']['sensor_id']
        screen_monitor.ids.title.title = obj.text
        screen_manager.current = 'screen_monitor'

    def list_bluetooth(self):
        if platform  == 'win' or platform  == 'linux' or platform  ==  'macosx':
            try:
                devices = bt2.scan_devices()
            except Bluetooth2Error as error:
                smartport_app.show_toast(error.args[1])
                return
            screen_list.ids.actionbar.title = 'Available devices'
            for address, name in devices:
                button = Factory.ButtonList(text=name)
                button.device = {'name': name,'address': address}
                button.bind(on_release=self.connect)
                screen_list.ids.list.add_widget(button)
        if platform  == 'android':
            try:
                devices = bt2.get_bonded_devices()
            except Bluetooth2Error as error:
                smartport_app.show_toast(error.args[1])
                return
            screen_list.ids.actionbar.title = 'Paired devices'
            for device in devices:
                button = Factory.ButtonList(text=device.getName())
                button.device = device
                button.bind(on_release=self.connect)
                screen_list.ids.list.add_widget(button)
        screen_list.previous = 'screen_monitors'
        screen_manager.current = 'screen_list'

    def connect(self, instance):
        result = bt2.connect(instance.device)
        if result == True:
            Clock.schedule_interval(read_bluetooth, 1)
            Clock.schedule_interval(screen_monitor.update_sensors, 1)
            if platform  == 'win' or platform  == 'linux' or platform  ==  'macosx':
                config['settings']['bt']['name'] = instance.device['name']
                config['settings']['bt']['address'] = instance.device['address']
            if platform  == 'android':
                config['settings']['bt']['name'] = instance.device.getName()
                config['settings']['bt']['address'] = instance.device.getAddress()
            store['settings'] = config['settings']
            self.ids.image_connection.icon = 'data/circle-green.png'
            screen_manager.current = 'screen_monitors'
        else:
            smartport_app.show_toast('Error bluetooth: ' + result)
            self.ids.image_connection.icon = 'data/circle-red.png'


class ScreenMonitor(Screen):

    def show_screen_monitors(self):
        screen_manager.current = 'screen_monitors'

    def show_screen_edit_sensor(self, obj):
        screen_edit_sensor.sensor = obj
        screen_edit_sensor.sensor_name = obj.sensor_name
        screen_edit_sensor.sensor_id = obj.sensor_id
        screen_edit_sensor.sensor_data_id = obj.sensor_data_id
        screen_edit_sensor.sensor_index = obj.sensor_index
        screen_manager.current = 'screen_edit_sensor'

    def update_sensors(self, ts):
        try:
            self.ids.sensor1.sensor_value = telemetry[self.ids.sensor1.sensor_id][
                self.ids.sensor1.sensor_data_id][self.ids.sensor1.sensor_index]
        except KeyError:
            pass
        try:
            self.ids.sensor2.sensor_value = telemetry[self.ids.sensor2.sensor_id][
                self.ids.sensor2.sensor_data_id][self.ids.sensor2.sensor_index]
        except KeyError:
            pass
        try:
            self.ids.sensor3.sensor_value = telemetry[self.ids.sensor3.sensor_id][
                self.ids.sensor3.sensor_data_id][self.ids.sensor3.sensor_index]
        except KeyError:
            pass
        try:
            self.ids.sensor4.sensor_value = telemetry[self.ids.sensor4.sensor_id][
                self.ids.sensor4.sensor_data_id][self.ids.sensor4.sensor_index]
        except KeyError:
            pass
        try:
            self.ids.sensor5.sensor_value = telemetry[self.ids.sensor5.sensor_id][
                self.ids.sensor5.sensor_data_id][self.ids.sensor5.sensor_index]
        except KeyError:
            pass
        try:
            self.ids.sensor6.sensor_value = telemetry[self.ids.sensor6.sensor_id][
                self.ids.sensor6.sensor_data_id][self.ids.sensor6.sensor_index]
        except KeyError:
            pass


class ScreenEditName(Screen):

    def update_name(self):
        config[self.origin.uuid]['name'] = self.ids.text_name.text
        store[self.origin.uuid] = config[self.origin.uuid]
        self.origin.text = self.ids.text_name.text
        self.ids.text_name.text = ''
        screen_manager.current = 'screen_monitors'

    def cancel_name(self):
        if self.origin.text == '':
            screen_monitors.ids.list_config.remove_widget(self.origin)
            del config[self.origin.uuid]
        screen_manager.current = 'screen_monitors'


class ScreenEditSensor(Screen):

    def show_sensor_list(self):
        screen_list.ids.list.clear_widgets()
        for sensor_id in telemetry.keys():
            if not sensor_id == 'sensor_id':
                for data_id in telemetry[sensor_id].keys():
                    sensor_data = get_sensor_data(data_id)
                    if sensor_data:
                        for index in sensor_data.keys():
                            button = Factory.ButtonList(
                                text=sensor_data[index]['name'])
                            button.sensor_id = sensor_id
                            button.sensor_data_id = data_id
                            button.sensor_index = index
                            button.sensor_unit = sensor_data[index]['unit']
                            button.bind(on_release=self.select_sensor)
                            screen_list.ids.list.add_widget(button)
        screen_list.previous = 'screen_edit_sensor'
        screen_list.ids.actionbar.title = 'Available sensors'
        screen_manager.current = 'screen_list'

    def select_sensor(self, sensor):
        self.sensor_name = sensor.text
        self.sensor_id = sensor.sensor_id
        self.sensor_data_id = sensor.sensor_data_id
        self.sensor_unit = sensor.sensor_unit
        self.sensor_index = sensor.sensor_index
        screen_list.ids.list.clear_widgets()
        screen_manager.current = 'screen_edit_sensor'

    def update_sensor(self):
        config[screen_monitor.uuid][self.sensor.index]['name'] = self.sensor_name
        config[screen_monitor.uuid][self.sensor.index]['sensor_id'] = self.sensor_id
        config[screen_monitor.uuid][self.sensor.index]['data_id'] = self.sensor_data_id
        config[screen_monitor.uuid][self.sensor.index]['unit'] = self.sensor_unit
        config[screen_monitor.uuid][self.sensor.index]['index'] = self.sensor_index
        store[screen_monitor.uuid] = config[screen_monitor.uuid]
        self.sensor.sensor_name = self.sensor_name
        self.sensor.sensor_id = self.sensor_id
        self.sensor.sensor_data_id = self.sensor_data_id
        self.sensor.sensor_unit = self.sensor_unit
        self.sensor.sensor_index = self.sensor_index
        screen_manager.current = 'screen_monitor'

    def show_screen_monitor(self):
        screen_manager.current = 'screen_monitor'


class ScreenList(Screen):

    def previous_screen(self):
        screen_manager.current = self.previous


class SmartportApp(App):

    def show_toast(self, title):
        self.toast = Factory.Toast()
        self.toast.ids.label.text = title
        Clock.schedule_interval(self.close_toast, 3)
        self.toast.open()

    def close_toast(self, obj):
        self.toast.dismiss()

    def build(self):
        return screen_manager


def read_bluetooth(obj):
    data = []
    try:
        while True:
            c = bt2.read()
            if c == 0x7D:
                data.append((int.from_bytes(bt2.read(), 'big')
                            ^ 0x20).to_bytes(1, 'big'))
            else:
                data.append(c)
    except Bluetooth2Error:
        if len(data) == 8:
            crc = 0
            for c in data:
                crc += int.from_bytes(c, "big")
                crc += crc >> 8
                crc &= 0x00FF
            crc = 0xFF - crc
            if crc == 0:
                data_id = int.from_bytes(
                    data[2], "big") << 8 | int.from_bytes(data[1], "big")
                value = int.from_bytes(data[6], "big") << 24 | int.from_bytes(
                    data[5], "big") << 16 | int.from_bytes(data[4], "big") << 8 | int.from_bytes(data[3], "big")
                sensor_data = get_sensor_data(data_id)
                if sensor_data:
                    for key in sensor_data.keys():
                        if telemetry['sensor_id'] not in telemetry:
                            telemetry[telemetry['sensor_id']] = {}
                        if data_id not in telemetry[telemetry['sensor_id']]:
                            telemetry[telemetry['sensor_id']][data_id] = {}
                        telemetry[telemetry['sensor_id']][data_id][key] = (
                            value >> sensor_data[key]['shift']) * sensor_data[key]['mult']
            if len(data) == 2:
                if data[0] == 0x7E:
                    telemetry['sensor_id'] = data[1]

def get_sensor_data(data_id):
    data = {
        range(0x0100, 0x010f): {0: {'name': 'Alt', 'unit': 'm', 'mult': 1, 'shift': 0}},
        range(0x0110, 0x011f): {0: {'name': 'Vario', 'unit': 'm/s', 'mult': 1, 'shift': 0.01}},
        range(0x0200, 0x020f): {0: {'name': 'Curr', 'unit': 'A', 'mult': 0.1, 'shift': 0}},
        range(0x0210, 0x021f): {0: {'name': 'VFAS', 'unit': 'v', 'mult': 0.01, 'shift': 0}},
        range(0x0300, 0x030f): {0: {'name': 'Cell', 'unit': 'v', 'mult': 0.02, 'shift': 0}},
        range(0x0400, 0x040f): {0: {'name': 'Temp1', 'unit': 'C', 'mult': 1, 'shift': 0}},
        range(0x0410, 0x041f): {0: {'name': 'Temp2', 'unit': 'C', 'mult': 1, 'shift': 0}},
        range(0x0500, 0x050f): {0: {'name': 'Rpm', 'unit': 'rpm', 'mult': 1, 'shift': 0}},
        range(0x0600, 0x060f): {0: {'name': 'Fuel', 'unit': '%', 'mult': 0.01, 'shift': 0}},
        range(0x0700, 0x070f): {0: {'name': 'AccX', 'unit': 'g', 'mult': 0.01, 'shift': 0}},
        range(0x0710, 0x071f): {0: {'name': 'AccY', 'unit': 'g', 'mult': 0.01, 'shift': 0}},
        range(0x0720, 0x072f): {0: {'name': 'AccZ', 'unit': 'g', 'mult': 0.01, 'shift': 0}},
        range(0x0800, 0x080f): {0: {'name': 'GPSLong', 'unit': '', 'mult': 0.01, 'shift': 0},
                                1: {'name': 'GPSLat', 'unit': '', 'mult': 0.01, 'shift': 16}},
        range(0x0820, 0x082f): {0: {'name': 'GPSAlt', 'unit': 'm', 'mult': 0.01, 'shift': 0}},
        range(0x0830, 0x083f): {0: {'name': 'GPSSpeed', 'unit': 'kts', 'mult': 0.001, 'shift': 0}},
        range(0x0840, 0x084f): {0: {'name': 'GPSCours', 'unit': 'º', 'mult': 0.01, 'shift': 0}},
        range(0x0850, 0x085f): {0: {'name': 'GPSTime', 'unit': 'g', 'mult': 0.01, 'shift': 0}},
        range(0x0900, 0x090f): {0: {'name': 'A3', 'unit': 'v', 'mult': 0.01, 'shift': 0}},
        range(0x0910, 0x091f): {0: {'name': 'A4', 'unit': 'v', 'mult': 0.01, 'shift': 0}},
        range(0x0a00, 0x0a0f): {0: {'name': 'AirSpeed', 'unit': 'kts', 'mult': 0.01, 'shift': 0}},
        range(0x0b00, 0x0b0f): {0: {'name': 'RboxBatt1', 'unit': 'v', 'mult': 0.001, 'shift': 0}},
        range(0x0b10, 0x0b1f): {0: {'name': 'RboxBatt2', 'unit': 'v', 'mult': 0.001, 'shift': 0}},
        range(0x0b20, 0x0b2f): {0: {'name': 'RboxState', 'unit': '', 'mult': 0.01, 'shift': 0}},
        range(0x0b30, 0x0b3f): {0: {'name': 'RboxCons', 'unit': 'mAh', 'mult': 1, 'shift': 0}},
        range(0x0b50, 0x0b5f): {0: {'name': 'EscV', 'unit': 'v', 'mult': 0.01, 'shift': 0},
                                1: {'name': 'EscA', 'unit': 'A', 'mult': 0.01, 'shift': 16}},
        range(0x0b60, 0x0b6f): {0: {'name': 'EscRpm', 'unit': 'rpm', 'mult': 100, 'shift': 0},
                                1: {'name': 'EscCons', 'unit': 'mAh', 'mult': 1, 'shift': 0}},
        range(0x0d00, 0x0d0f): {0: {'name': 'GassuitT1', 'unit': 'C', 'mult': 1, 'shift': 0}},
        range(0x0d10, 0x0d1f): {0: {'name': 'GassuitT2', 'unit': 'C', 'mult': 1, 'shift': 0}},
        range(0x0d20, 0x0d2f): {0: {'name': 'GassuitSpeed', 'unit': 'rpm', 'mult': 1, 'shift': 0}},
        range(0x0d30, 0x0d3f): {0: {'name': 'GassuitResVol', 'unit': 'ml', 'mult': 1, 'shift': 0}},
        range(0x0d40, 0x0d4f): {0: {'name': 'GassuitPerc', 'unit': '%', 'mult': 1, 'shift': 0}},

        range(0x0d50, 0x0d5f): {0: {'name': 'GassuitFlow', 'unit': '%', 'mult': 1, 'shift': 0}},
        range(0x0d60, 0x0d6f): {0: {'name': 'GassuitMaxFlow', 'unit': '%', 'mult': 1, 'shift': 0}},
        range(0x0d70, 0x0d7f): {0: {'name': 'GassuitAvgFlow', 'unit': '%', 'mult': 1, 'shift': 0}},
        range(0x0e50, 0x0e5f): {0: {'name': 'SBecV', 'unit': 'v', 'mult': 0.01, 'shift': 0},
                                1: {'name': 'SBecA', 'unit': 'A', 'mult': 0.01, 'shift': 16}},
        range(0xf101, 0xf102): {0: {'name': 'RSSI', 'unit': '', 'mult': 1, 'shift': 0}},
        range(0xf102, 0xf103): {0: {'name': 'A1', 'unit': 'v', 'mult': 0.1, 'shift': 0}},
        range(0xf103, 0xf104): {0: {'name': 'A2', 'unit': 'v', 'mult': 0.1, 'shift': 0}},
        range(0xf104, 0xf105): {0: {'name': 'RXBT', 'unit': 'v', 'mult': 0.1, 'shift': 0}},
        range(0xf105, 0xf106): {0: {'name': 'RAS', 'unit': '%', 'mult': 1, 'shift': 0}},
        range(0x0a10, 0x0a1f): {0: {'name': 'FuelQty', 'unit': 'ml', 'mult': 0.01, 'shift': 0}},
    }

    for key in data:
        if data_id in key:
            return data[key]


smartport_app = SmartportApp(title='Smartport BT')
telemetry = {}
telemetry['sensor_id'] = 0
bt = {
    'name': '',
    'address': ''
}
settings = {
    'bt': bt
}
sensor = {
    'name': '',
    'sensor_id': 0,
    'data_id': 0,
    'index': 0,
    'unit': ''
}
monitor = {
    'type': 'monitor',
    'name': '',
    'sensor1': sensor,
    'sensor2': sensor,
    'sensor3': sensor,
    'sensor4': sensor,
    'sensor5': sensor,
    'sensor6': sensor
}
config = {
    'settings': settings
}

screen_manager = ScreenManager()
screen_monitors = ScreenMonitors(name='screen_monitors')
screen_edit_name = ScreenEditName(name='screen_edit_name')
screen_edit_sensor = ScreenEditSensor(name='screen_edit_sensor')
screen_monitor = ScreenMonitor(name='screen_monitor')
screen_list = ScreenList(name='screen_list')
screen_manager.add_widget(screen_monitors)
screen_manager.add_widget(screen_edit_name)
screen_manager.add_widget(screen_edit_sensor)
screen_manager.add_widget(screen_list)
screen_manager.add_widget(screen_monitor)
screen_manager.current = 'screen_monitors'

store = JsonStore('smartport.json')
for element in store.keys():
    config[element] = store[element]
    if 'type' in config[element]:
        if config[element]['type'] == 'monitor':
            button = Factory.ButtonList(text=config[element]['name'])
            button.uuid = element
            button.bind(on_long_press=screen_monitors.show_popup_monitors)
            button.bind(on_short_press=screen_monitors.show_screen_monitor)
            screen_monitors.ids.list_config.add_widget(button)

bt2 = Bluetooth2()

smartport_app.run()