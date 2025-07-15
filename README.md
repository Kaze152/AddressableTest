# Python移动应用图像识别与自动点击功能

一个完整的Python解决方案，用于识别移动应用中的特定UI元素并执行自动点击操作。

## 功能特性

### 🔌 设备控制
- **Android设备支持**: 通过ADB进行截图、点击、滑动等操作
- **iOS设备支持**: 基于tidevice的基本操作支持
- **设备连接管理**: 自动检测设备连接状态
- **多种操作类型**: 支持点击、长按、双击、滑动等操作

### 🔍 图像识别
- **模板匹配**: 基于OpenCV的多尺度模板匹配
- **OCR文字识别**: 支持中英文文字识别（PaddleOCR）
- **颜色检测**: 颜色和形状特征识别
- **组合识别**: 多种识别方法可组合使用

### 🎯 自动化操作
- **智能点击**: 精确的坐标计算和点击执行
- **重试机制**: 可配置的重试次数和延迟
- **截图功能**: 操作前后的截图记录
- **序列执行**: 支持复杂的操作序列

### ⚙️ 工具与配置
- **配置管理**: 灵活的YAML配置文件
- **日志系统**: 详细的日志记录和调试信息
- **调试工具**: 可视化的调试和测试工具
- **错误处理**: 完善的异常处理和错误恢复

## 安装

### 系统要求
- Python 3.7+
- Android调试桥(ADB) - 用于Android设备
- iOS设备需要安装相应驱动

### 安装依赖
```bash
pip install -r requirements.txt
```

### 主要依赖库
- `opencv-python`: 图像处理和模板匹配
- `pillow`: 图像操作
- `paddleocr`: OCR文字识别
- `numpy`: 数值计算
- `adb-shell`: Android设备控制
- `tidevice`: iOS设备控制
- `pyyaml`: 配置文件支持
- `loguru`: 日志系统

## 快速开始

### 1. 连接设备
```python
from mobile_automation import AndroidDevice

# 连接Android设备
device = AndroidDevice()
if device.connect():
    print("设备连接成功")
    
    # 获取屏幕尺寸
    width, height = device.get_screen_size()
    print(f"屏幕尺寸: {width}x{height}")
    
    # 截图
    screenshot = device.screenshot()
    print(f"截图尺寸: {screenshot.shape}")
```

### 2. 模板匹配
```python
from mobile_automation import TemplateMatchers

# 初始化模板匹配器
matcher = TemplateMatchers()

# 截图
screenshot = device.screenshot()

# 匹配模板
matches = matcher.match_template(screenshot, "button_template.png")
if matches:
    best_match = matches[0]
    print(f"找到匹配: 位置({best_match.center_x}, {best_match.center_y}), 置信度{best_match.confidence}")
```

### 3. OCR文字识别
```python
from mobile_automation import OCRRecognizer

# 初始化OCR识别器
ocr = OCRRecognizer()

# 识别文字
text_results = ocr.recognize_text(screenshot)
for result in text_results:
    print(f"识别文字: '{result.text}', 位置: ({result.center_x}, {result.center_y})")

# 查找特定文字
settings_text = ocr.find_text(screenshot, "设置")
if settings_text:
    print(f"找到'设置'文字: {settings_text[0]}")
```

### 4. 自动点击
```python
from mobile_automation import AutoClicker

# 初始化自动点击器
clicker = AutoClicker(device)

# 点击模板
result = clicker.click_template("button_template.png", template_name="确认按钮")
print(f"点击结果: {result}")

# 点击文字
result = clicker.click_text("设置", exact_match=False)
print(f"点击结果: {result}")

# 点击颜色区域
result = clicker.click_color("blue", min_area=500)
print(f"点击结果: {result}")

# 点击坐标
result = clicker.click_coordinates(100, 200)
print(f"点击结果: {result}")
```

