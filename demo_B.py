# demo_B.py —— 接收端
#
# 直接运行，打印本机 MAC，
# 然后等待 demo_A 发来的消息。

import een
from machine import Pin

led = Pin(2, Pin.OUT)              # 板载 LED，按需修改引脚

e = een.EEN()
print('本机 MAC:', e.mac())
print('把这个 MAC 填到 demo_A.py 的 TARGET 里')

# ---------- 收到什么就干嘛 ----------
e.when('on',  led.on)
e.when('off', led.off)

def pong():
    e.send('pong')
    print('收到 ping，已回复 pong')

e.when('ping', pong)

def end():
    print('收到 end，收到就忽略（这里只是演示）')

e.when('end', end)

# ---------- 主循环 ----------
# when() 已接管接收，这里可以随便干别的
while True:
    # 也可以同时用阻塞方式收其他消息
    if e.wait(1000):
        print('其他消息:', e.msg, '来自', e.src)
