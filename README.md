# EasyEspNow (EEN)

MicroPython ESP-NOW 极简封装。默认 **ESP-NOW v1**，字符串进字符串出，
设完目标就不用再管 MAC，接收支持「收到什么就干嘛」一条命令绑定。

## 安装

把 `een.py` 上传到设备（Thonny / mpremote / ampy 均可），
和你的 `main.py` 放在同一目录。

## 快速开始

```python
import een

e = een.EEN()
print(e.mac())                  # 本机 MAC，字符串

e.to('aa:bb:cc:dd:ee:ff')       # 设一次目标
e.send('hello')                 # 发字符串
```

## 接收

### if 版（非阻塞）

```python
if e.got():
    print(e.msg, '来自', e.src)  # 全是字符串
```

### while 版（阻塞）

```python
while e.wait():
    print(e.msg)
    if e.msg == 'end':
        break
```

### 带超时（毫秒）

```python
while True:
    if e.wait(1000):
        print(e.msg)
    else:
        print('1 秒内没有消息')
```

## 收到什么就干嘛

`when(字符串, 函数名)`：收到指定消息就调用那个函数，**不阻塞主循环**。

```python
from machine import Pin
led = Pin(2, Pin.OUT)

e.when('on',  led.on)      # 收到 'on'  ->  led.on()
e.when('off', led.off)     # 收到 'off' ->  led.off()

while True:
    pass                   # 主循环随便干别的
```

需要传参时，自己包一个小函数：

```python
def set_led(level):
    led.value(level)

e.when('led on',  lambda: set_led(1))
e.when('led off', lambda: set_led(0))
```

收到就回复：

```python
def pong():
    e.send('pong')

e.when('ping', pong)
```

没匹配到的消息会被**直接忽略**。

## 切换版本

```python
e.ver(2)     # 默认是 1
```

- v1：兼容 ESP8266 / ESP32，单包最多 **250 字节**
- v2：仅较新 ESP32，单包最多 **1470 字节**

## API 速查

| 命令 | 作用 |
|------|------|
| `e.mac()` | 本机 MAC（字符串） |
| `e.to('aa:bb:...')` | 设置发送目标，之后不用再管 |
| `e.send('hi')` | 发送字符串 |
| `e.got(ms=0)` | if 版接收，非阻塞 |
| `e.wait(ms=None)` | while 版接收，可带超时 |
| `e.when('x', 函数名)` | 收到 'x' 就执行那个函数（无参） |
| `e.ver(1/2)` | 切换 ESP-NOW 版本，默认 v1 |
| `e.msg` / `e.src` | 最近一次的消息 / 来源（字符串） |

## 注意事项

- 所有设备必须在**同一 Wi-Fi 信道**。
  改信道：`e._wlan.config(channel=6)`
- **ESP8266 不支持广播**，目标必须填单播 MAC。
- ESP8266 上运行前会自动 `disconnect()`，避免自动重连 AP。
- 所有对外输出都是字符串，不用 `decode()`、不用管 bytes。
- 用 `when()` 会自动启用中断回调，主循环不阻塞。
- 若 `got()` / `wait()` 抛 `ValueError` 卡死，可重置：
  ```python
  e._e.active(False)
  e._e.active(True)
  ```

## 许可

MIT
