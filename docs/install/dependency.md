---
sort: 1
---

# 依赖关系

WxGL依赖下列模块：
 
* pyopengl     - 推荐版本：3.1.5或更高 
* numpy        - 推荐版本：1.18.2或更高 
* matplotlib   - 推荐版本：3.1.2或更高  
* pillow       - 推荐版本：8.2.0或更高
* freetype-py  - 推荐版本：2.2.0或更高
* pynput       - 推荐版本：1.7.6或更高
* imageio      - 推荐版本：2.8.0或更高

如果当前运行环境没有安装这些模块，安装程序将会自动安装它们。如果安装过程出现问题，或者安装完成后无法正常使用，请手动安装WxGL的依赖模块。

WxGL使用WxPython或PyQt6作为显示后端，若系统找不到WxPython和PyQt6，将使用OpenGL的GLUT库作为显示后端。如果想使用WxPython或PyQt6作为显示后端，请手动安装。
