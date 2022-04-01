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
* matplotlib - 推荐版本:3.1.2或更高  
* pillow - 推荐版本:8.2.0或更高
* wxpython - 推荐版本:4.0.7.post2或更高 
* freetype-py - 推荐版本:2.2.0或更高
* pynput - 推荐版本:1.7.6或更高
* imageio - 推荐版本:2.8.0或更高

# 快速体验

* 下面这几行代码，绘制了一个中心在三维坐标系原点半径为1的纯色圆球。忽略模块名的话，这些代码和Matplotlib的风格几乎是完全一致的。

```python
import wxgl.glplot as glt

glt.title('快速体验：$x^2+y^2+z^2=1$')
glt.uvsphere((0,0,0), 1, color='cyan')
glt.show()
```

* 在一张画布上可以任意放置多个子图。下面的代码演示了子图布局函数subplot的经典用法，代码中的纹理图片在example路径下。

```python
import wxgl
import wxgl.glplot as glt

glt.subplot(121)
glt.title('经纬度网格生成球体')
glt.uvsphere((0,0,0), 1, texture=wxgl.Texture('res/earth.jpg'))
glt.grid()
glt.subplot(122)
glt.title('正八面体迭代细分生成球体')
glt.isosphere((0,0,0), 1, color=(0,1,1), fill=False, iterations=5)
glt.grid()
glt.show()
```

* 对于数据快速可视化工具来说，ColorBar是必不可少的。下面的代码演示了ColorBar最简单的用法。

```python
import numpy as np
import wxgl.glplot as glt

vs = np.random.random((300, 3))*2-1
color = np.random.random(300)
size = np.linalg.norm(vs, axis=1)
size = 30 * (size - size.min()) / (size.max() - size.min())

glt.title('随机生成的300个点')
glt.point(vs, color, cm='jet', alpha=0.8, size=size)
glt.colorbar('jet', [0, 100], loc='right', subject='高度')
glt.colorbar('Paired', [-50, 50], loc='bottom', subject='温度', margin_left=5)
glt.colorbar('rainbow', [0, 240], loc='bottom', subject='速度', margin_right=5)
glt.show()
```

* WxGL提供了BaseLight、SunLight、LampLight、SkyLight、SphereLight等多种光照方案，配合光洁度、粗糙度、金属度、透光度等参数，可模拟不同的质感。

```python
import wxgl
import wxgl.glplot as glt

glt.subplot(221)
glt.title('太阳光')
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.SunLight(roughness=0, metalness=0, shininess=0.5))

glt.subplot(222)
glt.title('灯光')
pos = (3, 0.0, 3)
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.LampLight(position=pos))
glt.point((pos,), color='white', size=20)

glt.subplot(223)
glt.title('户外光')
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.SkyLight(sky=(1.0,1.0,1.0)))

glt.subplot(224)
glt.title('球谐光')
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.SphereLight(5, factor=0.8))

glt.show()
```

* 通过transform参数传递一个以累计渲染时长duration为参数的函数给模型，可以实现复杂的模型动画。相机巡航也以类似的方式实现。下面代码中，模型渲染使用了射向右后方的平行光，模型旋转时光照位置随之改变，而相机旋转时光照位置不变。

```python
import wxgl
import wxgl.glplot as glt

tf = lambda duration : ((0, 1, 0, (0.02*duration)%360),)
cf = lambda duration : {'azim':(-0.02*duration)%360}

tx = wxgl.Texture('res/earth.jpg')
light = wxgl.SunLight(direction=(1,0,-1))

glt.subplot(121)
glt.title('模型旋转')
glt.cylinder((0,1,0), (0,-1,0), 1, texture=tx, transform=tf, light=light)

glt.subplot(122)
glt.cruise(cf)
glt.title('相机旋转')
glt.cylinder((0,1,0), (0,-1,0), 1, texture=tx, light=light)

glt.show()
```

* 除了内置的绘图函数，wxgl还提供了GLSL接口，允许用户定制着色器代码。下面的代码演示了使用顶点着色器源码和片元着色器源码的基本流程。

```python
import wxgl
import wxgl.glplot as glt

vshader = """
	#version 330 core
	in vec4 a_Position;
    in vec4 a_Color;
	uniform mat4 u_ProjMatrix;
    uniform mat4 u_ViewMatrix;
    uniform mat4 u_ModelMatrix;
    out vec4 v_Color;
	void main() { 
		gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
		v_Color = a_Color;
	}
"""

fshader = """
	#version 330 core
	in vec4 v_Color;
	void main() { 
		gl_FragColor = v_Color; 
	} 
"""

m = wxgl.Model(wxgl.TRIANGLE_STRIP, vshader, fshader) # 实例化模型，设置绘图方法和着色器源码
m.set_vertex('a_Position', [[-1,1,0],[-1,-1,0],[1,1,0],[1,-1,0]]) # 4个顶点坐标
m.set_color('a_Color', [[1,0,0],[0,1,0],[0,0,1],[0,1,1]]) # 4个顶点的颜色
m.set_proj_matrix('u_ProjMatrix') # 设置投影矩阵
m.set_view_matrix('u_ViewMatrix') # 设置视点矩阵
m.set_model_matrix('u_ModelMatrix') # 设置模型矩阵

glt.model(m) # 添加模型到画布
glt.show() # 显示画布
```
