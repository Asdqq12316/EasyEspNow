# demo_A.py —— 发送端
# 型号：ESP32 或 ESP8266 均可，代码完全一致
#
# 用法：
#   1. 先运行 demo_B.py，记下它打印出的本机 MAC
#   2. 把那个 MAC 填到下面 TARGET
#   3. 运行本文件

import time
import een

TARGET = 'aa:bb:cc:dd:ee:ff'      # ← 改成接收端的 MAC

e = een.EEN()
print('本机 MAC:', e.mac())
print('目标 MAC:', TARGET)

e.to(TARGET)                       # 设一次，之后不用再管

n = 0
while True:
    n += 1
    e.send('a')
    print('发 a', n)
    time.sleep(1)

    e.send('b')
    print('发 b', n)
    time.sleep(1)