### 5. 执行操作序列
```python
# 定义操作序列
actions = [
    {
        'type': 'click_text',
        'text': '设置',
        'click_type': 'tap',
        'delay_after': 2.0
    },
    {
        'type': 'click_template',
        'template': 'wifi_button.png',
        'template_name': 'WiFi设置',
        'delay_after': 1.0
    },
    {
        'type': 'click_coordinates',
        'x': 300,
        'y': 400,
        'click_type': 'tap'
    }
]

# 执行序列
results = clicker.execute_action_sequence(actions)
for i, result in enumerate(results):
    print(f"操作 {i+1}: {result}")
```

## 项目结构

```
mobile_automation/
├── __init__.py                 # 主模块入口
├── device/                     # 设备控制模块
│   ├── __init__.py
│   ├── device_controller.py    # 设备控制基类
│   ├── android_device.py       # Android设备控制
│   └── ios_device.py          # iOS设备控制
├── recognition/                # 图像识别模块
│   ├── __init__.py
│   ├── template_matcher.py     # 模板匹配
│   ├── ocr_recognizer.py      # OCR识别
│   └── color_detector.py      # 颜色检测
├── automation/                 # 自动化模块
│   ├── __init__.py
│   ├── clicker.py             # 自动点击器
│   └── screen_capture.py      # 屏幕截图
├── utils/                      # 工具模块
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   └── logger.py              # 日志系统
└── examples/                   # 示例代码
    ├── basic_example.py        # 基础示例
    └── wechat_example.py       # 微信自动化示例
```

## 配置

### 创建配置文件
```python
from mobile_automation.utils import Config

# 创建示例配置文件
Config.create_sample_config('config.yaml')
```

### 配置示例
```yaml
device:
  android:
    default_timeout: 30
    screenshot_format: 'png'
    click_delay: 0.1
  
recognition:
  template_matching:
    threshold: 0.8
    multi_scale: true
  ocr:
    language: 'ch'  # 中英文
    confidence_threshold: 0.7
  color_detection:
    tolerance: 30

automation:
  retry_attempts: 3
  retry_delay: 1.0
  screenshot_before_action: true

logging:
  level: 'INFO'
  console_output: true
  file_output: true
```

## 示例

### 基础操作示例
查看 `mobile_automation/examples/basic_example.py` 了解基础功能的使用方法。

### 微信自动化示例
查看 `mobile_automation/examples/wechat_example.py` 了解如何自动化微信操作。

## 调试和测试

### 启用调试模式
```python
from mobile_automation.utils import Logger

# 设置日志级别为DEBUG
Logger.set_level('DEBUG')
```

### 保存调试图像
```python
# 保存模板匹配调试图像
matcher.save_debug_image(screenshot, matches, "debug_template.png")

# 保存OCR识别调试图像
ocr.save_debug_image(screenshot, text_results, "debug_ocr.png")

# 保存颜色检测调试图像
color_detector.save_debug_image(screenshot, color_matches, "debug_color.png")
```

## 注意事项

1. **权限要求**: 确保ADB调试已启用（Android）或设备已信任（iOS）
2. **性能考虑**: OCR识别可能较慢，建议针对特定区域进行识别
3. **稳定性**: 在不同设备和应用版本上测试功能
4. **错误处理**: 使用try-catch包装自动化代码
5. **隐私保护**: 注意保护用户隐私和数据安全

## 故障排除

### 常见问题

1. **设备连接失败**
   - 检查ADB是否正确安装
   - 确认设备USB调试已启用
   - 检查设备是否被其他工具占用

2. **模板匹配失败**
   - 调整匹配阈值
   - 检查模板图像质量
   - 尝试多尺度匹配

3. **OCR识别不准确**
   - 预处理图像（增强对比度、去噪）
   - 调整置信度阈值
   - 确保文字清晰可见

4. **点击位置不准确**
   - 检查坐标计算
   - 添加偏移量调整
   - 验证屏幕尺寸获取

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 免责声明

本工具仅用于学习和研究目的。使用时请遵守相关法律法规和应用服务条款。作者不对使用本工具造成的任何后果负责。
