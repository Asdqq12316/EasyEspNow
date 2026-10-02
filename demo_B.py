# demo_B.py —— 接收端
#
# 型号：ESP32 / ESP8266 都可运行，但接收方式不同：
#   - ESP32   ：e.when() 自动生效，主循环可空转
#   - ESP8266 ：主循环里必须调用 e.poll()
#
# 文件末尾已经根据 sys.platform 自动切换，两种板子都能直接跑。

import sys
import een
from machine import Pin

# 板载 LED（ESP32 / ESP8266 一般在 GPIO2）
led = Pin(2, Pin.OUT)

e = een.EEN()
print('本机 MAC:', e.mac())
print('平台:', sys.platform)
print('把这个 MAC 填到 demo_A.py 的 TARGET 里')

# ---------- 收到什么就干嘛（函数名不加括号！）----------
e.when('on',  led.on)
e.when('off', led.off)

def pong():
    e.send('pong')
    print('收到 ping，已回 pong')

e.when('ping', pong)

def end():
    print('收到 end，这里是收到 end 后的处理')

e.when('end', end)

# ---------- 主循环 ----------
# ESP32   ：when() 用中断回调，主循环空转即可
# ESP8266 ：没有 irq()，必须调用 e.poll() 才会触发 when()
if sys.platform == 'esp8266':
    while True:
        e.poll()                 # ESP8266 必须写这一行
else:
    while True:
        pass                     # ESP32 主循环可以空转
