import numpy as np
import wxgl
import wxgl.glplot as glt

# ----------------------------
# Demo 1
# ----------------------------
glt.title('快速体验：$x^2+y^2+z^2=1$')
glt.uvsphere((0,0,0), 1, color='cyan')
glt.show()

# ----------------------------
# Demo 2
# ----------------------------
glt.subplot(121)
glt.title('经纬度网格生成球体')
glt.uvsphere((0,0,0), 1, texture=wxgl.Texture('res/earth.jpg'))
glt.grid()
glt.subplot(122)
glt.title('正八面体迭代细分生成球体')
glt.isosphere((0,0,0), 1, color=(0,1,1), fill=False, iterations=5)
glt.grid()
glt.show()

# ----------------------------
# Demo 3
# ----------------------------
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

# ----------------------------
# Demo 4
# ----------------------------
glt.subplot(221)
glt.title('太阳光')
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.SunLight())

glt.subplot(222)
glt.title('灯光')
pos = (3, 0.0, 3)
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.LampLight(position=pos))
glt.point((pos,), color='white', size=20)

glt.subplot(223)
glt.title('户外光')
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.SkyLight())

glt.subplot(224)
glt.title('球谐光')
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.SphereLight(9))

glt.show()

# ----------------------------
# Demo 5
# ----------------------------
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

# ----------------------------
# Demo 6
# ----------------------------
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
