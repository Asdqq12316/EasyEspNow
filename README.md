# EasyEspNow (EEN)

MicroPython ESP-NOW 极简封装。默认 **ESP-NOW v1**，字符串进字符串出，
设完目标就不用再管 MAC，接收支持「收到什么就干嘛」一条命令绑定。

支持 **ESP32** 和 **ESP8266**，两平台用法基本一致，
唯一区别是接收时 ESP8266 需要在主循环里多调一行 `e.poll()`。

---

## 安装

把 `een.py` 上传到设备（Thonny / mpremote / ampy 均可），
和你的 `main.py` 放在同一目录。

| 工具 | 命令 |
|------|------|
| Thonny | 文件 → 保存副本到设备 → 选择 `een.py` |
| mpremote | `mpremote cp een.py :` |
| ampy | `ampy put een.py` |

---

## 快速开始

```python
import een

e = een.EEN()
print(e.mac())                  # 本机 MAC，字符串

e.to('aa:bb:cc:dd:ee:ff')       # 设一次目标
e.send('hello')                 # 发字符串
```

---

## 平台差异（重要）

| 功能 | ESP32 | ESP8266 |
|------|-------|---------|
| ESP-NOW 基础通信 | ✅ | ✅ |
| `irq()` 中断回调 | ✅ 有 | ❌ 无 |
| `e.when()` 后是否需要 `e.poll()` | 不需要 | **需要** |
| 广播 MAC | ✅ | ❌ 不支持 |
| 主循环 | 可空转 | 必须调 `e.poll()` |

一句话：

- **ESP32**：`when()` 自动生效，主循环可以 `while True: pass`
- **ESP8266**：主循环里必须写 `e.poll()`，否则 `when()` 绑定的函数不会被触发

---

## 接收

### if 版（非阻塞）— 通用

```python
if e.got():
    print(e.msg, '来自', e.src)  # 全是字符串
```

### while 版（阻塞）— 通用

```python
while e.wait():
    print(e.msg)
    if e.msg == 'end':
        break
```

### 带超时（毫秒）— 通用

```python
while True:
    if e.wait(1000):
        print(e.msg)
    else:
        print('1 秒内没有消息')
```

---

## 收到什么就干嘛

`when(字符串, 函数名)`：收到指定消息就调用那个函数，**不阻塞主循环**。

> ⚠️ 函数名后面**不要加括号**。
> - `e.when('on', led.on)` → ✅ 传函数本身
> - `e.when('on', led.on())` → ❌ 立刻执行，返回 None

### ESP32 写法

```python
# 型号：ESP32
import een
from machine import Pin

led = Pin(2, Pin.OUT)

e = een.EEN()
print('我的 MAC:', e.mac())

e.when('on',  led.on)
e.when('off', led.off)

while True:
    pass        # ESP32 用中断，主循环可以空转
```

### ESP8266 写法

```python
# 型号：ESP8266
import een
from machine import Pin

led = Pin(2, Pin.OUT)

e = een.EEN()
print('我的 MAC:', e.mac())

e.when('on',  led.on)
e.when('off', led.off)

while True:
    e.poll()    # ESP8266 必须写这一行
```

### 需要传参时，自己包一个小函数 — 通用

```python
def set_led(level):
    led.value(level)

e.when('led on',  lambda: set_led(1))
e.when('led off', lambda: set_led(0))
```

### 收到就回复 — 通用

```python
def pong():
    e.send('pong')

e.when('ping', pong)
```

没匹配到的消息会被**直接忽略**。

---

## OLED 显示屏示例（含型号引脚）

| 型号 | 默认 I2C 引脚 | 说明 |
|------|---------------|------|
| ESP32 | `sda=21, scl=22` | 多数 ESP32 开发板 |
| ESP8266 | `sda=16, scl=5` | NodeMCU / Wemos D1 mini |

屏幕通常为 0.96 寸 I2C OLED，地址 `0x3C`（部分为 `0x3D`）。

### ESP32 版（中断回调）

```python
# 型号：ESP32
import een
from oled_draw import OLED

e = een.EEN()
print('我的 MAC:', e.mac())

oled = OLED(sda=21, scl=22, width=128, height=64,
            font_path='ziku.txt', addr=0x3C)

def show_black():
    oled.fill(1)
    oled.draw_text(0, 0, "你好", 0)
    oled.show()

def show_white():
    oled.fill(0)
    oled.draw_text(0, 0, "你好", 1)
    oled.show()

e.when('a', show_black)
e.when('b', show_white)

while True:
    pass        # ESP32 用中断
```

### ESP8266 版（轮询）

```python
# 型号：ESP8266
import een
from oled_draw import OLED

e = een.EEN()
print('我的 MAC:', e.mac())

oled = OLED(sda=16, scl=5, width=128, height=64,
            font_path='ziku.txt', addr=0x3C)

def show_black():
    oled.fill(1)
    oled.draw_text(0, 0, "你好", 0)
    oled.show()

def show_white():
    oled.fill(0)
    oled.draw_text(0, 0, "你好", 1)
    oled.show()

e.when('a', show_black)
e.when('b', show_white)

while True:
    e.poll()    # ESP8266 必须写
```

---

## 切换版本

```python
e.ver(2)     # 默认是 1
```

- v1：兼容 ESP8266 / ESP32，单包最多 **250 字节**
- v2：仅较新 ESP32，单包最多 **1470 字节**

部分老固件不支持 `version=` 参数，`ver(2)` 会静默退回 v1。

---

## API 速查

| 命令 | 作用 |
|------|------|
| `e.mac()` | 本机 MAC（字符串） |
| `e.to('aa:bb:...')` | 设置发送目标，之后不用再管 |
| `e.send('hi')` | 发送字符串 |
| `e.got(ms=0)` | if 版接收，非阻塞 |
| `e.wait(ms=None)` | while 版接收，可带超时 |
| `e.when('x', 函数名)` | 收到 'x' 就执行那个函数（无参，不加括号） |
| `e.poll()` | ESP8266 主循环里必须调用 |
| `e.ver(1/2)` | 切换 ESP-NOW 版本，默认 v1 |
| `e.msg` / `e.src` | 最近一次的消息 / 来源（字符串） |

---

## 判断自己是哪种设备

```python
import sys
print(sys.platform)     # 'esp32' 或 'esp8266'

import een
e = een.EEN()
print(e._has_irq)       # True = 有 irq；False = 需要 poll
```

---

## 注意事项

- 所有设备必须在**同一 Wi-Fi 信道**。
  改信道：`e._wlan.config(channel=6)`
- **ESP8266 不支持广播**，目标必须填单播 MAC。
- ESP8266 上运行前会自动 `disconnect()`，避免自动重连 AP。
- 所有对外输出都是字符串，不用 `decode()`、不用管 bytes。
- 用 `when()` 时：ESP32 自动启用中断；ESP8266 需要主循环 `poll()`。
- 若 `got()` / `wait()` 抛 `ValueError` 卡死，可重置：
  ```python
  e._e.active(False)
  e._e.active(True)
  ```

---

## 许可

MIT
