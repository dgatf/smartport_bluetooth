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
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.factory import Factory
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.utils import platform
from plyer import tts
from functools import partial
import threading
import re # floatinput
import struct
import json
import uuid
import time
import logging
Builder.load_file('smartportbt_kv.kv')

if platform == 'win' or platform == 'linux' or platform == 'macosx':
    import bluetooth
if platform == 'linux':
    from gattlib import DiscoveryService, GATTRequester, GATTResponse
if platform == 'android':
    from jnius import autoclass
    bluetooth = autoclass('android.bluetooth.BluetoothAdapter')
    UUID = autoclass('java.util.UUID')

class FloatInput(TextInput):

    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)


class BluetoothExtendedError(Exception):
    pass


if platform == 'linux':
    class DeviceBle(GATTRequester):

        """def __init__(self, address, **kwargs):
            self.del_buffer = False
            self.buffer = bytearray(0)"""

        def init(self):
            self.del_buffer = False
            self.buffer = bytearray(0)
        
        def on_notification(self, handle, data):
            if self.del_buffer:
                self.buffer = bytearray(0)
                self.del_buffer = False
            self.buffer += data[3:len(data)]


class BluetoothExtended():

    def __init__(self, **kwargs):
        self.isConnected = False 
        self.root = True       

    def get_bonded_devices(self):
        if platform == 'android':
            if bluetooth.getDefaultAdapter().isEnabled() == False:
                raise BluetoothExtendedError(1, 'Bluetooth not enabled')
            return bluetooth.getDefaultAdapter().getBondedDevices().toArray()

    def scan_devices(self):
        if platform == 'win' or platform == 'linux' or platform == 'macosx':
            root = True
            devices = {'classic': [], 'ble': []}
            # bt classic
            try:
                devices['classic'] = bluetooth.discover_devices(
                    duration=4,
                    lookup_names=True,
                    flush_cache=True,
                    lookup_class=False)
            except OSError as error:
                if error.args[0] == 19:
                    raise BluetoothExtendedError(1, 'Bluetooth not enabled')
                else:
                    raise BluetoothExtendedError(
                        10, 'Unknown error: ' + error.args[1])
                return
            # bt ble
            if platform == 'linux':
                service = DiscoveryService("hci0")
                try:
                    devices_ble = service.discover(2)
                except RuntimeError as error:
                    root = False
                else:
                    for key in devices_ble:
                        devices['ble'].append((key, devices_ble[key]))
            return devices, root

    def connect(self, address, type):
        if platform == 'win' or platform == 'linux' or platform == 'macosx':
            if type == 'classic':
                port = 1
                self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                try:
                    self.socket.connect((address, port))
                except bluetooth.btcommon.BluetoothError as error:
                    if error.args[0] == 112:
                        raise BluetoothExtendedError(2, 'Couldn\'t connect')
                    else:
                        raise BluetoothExtendedError(
                            10, 'Unknown error: ' + error.args[1])
                else:
                    self.type = 'classic'
                    self.isConnected = True
                    return
            if type == 'ble' and platform == 'linux':
                self.type = 'ble'
                self.device = DeviceBle(address)
                self.device.init()
                self.isConnected = True
                return
        if platform == 'android':
            devices = bluetooth.getDefaultAdapter().getBondedDevices().toArray()
            if not bluetooth.getDefaultAdapter().isEnabled():
                raise BluetoothExtendedError(5, 'Bluetooth not available')
            for device in devices:
                logging.info('{} {}'.format(device.getType(), device.getName()))
                if device.getAddress() == address:
                    logging.info('Connecting')
                    if device.getType() == 1:
                        try:
                            self.socket = device.createRfcommSocketToServiceRecord(
                                UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                            self.socket.connect()
                        except Exception as error:
                            logging.info(error.args)
                            raise BluetoothExtendedError(2, 'Couldn\'t connect')
                        else:
                            self.isConnected = True
                            return
                    if device.getType() == 2:
                        raise BluetoothExtendedError(5, 'BLE not implemented')
                        # bluetoothGatt = device.connectGatt(this, False, gattCallback)
        raise BluetoothExtendedError(2, 'Couldn\'t connect')

    #def gattCallback(self):
    #    pass


    def disconnect(self):
        self.socket.close()
        self.isConnected = False

    def read(self, lenght):
        if platform == 'win' or platform == 'linux' or platform == 'macosx':
            if self.type == 'classic':
                buffer = bytearray(0) 
                try:
                    buffer = self.socket.recv(20)
                except bluetooth.btcommon.BluetoothError as error:
                    if error.args[0] == 'timed out':
                        raise BluetoothExtendedError(3, 'Read timeout')
                    if error.args[0] == 103:
                        raise BluetoothExtendedError(4, 'Software disconnection')
                    if error.args[0] == 11:
                        raise BluetoothExtendedError(5, 'Bluetooth not available')
                    else:
                        raise BluetoothExtendedError(
                            10, 'Unknown error: ' + str(error.args))
                return buffer
            if self.type == 'ble':
                if self.device.del_buffer == False:
                    self.device.del_buffer = True
                    return self.device.buffer
                return bytearray(0)
        if platform == 'android':
            buffer = [0] * 20
            lenght = self.socket.read(buffer, 0, 20)
            return bytearray(buffer[0:lenght])


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
        for cont in range(1, 7):
            index = 'sensor' + str(cont)
            screen_monitor.ids[index].sensor_name = config[obj.uuid][index]['name']
            screen_monitor.ids[index].sensor_unit = config[obj.uuid][index]['unit']
            screen_monitor.ids[index].sensor_data_id = config[obj.uuid][index]['data_id']
            screen_monitor.ids[index].sensor_index = config[obj.uuid][index]['index']
            screen_monitor.ids[index].sensor_id = config[obj.uuid][index]['sensor_id']
        screen_monitor.ids.title.title = obj.text
        screen_manager.current = 'screen_monitor'

    def connect(self):
        if bluetooth_extended.isConnected:
            try:
                self.timer_read.cancel()
                self.timer_update.cancel()
            except:
                pass
            bluetooth_extended.disconnect()
            self.ids.image_connection.icon = 'data/circle-red.png'
            self.ids.button_connection.text = 'Connect'
        else:
            try:
                bluetooth_extended.connect(config['settings']['bt']['address'], config['settings']['bt']['type'])
            except BluetoothExtendedError as error:
                Clock.schedule_once(partial(smartport_app.show_toast, error.args[1]), 1)
            except KeyError:
                smartport_app.show_toast('Select bluetooth device')
            else:
                self.timer_read = Clock.schedule_interval(read_bluetooth, 0.01)
                self.timer_update = Clock.schedule_interval(
                    screen_monitor.update_sensors, 0.02)
                self.ids.image_connection.icon = 'data/circle-green.png'
                self.ids.button_connection.text = 'Disconnect'
                screen_manager.current = 'screen_monitors'

    def show_screen_settings(self):
        try:
            screen_settings.ids.device.text = config['settings']['bt']['name']
        except Exception as e:
            print(e.args)
        screen_manager.current = 'screen_settings'


class ScreenSettings(Screen):
    
    def list_bluetooth(self):
        screen_list.ids.list.clear_widgets()
        if platform == 'win' or platform == 'linux' or platform == 'macosx':
            try:
                devices, root = bluetooth_extended.scan_devices()
            except BluetoothExtendedError as error:
                Clock.schedule_once(partial(smartport_app.show_toast, error.args[1]), 1)
                return
            screen_list.ids.actionbar.title = 'Available devices'
            screen_list.previous = 'screen_settings'
            screen_manager.current = 'screen_list'
            if root == False:
                Clock.schedule_once(partial(smartport_app.show_toast, 'Run as administrator to scan for ble devices'), 1)
            for key in devices:
                for address, name in devices[key]:
                    button = Factory.ButtonList(text=name or address)
                    button.device_name = name
                    button.device_address = address
                    button.device_type = key
                    button.bind(on_release=self.select_device)
                    screen_list.ids.list.add_widget(button)
        if platform == 'android':
            try:
                devices = bluetooth_extended.get_bonded_devices()
            except BluetoothExtendedError as error:
                smartport_app.show_toast(error.args[1])
                return
            screen_list.ids.actionbar.title = 'Paired devices'
            screen_list.previous = 'screen_settings'
            screen_manager.current = 'screen_list'
            for device in devices:
                button = Factory.ButtonList(text=device.getName())
                button.device_name = device.getName()
                button.device_address = device.getAddress()
                button.device_type = 'android'
                button.bind(on_release=self.select_device)
                screen_list.ids.list.add_widget(button)

    def select_device(self, instance):
        self.ids.device.device_name = instance.device_name
        self.ids.device.device_address = instance.device_address
        self.ids.device.device_type = instance.device_type
        self.ids.device.text = instance.device_name
        screen_list.ids.list.clear_widgets()
        screen_manager.current = 'screen_settings'

    def update_settings(self):
        try:
            config['settings']['bt']['name'] = self.ids.device.device_name
            config['settings']['bt']['address'] = self.ids.device.device_address
            config['settings']['bt']['type'] = self.ids.device.device_type
        except:
            pass
        store['settings'] = config['settings']
        screen_manager.current = 'screen_monitors'

    def show_screen_monitors(self):
        screen_manager.current = 'screen_monitors'


class ScreenMonitor(Screen):

    def show_screen_monitors(self):
        screen_manager.current = 'screen_monitors'

    def show_screen_edit_sensor(self, obj):
        screen_edit_sensor.sensor = obj
        screen_edit_sensor.sensor_name = obj.sensor_name
        screen_edit_sensor.sensor_id = obj.sensor_id
        screen_edit_sensor.sensor_data_id = obj.sensor_data_id
        screen_edit_sensor.sensor_index = obj.sensor_index
        screen_edit_sensor.sensor_unit = obj.sensor_unit
        screen_edit_sensor.ids.multiplier.text = str(
            config[self.uuid][obj.index]['multiplier'])
        if obj.sensor_index == 2:
            if config[screen_monitor.uuid][obj.index]['value'] == 'sum':
                screen_edit_sensor.ids.sum.state = 'down'
            if config[screen_monitor.uuid][obj.index]['value'] == 'max':
                screen_edit_sensor.ids.max.state = 'down'
            if config[screen_monitor.uuid][obj.index]['value'] == 'min':
                screen_edit_sensor.ids.min.state = 'down'
            if config[screen_monitor.uuid][obj.index]['value'] == 'delta':
                screen_edit_sensor.ids.delta.state = 'down'
        screen_edit_sensor.ids.alarm_check.active = config[self.uuid][obj.index]['alarm']
        if config[self.uuid][obj.index]['alarm_condition'] == 'lower':
            screen_edit_sensor.ids.lower.state = 'down'
        if config[self.uuid][obj.index]['alarm_condition'] == 'equal':
            screen_edit_sensor.ids.equal.state = 'down'
        if config[self.uuid][obj.index]['alarm_condition'] == 'higher':
            screen_edit_sensor.ids.higher.state = 'down'
        screen_edit_sensor.ids.alarm_interval.text = str(
            config[self.uuid][obj.index]['alarm_interval'])
        screen_edit_sensor.ids.alarm_value.text = str(
            config[self.uuid][obj.index]['alarm_value'])
        screen_edit_sensor.ids.alarm_text.text = config[self.uuid][obj.index]['alarm_text']
        obj.background_color = [1, 1, 1, 1]
        screen_manager.current = 'screen_edit_sensor'

    def update_sensors(self, ts):
        if self.uuid in config:
            for cont in range(1, 7):
                update = False
                button_index = 'sensor' + str(cont)
                if config[self.uuid][button_index]['index'] == 2:
                    try:
                        cells = telemetry[config[self.uuid][button_index]['sensor_id']
                                          ][config[self.uuid][button_index]['data_id']][2]
                    except KeyError:
                        pass
                    else:
                        update = True
                        sum = 0.0
                        max = 0.0
                        min = 10.0
                        for key in cells.keys():
                            if config[self.uuid][button_index]['value'] == 'sum':
                                sum += cells[key]
                            if config[self.uuid][button_index]['value'] == 'max' or config[self.uuid][button_index]['value'] == 'delta':
                                if cells[key] > max:
                                    max = cells[key]
                            if config[self.uuid][button_index]['value'] == 'min' or config[self.uuid][button_index]['value'] == 'delta':
                                if cells[key] < min and cells[key] > 0:
                                    min = cells[key]
                        if config[self.uuid][button_index]['value'] == 'sum':
                            value = sum
                        if config[self.uuid][button_index]['value'] == 'min':
                            value = min
                        if config[self.uuid][button_index]['value'] == 'max':
                            value = max
                        if config[self.uuid][button_index]['value'] == 'delta':
                            value = max-min
                        value = float('{:.2f}'.format(value))
                elif config[self.uuid][button_index]['index'] == 0 or config[self.uuid][button_index]['index'] == 1:
                    try:
                        value = telemetry[config[self.uuid][button_index]['sensor_id']][config[self.uuid][button_index]
                                                                                        ['data_id']][config[self.uuid][button_index]['index']] * config[self.uuid][button_index]['multiplier']
                    except KeyError:
                        pass
                    else:
                        value = float('{:.2f}'.format(value))
                        update = True
                if update:  # update text and alarm
                    self.ids[button_index].sensor_value = value
                    if config[self.uuid][button_index]['alarm']:
                        condition = {'higher': config[self.uuid][button_index]['alarm_condition'] == 'higher' and self.ids[button_index].sensor_value > config[uuid][button_index]['alarm_value'],
                                     'equal': config[self.uuid][button_index]['alarm_condition'] == 'equal' and self.ids[button_index].sensor_value == config[self.uuid][button_index]['alarm_value'],
                                     'lower': config[self.uuid][button_index]['alarm_condition'] == 'lower' and self.ids[button_index].sensor_value < config[self.uuid][button_index]['alarm_value']
                                     }
                        if condition['higher'] or condition['equal'] or condition['lower']:
                            try:
                                screen_monitor.ids[button_index].alarm_voice.is_triggered
                            except AttributeError:
                                screen_monitor.ids[button_index].alarm_voice = Clock.create_trigger(
                                    screen_monitor.alarms, config[screen_monitor.uuid][button_index]['alarm_interval'])
                            try:
                                screen_monitor.ids[button_index].alarm_blink.is_triggered
                            except AttributeError:
                                screen_monitor.ids[button_index].alarm_blink = Clock.create_trigger(
                                    screen_monitor.alarms, 0.5)
                            if not screen_monitor.ids[button_index].alarm_voice.is_triggered:
                                screen_monitor.ids[button_index].alarm_voice()
                                global text_voice
                                text_voice = config[self.uuid][button_index]['alarm_text']
                                text_voice = text_voice.replace(
                                    '%s', config[self.uuid][button_index]['name'])
                                text_voice = text_voice.replace(
                                    '%v', str(value))
                                text_voice = text_voice.replace(
                                    '%u', config[self.uuid][button_index]['unit'])
                                event_voice.set()
                            if not screen_monitor.ids[button_index].alarm_blink.is_triggered:
                                screen_monitor.ids[button_index].alarm_blink()
                                color = self.ids[button_index].background_color
                                self.ids[button_index].background_color = (
                                    1, int(not color[1]), int(not color[2]), 1)
                        else:
                            self.ids[button_index].background_color = [
                                1, 1, 1, 1]

    def alarms(self, interval):
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
        button = Factory.ButtonList(text='')
        button.sensor_id = 0
        button.sensor_data_id = 0
        button.sensor_index = 0
        button.sensor_unit = ''
        button.bind(on_release=self.select_sensor)
        screen_list.ids.list.add_widget(button)
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
        config[screen_monitor.uuid][self.sensor.index]['multiplier'] = float(
            self.ids.multiplier.text)
        if config[screen_monitor.uuid][self.sensor.index]['index'] == 2:
            if self.ids.sum.state == 'down':
                config[screen_monitor.uuid][self.sensor.index]['value'] = 'sum'
            if self.ids.max.state == 'down':
                config[screen_monitor.uuid][self.sensor.index]['value'] = 'max'
            if self.ids.min.state == 'down':
                config[screen_monitor.uuid][self.sensor.index]['value'] = 'min'
            if self.ids.delta.state == 'down':
                config[screen_monitor.uuid][self.sensor.index]['value'] = 'delta'
        config[screen_monitor.uuid][self.sensor.index]['alarm'] = self.ids.alarm_check.active
        if self.ids.lower.state == 'down':
            config[screen_monitor.uuid][self.sensor.index]['alarm_condition'] = 'lower'
        if self.ids.equal.state == 'down':
            config[screen_monitor.uuid][self.sensor.index]['alarm_condition'] = 'equal'
        if self.ids.higher.state == 'down':
            config[screen_monitor.uuid][self.sensor.index]['alarm_condition'] = 'higher'
        try:
            config[screen_monitor.uuid][self.sensor.index]['alarm_interval'] = int(
                self.ids.alarm_interval.text)
        except ValueError:
            config[screen_monitor.uuid][self.sensor.index]['alarm_interval'] = 15
        screen_monitor.ids[self.sensor.index].alarm_voice = Clock.create_trigger(
            screen_monitor.alarms, config[screen_monitor.uuid][self.sensor.index]['alarm_interval'])
        screen_monitor.ids[self.sensor.index].alarm_blink = Clock.create_trigger(
            screen_monitor.alarms, 0.5)
        try:
            config[screen_monitor.uuid][self.sensor.index]['alarm_value'] = int(
                self.ids.alarm_value.text)
        except ValueError:
            config[screen_monitor.uuid][self.sensor.index]['alarm_value'] = 0
        config[screen_monitor.uuid][self.sensor.index]['alarm_text'] = self.ids.alarm_text.text
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

    def show_toast(self, message, *args):
        self.toast = Factory.Toast()
        self.toast.ids.label.text = message
        Clock.schedule_interval(self.close_toast, 3)
        self.toast.open()

    def close_toast(self, obj):
        self.toast.dismiss()

    def build(self):
        return screen_manager


def check_crc(packet):
    crc = 0
    for c in range(2, 10):
        crc += packet[c]
        crc += crc >> 8
        crc &= 0x00FF
    crc = 0xFF - crc
    if crc == 0:
        return True
    return False


def add_telemetry(packet):
    sensor_id = packet[1]
    frame_id = packet[2]
    data_id = packet[4] << 8 | packet[3]
    value = packet[8] << 8 << 24 | packet[7] << 16 | packet[6] << 8 | packet[5]
    if frame_id == 0x10:
        sensor_data = get_sensor_data(data_id)
        # logging.info('data: {} {} {} {}'.format(sensor_id, frame_id, data_id, value))
        if sensor_data:
            for key in sensor_data.keys():
                if sensor_id not in telemetry:
                    telemetry[sensor_id] = {}
                if data_id not in telemetry[sensor_id]:
                    if key == 2:
                        telemetry[sensor_id][data_id] = {2: {}}
                    else:
                        telemetry[sensor_id][data_id] = {}
                if key == 2:
                    telemetry[sensor_id][data_id][2][value & 0x0000000F] = (
                        (value & 0x000FFF00) >> 8) * sensor_data[2]['mult']
                    telemetry[sensor_id][data_id][2][(
                        value & 0x0000000F) + 1] = (value >> 20) * sensor_data[2]['mult']
                elif key == 0:
                    telemetry[sensor_id][data_id][0] = (
                        value & 0x0000FFFF) * sensor_data[key]['mult']
                elif key == 1:
                    telemetry[sensor_id][data_id][1] = (
                        value >> 16) * sensor_data[key]['mult']
            # logging.info('telemetry: {}'.format(telemetry))


def read_bluetooth(obj):
    try:
        buffer = bluetooth_extended.read(20)
    except BluetoothExtendedError as error:
        if error.args[0] == 4 or error.args[0] == 5:
            smartport_app.show_toast(error.args[1])
            screen_monitors.timer_read.cancel()
            screen_monitors.timer_update.cancel()
            bluetooth_extended.disconnect()
            screen_monitors.ids.image_connection.icon = 'data/circle-red.png'
            screen_monitors.ids.button_connection.text = 'Connect'
        if error.args[0] == 10:
            raise error
    else:
        global packet
        for i in range(len(buffer)):
            if buffer[i] == 0x7E:
                packet = [0x7E]
            elif len(packet) > 0:
                if buffer[i] == 0x7D:
                    i += 1
                    packet.append(buffer[i] ^ 0x20)
                else:
                    packet.append(buffer[i])
                if len(packet) == 10:
                    if check_crc(packet):
                        add_telemetry(packet)
                    packet = []


def get_sensor_data(data_id):
    data = {
        range(0x0100, 0x010f): {0: {'name': 'Alt', 'unit': 'm', 'mult': 1, 'shift': 0}},
        range(0x0110, 0x011f): {0: {'name': 'Vario', 'unit': 'm/s', 'mult': 1, 'shift': 0.01}},
        range(0x0200, 0x020f): {0: {'name': 'Curr', 'unit': 'A', 'mult': 0.1, 'shift': 0}},
        range(0x0210, 0x021f): {0: {'name': 'VFAS', 'unit': 'v', 'mult': 0.01, 'shift': 0}},
        range(0x0300, 0x030f): {2: {'name': 'Cell', 'unit': 'v', 'mult': 0.002, 'shift': 0}},
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
        range(0x0840, 0x084f): {0: {'name': 'GPSCours', 'unit': '\xf8', 'mult': 0.01, 'shift': 0}},
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


def do_speak(event_voice):
    global text_voice
    while True:
        event_voice.wait()
        tts.speak(text_voice)
        event_voice.clear()


def hide_widget(wid, dohide=True):
    if hasattr(wid, 'saved_attrs'):
        if not dohide:
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs
            del wid.saved_attrs
    elif dohide:
        wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
        wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True


text_voice = ''
smartport_app = SmartportApp(title='Smartport BT')
# config = {<uuid>:{type:<>, name:<>, sensor1:{name:<>,sensor_id:<>,data_id:<>,index:<>,unit:<>,alarm:<>,condition:<>...}
#          settings:{bt{name:<>,address:<>}}}
# telemetry = {<sensorId>: {<dataId>: {<index>: <value>, <index>: <value>}}}
telemetry = {}
telemetry['sensor_id'] = 0
bt = {
    'name': '',
    'address': '',
    'type': ''
}
settings = {
    'bt': bt
}
sensor = {
    'name': '',
    'sensor_id': 0,
    'data_id': 0,
    'index': 0,
    'unit': '',
    'multiplier': 1,
    'alarm': False,
    'alarm_condition': '',
    'alarm_interval': 0,
    'alarm_value': 0,
    'alarm_text': ''
}
monitor = {
    'type': 'monitor',
    'name': '',
    'sensor1': {
        'name': '',
        'sensor_id': 0,
        'data_id': 0,
        'index': 0,
        'unit': '',
        'multiplier': 1.0,
        'alarm': False,
        'alarm_condition': 'lower',
        'alarm_interval': 0,
        'alarm_value': 0,
        'alarm_text': ''
    },
    'sensor2': {
        'name': '',
        'sensor_id': 0,
        'data_id': 0,
        'index': 0,
        'unit': '',
        'multiplier': 1.0,
        'alarm': False,
        'alarm_condition': 'lower',
        'alarm_interval': 0,
        'alarm_value': 0,
        'alarm_text': ''
    },
    'sensor3': {
        'name': '',
        'sensor_id': 0,
        'data_id': 0,
        'index': 0,
        'unit': '',
        'multiplier': 1.0,
        'alarm': False,
        'alarm_condition': 'lower',
        'alarm_interval': 0,
        'alarm_value': 0,
        'alarm_text': ''
    },
    'sensor4': {
        'name': '',
        'sensor_id': 0,
        'data_id': 0,
        'index': 0,
        'unit': '',
        'multiplier': 1.0,
        'alarm': False,
        'alarm_condition': 'lower',
        'alarm_interval': 0,
        'alarm_value': 0,
        'alarm_text': ''
    },
    'sensor5': {
        'name': '',
        'sensor_id': 0,
        'data_id': 0,
        'index': 0,
        'unit': '',
        'multiplier': 1.0,
        'alarm': False,
        'alarm_condition': 'lower',
        'alarm_interval': 0,
        'alarm_value': 0,
        'alarm_text': ''
    },
    'sensor6': {
        'name': '',
        'sensor_id': 0,
        'data_id': 0,
        'index': 0,
        'unit': '',
        'multiplier': 1.0,
        'alarm': False,
        'alarm_condition': 'lower',
        'alarm_interval': 0,
        'alarm_value': 0,
        'alarm_text': ''
    }
}
config = {
    'settings': settings
}

screen_manager = ScreenManager()
screen_monitors = ScreenMonitors(name='screen_monitors')
screen_settings = ScreenSettings(name='screen_settings')
screen_edit_name = ScreenEditName(name='screen_edit_name')
screen_edit_sensor = ScreenEditSensor(name='screen_edit_sensor')
screen_monitor = ScreenMonitor(name='screen_monitor')
screen_list = ScreenList(name='screen_list')
screen_manager.add_widget(screen_monitors)
screen_manager.add_widget(screen_settings)
screen_manager.add_widget(screen_edit_name)
screen_manager.add_widget(screen_edit_sensor)
screen_manager.add_widget(screen_list)
screen_manager.add_widget(screen_monitor)
screen_manager.current = 'screen_monitors'

store = JsonStore('smartportbt.json')
for element in store.keys():
    config[element] = store[element]
    if 'type' in config[element]:
        if config[element]['type'] == 'monitor':
            button = Factory.ButtonList(text=config[element]['name'])
            button.uuid = element
            button.bind(on_long_press=screen_monitors.show_popup_monitors)
            button.bind(on_short_press=screen_monitors.show_screen_monitor)
            screen_monitors.ids.list_config.add_widget(button)

bluetooth_extended = BluetoothExtended()
bluetooth_extended.timeout = 0.003

event_voice = threading.Event()
thread_voice = threading.Thread(
    name='thread_voice', target=do_speak, args=(event_voice,), daemon=True)
thread_voice.start()
packet = []

if __name__ == "__main__":
    smartport_app.run()
