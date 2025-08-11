import os
import time
import struct
import threading
from typing import TypeAlias

import PIL.Image
import numpy as np
from tqdm import tqdm
import serial.tools.list_ports


RGB565: TypeAlias = int


def _screen_data_compressor(photo_data: list[RGB565]) -> bytearray:
    hex_use = bytearray()
    block_size = 128
    assert len(photo_data) % block_size == 0
    for i in range(0, len(photo_data)//block_size):
        data_w = photo_data[i*block_size:(i+1)*block_size]
        cmp_use = []
        for i in range(0, block_size//2):
            cmp_use.append(data_w[i*2+0]*65536+data_w[i*2+1])
        result = max(set(cmp_use), key=cmp_use.count)
        hex_use.extend(struct.pack('>BBI', 2, 4, result))
        for i in range(0, block_size//2):
            if ((data_w[i*2+0]*65536+data_w[i*2+1]) != result):
                hex_use.extend(struct.pack('>BBHH', 4, i, data_w[i*2+0], data_w[i*2+1]))
        hex_use.extend([2, 3, 8, 1, 0, 0])
    return hex_use


def _img_to_RGB565(img: PIL.Image.Image) -> list[RGB565]:
    img = np.asarray(img)
    R_8bit, G_8bit, B_8bit = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    R_5bit = (R_8bit >> 3).astype(np.uint16)
    G_6bit = (G_8bit >> 2).astype(np.uint16)
    B_5bit = (B_8bit >> 3).astype(np.uint16)
    rgb565_image = (R_5bit << 11) | (G_6bit << 5) | B_5bit
    return rgb565_image.flatten().tolist()


class MiniScreen:
    def __init__(self, ser: serial.Serial, size=(160, 80), show_counter=False):
        self.ser = ser
        self.size = size
        self.data = None
        self.touch = 65535
        self.show_counter = show_counter
        if self.show_counter:
            self.tqdm = {i: tqdm(desc=i) for i in ('发送次数', '发送大小', '处理图像次数')}
        self.deamon = threading.Thread(target=self._show_send, daemon=True).start()

    def __del__(self):
        self.ser.close()

    def _read_adc_ch(self, ch) -> int:
        self.ser.write(bytearray([8, ch, 0, 0, 0, 0]))
        recv = self.ser.read(self.ser.in_waiting)
        if not recv:
            return 0
        return recv[4]*256+recv[5]

    def _show_send(self):
        while True:
            if t := self._read_adc_ch(9):
                self.touch = t
            if not self.data:
                time.sleep(0.01)
                continue
            t = self.data
            self.data = None
            self.ser.write(t)
            if self.show_counter:
                self.tqdm['发送次数'].update(1)
                self.tqdm['发送大小'].update(len(t))

    def show(self, img: PIL.Image.Image):
        self.data = _screen_data_compressor(_img_to_RGB565(img.resize(self.size)))
        if self.show_counter:
            self.tqdm['处理图像次数'].update(1)


def get_mini_screen_device() -> list[MiniScreen]:
    a = []
    for port in serial.tools.list_ports.comports():
        try:
            if os.name == 'nt':
                ser = serial.Serial(port.name, 19200, timeout=2)
            elif os.name == 'posix':
                ser = serial.Serial(port.device, 19200, timeout=2)
            else:
                raise NotImplementedError
        except serial.serialutil.SerialException:
            continue
        time.sleep(0.15)     # 理论上MSN设备100ms要发送一次「MSN01」，在150ms内至少会收到一次
        recv = ser.read(ser.in_waiting)
        try:
            assert recv.endswith(b'\x00MSN01'), 1
            ser.write(b'\x00MSNCN')
            time.sleep(0.15)
            recv = ser.read(ser.in_waiting)
            assert recv.startswith(b'\x00MSN'), 2
        except AssertionError as e:
            ser.close()
        else:
            a.append(MiniScreen(ser))
    return a
