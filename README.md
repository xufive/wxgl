# WxGL

WxGL是一个基于PyOpenGL的三维数据可视化库,以wx为显示后端,提供Matplotlib风格的交互式应用模式,同时,也可以和wxPython无缝结合,在wx的窗体上绘制三维模型。从V0.7.0开始,新的版本升级都会考虑向下兼容。

# 1. 安装和依赖关系

WxGL模块使用pip命令安装。
```shell
pip install wxgl
```

WxGL依赖以下模块,如果当前运行环境没有安装这些模块,安装程序将会自动安装它们。如果安装过程出现问题,或者安装完成后无法正常使用,请手动安装WxGL的依赖模块。
 
* pyopengl(推荐版本:3.1.5或更高) 
* numpy(推荐版本:1.18.2或更高) 
* scipy(推荐版本:1.4.1或更高)
* matplotlib(推荐版本:3.1.2或更高)  
* pillow(推荐版本:8.2.0或更高)
* wxpython(推荐版本:4.0.7.post2或更高) 
* freetype(推荐版本:2.2.0或更高)

# 2. 快速体验

从V0.6.0开始,WxGL新增了交互式绘图子模块wxplot,提供类似Matplotlib风格2D/3D绘图函数。如果熟悉NumPy和Matplotlib的话,几分钟就可以学会使用WxGL的交互式绘图。

```python
>>> import wxgl.wxplot as plt
>>> plt.sphere((0,0,0), 1, color='cyan')
>>> plt.show()
```

上面这几行代码,绘制了一个中心在坐标原点半径为1的青色的圆球。如果忽略模块名的话,这些代码和Matplotlib的风格是完全一样的。执行最后一句show()命令后,将弹出GUI窗口,同时程序将阻塞,直至关闭GUI窗口。

![本地图片](https://img-blog.csdnimg.cn/20210701153814347.png)

WxGL自动根据绘图指令和绘图数据选择2D或3D模式。比如,下面的代码并未显式地设置2D或3D模式,最终输出的是2D模式下附带ColorBar的热力图。

```python
>>> import numpy as np
>>> import wxgl.wxplot as plt
>>> ys, xs = np.mgrid[-2:2:200j,-4:4:400j]
>>> data = 5*xs*np.exp(-xs**2-ys**2)
>>> plt.hot(data, xs=xs, ys=ys, cm='jet')
>>> plt.colorbar(tick_format=lambda t:'%0.2f'%t)
>>> plt.title('热力图和ColorBar')
>>> plt.show()
```

![本地图片](https://img-blog.csdnimg.cn/20210701171709520.png)

WxGL支持在一张画布上绘制多张子图,创建子图的方式也非常类似Matplotlib。

```python
>>> plt.subplot(121)
>>> plt.cylinder([(0,0,1),(0,0,-1)], 1, color='#ff7f0e')
>>> plt.subplot(122)
>>> plt.cube((0,0,0), 1, color='#2ca02c')
>>> plt.show()
```

![本地图片](https://img-blog.csdnimg.cn/20210701154641124.png)

正如Matplotlib可以支持面向对象的使用方式,WxGL也提供了面向对象的使用方法。
```python
>>> ys, xs = np.mgrid[-2:2:200j,-4:4:400j]
>>> zs = 5*xs*np.exp(-xs**2-ys**2)
>>> fig = plt.create_figure(size=(800,600))
>>> ax = fig.add_axes()
>>> ax.mesh(xs, ys, zs, color=zs, cm='hsv')
>>> fig.show()
```

![本地图片](https://img-blog.csdnimg.cn/20210701153604516.png)






