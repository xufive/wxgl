---
sort: 1
---

# 安装

WxGL模块使用pip命令安装。

```
pip install wxgl
```

以下模块为WxGL所依赖，如果当前系统没有安装或者版本不满足要求，安装过程将同时安装或更新它们。

* pyopengl          - 推荐版本：3.1.5或更高 
* numpy             - 推荐版本：1.18.2或更高 
* matplotlib        - 推荐版本：3.1.2或更高
* pyqt6             - 推荐版本：6.3.0或更高 
* pillow            - 推荐版本：8.2.0或更高
* freetype-py       - 推荐版本：2.2.0或更高
* imageio           - 推荐版本：2.22.0或更高
* imageio-ffmpeg    - 推荐版本：0.4.8或更高
* webp              - 推荐版本：0.1.5或更高

WxGL使用WxPython或PyQt6作为显示后端，上述安装过程自动安装了PyQt6模块。如果想使用WxPython作为显示后端，请自行安装。

在Windows和macOS平台上，可使用如下命令WxPython模块。

```
pip install -U wxPython
```

在Linux平台上，以Ubuntu为例，可使用如下命令WxPython模块。

```
pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04 wxPython
```

