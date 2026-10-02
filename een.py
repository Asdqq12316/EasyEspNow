# een.py —— EasyEspNow (EEN)
# 支持 irq() 的设备自动用中断；不支持时退回 poll() 轮询
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

        self._e = self._make(1)
        self._e.active(True)

        # 检测固件是否支持 irq()
        self._has_irq = hasattr(self._e, 'irq')

        self._dst = None
        self._peers = set()
        self._rules = {}                 # 'msg' -> 函数
        self._irq_on = False

        self.msg = None
        self.src = None

    # ---------- 兼容不同固件 ----------
    @staticmethod
    def _make(ver):
        try:
            return espnow.ESPNow(version=ver)
        except TypeError:
            return espnow.ESPNow()

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
        was_irq = self._irq_on
        self._e.active(False)
        self._e = self._make(n)
        self._e.active(True)
        self._has_irq = hasattr(self._e, 'irq')
        for p in self._peers:
            self._e.add_peer(p)
        if was_irq and self._has_irq:
            self._e.irq(self._handler)
            self._irq_on = True
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
        e.when('on',  led.on)
        e.when('ping', pong)
        支持 irq 的设备：自动中断回调
        不支持 irq 的设备：需要在主循环里调用 e.poll()
        """
        self._rules[msg] = cb
        if self._has_irq:
            self._start_irq()
        return self

    # ---------- 轮询（irq 不可用时用） ----------
    def poll(self):
        """
        在 while 循环里调用：
            while True:
                e.poll()
                # 其他代码
        """
        if self._has_irq:
            return          # 有 irq 就不用 poll
        while True:
            try:
                src, msg = self._e.recv(0)
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

    # ---------- 本机 MAC ----------
    def mac(self):
        return self._s(self._wlan.config('mac'))

    # ---------- 内部 ----------
    def _start_irq(self):
        if not self._irq_on:
            self._irq_on = True
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