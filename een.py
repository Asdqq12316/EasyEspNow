# een.py
import network
import espnow


class EEN:
    def __init__(self):
        self._wlan = network.WLAN(network.WLAN.IF_STA)
        self._wlan.active(True)
        try:
            self._wlan.disconnect()
        except OSError:
            pass

        self._e = espnow.ESPNow(version=1)   # 默认 v1
        self._e.active(True)

        self._dst = None
        self._peers = set()
        self._rules = {}                      # 'msg' -> 函数
        self._irq = False

        self.msg = None
        self.src = None

    # ---------- 工具 ----------
    @staticmethod
    def _b(mac):
        if isinstance(mac, (bytes, bytearray)):
            return bytes(mac)
        return bytes(int(x, 16) for x in mac.split(':'))

    @staticmethod
    def _s(mac):
        return ':'.join('%02x' % b for b in mac)

    # ---------- ① 设目标 ----------
    def to(self, mac):
        self._dst = self._b(mac)
        if self._dst not in self._peers:
            self._e.add_peer(self._dst)
            self._peers.add(self._dst)
        return self

    # ---------- ② 改版本 ----------
    def ver(self, n):
        self._e.active(False)
        self._e = espnow.ESPNow(version=n)
        self._e.active(True)
        for p in self._peers:
            self._e.add_peer(p)
        return self

    # ---------- ③ 发送 ----------
    def send(self, data):
        if self._dst is None:
            raise ValueError('先调用 e.to(mac)')
        if isinstance(data, str):
            data = data.encode()
        return self._e.send(self._dst, data)

    # ---------- ④ 接收 ----------
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

    def wait(self, ms=None):
        return self.got(ms)

    # ---------- 收到什么就干嘛 ----------
    def when(self, msg, cb):
        """
        e.when('led on', led.on)          # 直接传函数名
        e.when('ping',   pong)            # 传你自己定义的函数
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