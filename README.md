# WxGL

WxGL是一个基于PyOpenGL的三维数据可视化库，以wx为显示后端，提供Matplotlib风格的交互式应用方式。WxGL也可以和wxPython无缝结合，在wx的窗体上绘制三维模型。

# 安装和依赖关系

WxGL模块使用pip命令安装。
```shell
pip install wxgl
```

WxGL依赖pyopengl等模块，如果当前运行环境没有安装这些模块，安装程序将会自动安装它们。如果安装过程出现问题，或者安装完成后无法正常使用，请手动安装WxGL的依赖模块。
 
* pyopengl - 推荐版本:3.1.5或更高 
* numpy - 推荐版本:1.18.2或更高 
* scipy - 推荐版本:1.4.1或更高
* matplotlib - 推荐版本:3.1.2或更高  
* pillow - 推荐版本:8.2.0或更高
* wxpython - 推荐版本:4.0.7.post2或更高 
* freetype - 推荐版本:2.2.0或更高

# 快速体验

下面这几行代码，绘制了一个中心在坐标原点半径为1的纯色圆球。忽略模块名的话，这些代码和Matplotlib的风格是完全一致的。

```python
import wxgl.wxplot as plt
plt.uvsphere((0,0,0), 1, color='cyan')
plt.title('快速体验：$x^2+y^2=1$')
plt.show()
```


生成一个地球模式是如此简单。

```python
>>> plt.uvsphere((0,0,0), 1, texture='res/image/earth.jpg', xflip=True, yflip=False)
>>> plt.show()
```

让地球自转，更是易如反掌。
```python
plt.uvsphere((0,0,0), 1, 
    texture='res/image/earth.jpg', 
    xflip=True, 
    yflip=False,
    transform = lambda tn,gms,tms : ((0, 1, 0, (0.02*tms)%360),)
)
plt.show()
``