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

glt.uvsphere((0,0,0), 1, color='cyan')
glt.title('快速体验：$x^2+y^2=1$')
glt.show()
```

![色球](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_01.png)


* 在一张画布上可以任意放置多个子图。下面的代码演示了子图布局函数subplot的经典用法。实际上，这个函数比Matplotlib的同名函数更灵活和便捷。

```python
import wxgl
import wxgl.glplot as glt

glt.subplot(121)
glt.title('经纬度网格生成球体')
glt.uvsphere((0,0,0), 1, texture=wxgl.Texture('res/earth.jpg'))
glt.subplot(122)
glt.title('正八面体迭代细分生成球体')
glt.isosphere((0,0,0), 1, color=(0,1,1), iterations=5)
glt.show()
```

![子图布局](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_02.png)


* 对于数据快速可视化工具来说，ColorBar是必不可少的。下面的代码演示了ColorBar最简单的用法。wxgl提供了cmap_help和cmap_list两个函数用于查看颜色映射表。

```python
import numpy as np
import wxgl.glplot as glt

vs = np.random.random((300, 3))*2-1
color = np.random.random(300)
size = np.random.randint(3, 15, size=300)
glt.point(vs, color, cm='jet', alpha=0.9, size=size)
glt.colorbar('jet', [-1, 1], loc='right')
glt.colorbar('Paired', [-5, 5], loc='bottom', subject='温度')
glt.colorbar('rainbow', [0, 77], loc='bottom', subject='速度')
glt.show()
```

![调色板](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_03.png)


* 通过transform参数传递一个以累计渲染时长为参数的函数给模型，可以实现复杂的模型动画。相机巡航、漫游等，也以同样的方式实现。

```python
import numpy as np
import wxgl
import wxgl.glplot as glt

r = 1 # 花灯半径为1
theta = np.linspace(0, 2*np.pi, 361) 
xs = r * np.tile(np.cos(theta), (150,1))
zs = r * np.tile(-np.sin(theta), (150,1))
ys = np.repeat(np.linspace(1.35, -1.35, 150), 361).reshape(150,361)

tf = lambda duration : ((0, 1, 0, (-0.02*duration)%360),)
tx = wxgl.Texture('res/bull.jpg')

glt.mesh(xs, ys, zs, texture=tx, transform=tf, light=wxgl.BaseLight())
glt.show()
```

![动画函数](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_04.png)


* 除了内置绘图函数，wxgl还提供了GLSL接口，允许用户定制着色器代码。这意味着，wxgl正在尝试成为GLSL语言的解释器——尽管距离这个目标还很遥远。下面的代码演示了使用顶点着色器源码和片元着色器源码的基本流程。

```python
import wxgl
import wxgl.glplot as glt

vshader = """
	#version 330 core
	in vec4 a_Position;
    in vec4 a_Color;
	uniform mat4 u_MVPMatrix;
    out vec4 v_Color;
	void main() { 
		gl_Position = u_MVPMatrix * a_Position; 
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
m.set_mvp_matrix('u_MVPMatrix') # 设置模型矩阵、视点矩阵和投影矩阵

glt.cruise(lambda duration : {'azim':(0.02*duration)%360}) # 相机巡航（绕y轴逆时针旋转）
glt.model(m) # 添加模型到画布
glt.show() # 显示画布
```

这里使用Model.set_mvp_matrix函数将着色器中的MVP三合一矩阵和WxGL的模型矩阵、视点矩阵和投影矩阵联系起来。Model类还提供了set_model_matrix函数、set_view_matrix函数和set_proj_matrix函数，分别关联着色器中的模型矩阵、视点矩阵和投影矩阵。另外，这段代码还演示了相机动画函数的使用方式，和前面的模型动画基本类似。

![GLSL接口](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_05.png)



