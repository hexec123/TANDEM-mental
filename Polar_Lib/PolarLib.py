import asyncio
import math
import numpy as np
import time

from bleak import BleakClient, BleakError
from bleak.uuids import uuid16_dict
""" 
MIT License

Copyright (c) 2023 Kieran Brennan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

"""
Copyright(c) 2024 Centre technologique en aérospatiale (CTA)
"""
# AUTHOR: Jean-Yves Galipeau (OIQ: 125441)
# DATE: FEB 1, 2024
# Inspired by works of Kiran Brennan (https://github.com/kbre93/dont-hold-your-breath/tree/master)

uuid16_inv_dict = {v: k for k, v in uuid16_dict.items()}

HEART_RATE_DEVICE_PATTERN = "0000{0:x}-0000-1000-8000-00805f9b34fb"
PMD_DEVICE_PATTERN = "FB005C8{0:x}-02E7-F387-1CAD-8ACD2D8DF0C8"


class DeviceH10:
    ECG_SAMPLING_FREQUENCY = 130

    """ Predefined UUID (Universal Unique Identifier) mapping are based on Heart Rate GATT service Protocol that most
    Fitness/Heart Rate device manufacturer follow (including Polar H10 in this case) to obtain a specific response from 
    the device like an API could do """

    # UUID for model number
    MODEL_NBR_UUID = HEART_RATE_DEVICE_PATTERN.format(
        uuid16_inv_dict.get("Model Number String")
    )

    # UUID for manufacturer name
    MANUFACTURER_NAME_UUID = HEART_RATE_DEVICE_PATTERN.format(
        uuid16_inv_dict.get("Manufacturer Name String")
    )

    # UUID for battery level
    BATTERY_LEVEL_UUID = HEART_RATE_DEVICE_PATTERN.format(
        uuid16_inv_dict.get("Battery Level")
    )

    HEART_RATE_MEASUREMENT_UUID = HEART_RATE_DEVICE_PATTERN.format(
        uuid16_inv_dict.get("Heart Rate Measurement")
    )

    # UUID for Request of stream settings
    PMD_CONTROL_UUID = PMD_DEVICE_PATTERN.format(1)

    # UUID for Request of start stream
    PMD_DATA_UUID = PMD_DEVICE_PATTERN.format(2)

    ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82,
                           0x00, 0x01, 0x01, 0x0E, 0x00])

    def __init__(self, mac_address: str, debug_mode: bool = False):
        self._mac_address: str = mac_address
        self._debug_mode: bool = debug_mode
        self._loop = None
        self._stop = False
        self.last_hr_value = None
        self.last_ibi_value = None
        self.last_ecg_values = None
        self._received_data_cb = None
        self.hr_stream_times = None
        self.ecg_stream_times = None
        self.ibi_stream_times = None

    @property
    def received_data_cb(self):
        return self._received_data_cb

    @received_data_cb.setter
    def received_data_cb(self, value):
        if not callable(value):
            raise RuntimeError("Not a callable object.  Must be a function.")

        self._received_data_cb = value

    async def connect_async(self):
        """ Connect to device and received data from the device. """
        if self._debug_mode:
            print("Connecting to device: {0}".format(self._mac_address))
        self._stop = False

        try:
            async with BleakClient(self._mac_address) as bluetooth_client:
                model_number = await bluetooth_client.read_gatt_char(self.MODEL_NBR_UUID)
                manufacturer_name = await bluetooth_client.read_gatt_char(self.MANUFACTURER_NAME_UUID)
                battery_level = await bluetooth_client.read_gatt_char(self.BATTERY_LEVEL_UUID)

                if self._debug_mode:
                    print(">>> Model Number: {0}".format(DeviceH10.conv2string(model_number)), flush=True)
                    print(">>> Manufacturer Name: {0}".format(DeviceH10.conv2string(manufacturer_name)), flush=True)
                    print(">>> Battery Level: {0}%".format(int(battery_level[0])), flush=True)

                await bluetooth_client.read_gatt_char(self.PMD_CONTROL_UUID)
                await bluetooth_client.write_gatt_char(self.PMD_CONTROL_UUID, self.ECG_WRITE)
                await bluetooth_client.start_notify(self.PMD_DATA_UUID, self.ecg_recv_data_conv)
                await bluetooth_client.start_notify(self.HEART_RATE_MEASUREMENT_UUID, self.hr_recv_data_conv)
                await asyncio.wait_for(self.wait_stop_request(), timeout=None)
                await bluetooth_client.stop_notify(self.PMD_DATA_UUID)
                await bluetooth_client.stop_notify(self.HEART_RATE_MEASUREMENT_UUID)
                await bluetooth_client.disconnect()
        except BleakError as ex:
            print(ex)
        except asyncio.TimeoutError:
            pass  # Could handle timeout if desired.
        except (asyncio.CancelledError, KeyboardInterrupt):
            print("Interrupt App - PolarH10!")

    async def wait_stop_request(self):
        """ Wait to received to Stop command. """
        while not self._stop:
            await asyncio.sleep(1)

    async def ecg_recv_data_conv(self, sender, data: bytearray):
        """ Received data and convert them to timestamp and ECG values. """
        ecg_stream_values = []
        ecg_stream_times = []
        if data[0] == 0x00:
            if self._debug_mode:
                print("Data received ECG...")
            timestamp = DeviceH10.conv2int(data, 1, 8, signed=False) / 1.0e9
            step = 3
            time_step = 1.0 / self.ECG_SAMPLING_FREQUENCY
            samples = data[10:]
            n_samples = math.floor(len(samples) / step)
            offset = 0
            sample_timestamp = timestamp - (n_samples - 1) * time_step
            while offset < len(samples):
                ecg = DeviceH10.conv2int(samples, offset, step, signed=True)
                offset += step
                ecg_stream_values.extend([ecg])
                ecg_stream_times.extend([sample_timestamp])
                sample_timestamp += time_step

            if self._debug_mode:
                print("ECG|{0} len={2}|{1} len={3}".format(ecg_stream_times, ecg_stream_values,
                                                           len(ecg_stream_times), len(ecg_stream_values)))

            self.last_ecg_values = ecg_stream_values
            self.ecg_stream_times = ecg_stream_times

            if self.received_data_cb is not None:
                self.received_data_cb(self)
                await asyncio.sleep(0.1)

    async def hr_recv_data_conv(self, sender, data: bytearray):
        """
        `data` is formatted according to the GATT Characteristic and Object Type 0x2A37 Heart Rate Measurement which is
        one of the three characteristics included in the "GATT Service 0x180D Heart Rate".
        `data` can include the following bytes:
        - flags
            Always present.
            - bit 0: HR format (uint8 vs. uint16)
            - bit 1, 2: sensor contact status
            - bit 3: energy expenditure status
            - bit 4: RR interval status
        - HR
            Encoded by one or two bytes depending on flags/bit0. One byte is always present (uint8). Two bytes (uint16)
            are necessary to represent HR > 255.
        - energy expenditure
            Encoded by 2 bytes. Only present if flags/bit3.
        - inter-beat-intervals (IBIs)
            One IBI is encoded by 2 consecutive bytes. Up to 18 bytes depending on presence of uint16 HR format and
            energy expenditure.
        """
        byte0 = data[0]  # heart rate format
        uint8_format = (byte0 & 1) == 0
        energy_expenditure = ((byte0 >> 3) & 1) == 1
        rr_interval = ((byte0 >> 4) & 1) == 1

        if not rr_interval:
            return

        if self._debug_mode:
            print("Data received HR...")

        first_rr_byte = 2
        if uint8_format:
            hr = data[1]
            pass
        else:
            hr = (data[2] << 8) | data[1]  # uint16
            first_rr_byte += 1

        if energy_expenditure:
            # ee = (data[first_rr_byte + 1] << 8) | data[first_rr_byte]
            first_rr_byte += 2

        hr_stream_values = []
        hr_stream_times = []

        hr_stream_values.extend([hr])
        hr_stream_times.extend([time.time_ns() / 1.0e9])

        ibi_stream_values = []
        ibi_stream_times = []

        for i in range(first_rr_byte, len(data), 2):
            ibi = (data[i + 1] << 8) | data[i]
            # Polar H7, H9, and H10 record IBIs in 1/1024 seconds format.
            # Convert 1/1024 sec format to milliseconds.
            # transmit data in milliseconds.
            ibi = np.ceil(ibi / 1024 * 1000)
            ibi_stream_values.extend([ibi])
            ibi_stream_times.extend([time.time_ns() / 1.0e9])

        if self._debug_mode:
            print("HR |{0} len={2}|{1} len={3}".format(hr_stream_times, hr_stream_values,
                                                       len(hr_stream_times), len(hr_stream_values)))
            print("IBI|{0} len={2}|{1} len={3}".format(ibi_stream_times, ibi_stream_values,
                                                       len(ibi_stream_times), len(hr_stream_values)))

        if len(hr_stream_values) > 0:
            self.last_hr_value = hr_stream_values[0]

        if len(ibi_stream_values) > 0:
            self.last_ibi_value = ibi_stream_values[0]

        if self.received_data_cb is not None:
            self.received_data_cb(self)
            await asyncio.sleep(0.1)

    def stop(self):
        self._stop = True

    @staticmethod
    def conv2int(data, offset, length, signed: bool):
        """ Convert byte array to an integer (signed or not). """
        return int.from_bytes(bytearray(data[offset: offset + length]), byteorder="little", signed=signed)

    @staticmethod
    def conv2string(data):
        return "".join(map(chr, data))
