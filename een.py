# een.py —— EasyEspNow (EEN)
# MicroPython ESP-NOW 极简封装
# 默认 ESP-NOW v1，字符串进字符串出，设完目标不用再管 MAC
import network
import espnow


class EEN:
    def __init__(self):
        # WLAN 自动初始化
        self._wlan = network.WLAN(network.WLAN.IF_STA)
        self._wlan.active(True)
        try:
            self._wlan.disconnect()      # ESP8266 需要，避免自动连 AP
        except OSError:
            pass

        # ESP-NOW 初始化（默认 v1，自动兼容老固件）
        self._e = self._make(1)
        self._e.active(True)

        self._dst = None                 # 目标 MAC (bytes)
        self._peers = set()              # 已注册的 peer
        self._rules = {}                 # 'msg' -> 函数
        self._irq = False

        self.msg = None                  # 最近消息（字符串）
        self.src = None                  # 最近来源（字符串）

    # ---------- 兼容不同固件 ----------
    @staticmethod
    def _make(ver):
        """老固件不支持 version= 参数，自动回退"""
        try:
            return espnow.ESPNow(version=ver)
        except TypeError:
            return espnow.ESPNow()

    # ---------- 字符串 ↔ bytes ----------
    @staticmethod
    def _b(mac):
        if isinstance(mac, (bytes, bytearray)):
            return bytes(mac)
        return bytes(int(x, 16) for x in mac.split(':'))

    @staticmethod
    def _s(mac):
        return ':'.join('%02x' % b for b in mac)

    # ---------- ① 设置发送目标（一次就够）----------
    def to(self, mac):
        self._dst = self._b(mac)
        if self._dst not in self._peers:
            self._e.add_peer(self._dst)
            self._peers.add(self._dst)
        return self

    # ---------- ② 改 ESP-NOW 版本 ----------
    def ver(self, n):
        self._e.active(False)
        self._e = self._make(n)
        self._e.active(True)
        for p in self._peers:            # 重新注册
            self._e.add_peer(p)
        return self

    # ---------- ③ 发送字符串 ----------
    def send(self, data):
        if self._dst is None:
            raise ValueError('先调用 e.to(mac)')
        if isinstance(data, str):
            data = data.encode()
        return self._e.send(self._dst, data)

    # ---------- ④ 接收 ----------
    # if 用法：非阻塞
    def got(self, ms=0):
        try:
            src, msg = self._e.recv(ms)
        except (OSError, ValueError):
            return False
        if msg is None:
            return False
        self.src = self._s(src)
        try:
            self.msg = msg.decode()
        except UnicodeDecodeError:
            self.msg = repr(msg)
        return True

    # while 用法：阻塞（可带超时毫秒）
    def wait(self, ms=None):
        return self.got(ms)

    # 收到什么就干嘛（不阻塞主循环）
    def when(self, msg, cb):
        """
        e.when('on',  led.on)         # 收到 'on' -> led.on()
        e.when('ping', pong)          # 收到 'ping' -> pong()
        """
        self._rules[msg] = cb
        self._start()
        return self

    # ---------- 本机 MAC ----------
    def mac(self):
        return self._s(self._wlan.config('mac'))

    # ---------- 内部 ----------
    def _start(self):
        if not self._irq:
            self._irq = True
            self._e.irq(self._handler)

    def _handler(self, e):
        while True:
            try:
                src, msg = e.recv(0)
            except (OSError, ValueError):
                return
            if msg is None:
                return
            try:
                m = msg.decode()
            except UnicodeDecodeError:
                m = repr(msg)
            cb = self._rules.get(m)
            if cb:
                cb()