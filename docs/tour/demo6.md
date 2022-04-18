---
sort: 6
---

# 定制着色器

除了内置的绘图函数，WxGL还提供了GLSL接口，允许用户定制着色器代码。下面的代码演示了使用定制的顶点着色器和片元着色器的基本流程。

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

![readme_06.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/readme_06.jpg)
