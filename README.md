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

* 下面这几行代码，绘制了一个中心在坐标原点半径为1的纯色圆球。忽略模块名的话，这些代码和Matplotlib的风格是完全一致的。

```python
import wxgl.wxplot as plt

plt.uvsphere((0,0,0), 1, color='cyan')
plt.title('快速体验：$x^2+y^2=1$')
plt.show()
```

![色球](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_01.png)


* 在一张画布上可以任意方式排放多个子图。下面的代码演示了子图布局函数subplot的经典用法。实际上，这个函数比Matplotlib的同名函数更加灵活和快捷。

```python
plt.subplot(121)
plt.title('经纬度网格生成球体')
plt.uvsphere((0,0,0), 1, lon=(180,-180), lat=(90,-90), texture='res/earth.jpg')
plt.subplot(122)
plt.title('正八面体迭代细分生成球体', color='cyan')
plt.isosphere((0,0,0), 1, color=[0,1,1])
plt.show()
```

![子图布局](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_02.png)


* 对于数据快速可视化工具来说，调色板（ColorBar）是必不可少的。下面的代码演示了调色板最简单的用法。wxgl提供了cmap_help和cmap_list两个函数用于显示调色板分类和调色板列表。

```python
vs = np.random.random((300, 3))*2-1
color = np.random.random(300)
size = np.random.randint(3, 15, size=300)
plt.scatter(vs, color, 'jet', size=size)
plt.colorbar('jet', [-1, 1], loc='right')
plt.show()
```

![调色板](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_03.png)


* 通过transform参数传递一个以累计渲染时长为参数的函数给模型，可以实现复杂的模型动画。相机巡航、漫游等，也以同样的方式实现。

```python
lon = np.arange(-180, 180)
lat = np.arange(-90, 90)
lons, lats = np.meshgrid(lon, lat)
height = np.sin(np.radians(lons))*80

tf = lambda duration : ((0, 1, 0, (0.02*duration)%360),)
tx = 'res/earth.jpg'

plt.mesh(lons, height, lats, color='brown', texture=None, transform=tf, light=(-1,0,0))
plt.mesh(lons, lats, height, texture=tx, transform=None, cw=True, light=(-1,0,0))
plt.xlabel("经度")
plt.ylabel("高度")
plt.zlabel("纬度")
plt.xrange((-180, 180))
plt.yformat(lambda y : '%d KM'%y)
plt.xdensity(6)
plt.show()
```

![动画函数](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_04.png)


* 除了内置绘图函数，wxgl还提供了GLSL接口，允许用户定制着色器代码。这意味着，wxgl正在尝试成为GLSL语言的不完全解释器。下面的代码演示了使用顶点着色器源码和片元着色器源码的基本流程。

```python
import wxgl
import wxgl.wxplot as plt

vshader_src = """
	#version 330 core
	in vec4 a_Position;
	uniform mat4 u_ProjMatrix;
	uniform mat4 u_ViewMatrix;
	uniform mat4 u_ModelMatrix;
	void main() { 
		gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
		gl_PointSize = (a_Position.z + 1) * 30 ;
	}
"""

fshader_src = """
	#version 330 core
	uniform sampler2D u_Texture;
	void main() { 
		vec2 temp = gl_PointCoord - vec2(0.5);
		if (dot(temp, temp) > 0.25) {
			discard;
		}
		gl_FragColor = texture2D(u_Texture, gl_PointCoord);
	} 
"""

vs = np.random.random((300, 3)) * 2 - 1
texture = np.uint8(np.random.randint(0, 256, (64,64,3)))

m = wxgl.Model(wxgl.POINTS, vshader_src, fshader_src, sprite=True)
m.set_vertex('a_Position', vs)
m.set_proj_matrix('u_ProjMatrix') # 设置投影矩阵
m.set_view_matrix('u_ViewMatrix') # 设置视点矩阵
m.set_model_matrix('u_ModelMatrix') # 设置模型矩阵
m.add_texture('u_Texture', texture)

plt.model(m)
plt.show()
```

![GLSL接口](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/readme_img_05.png)



