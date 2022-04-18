---
sort: 16
---

# 定制着色器

WxGL的模型是[wxgl.Model](https://xufive.github.io/wxgl/api/model.html)类的实例，[wxgl.glplot.model](https://xufive.github.io/wxgl/api/glplot.html#wxglglplotmodel)函数可以绘制wxgl.Model实例。

这段代码绘制了一个球环，球环的颜色来自1D纹理，球环上每个顶点的纹理坐标是该点法向量和光线向量的点积。

```python
import numpy as np
import wxgl
import wxgl.glplot as glt

vshader = """
    #version 330 core
    in vec4 a_Position;
    in vec3 a_Normal;
    uniform mat4 u_ProjMatrix;
    uniform mat4 u_ViewMatrix;
    uniform mat4 u_ModelMatrix;
    out vec3 v_Normal;
    void main() { 
        gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
        mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
        v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
    }
"""

fshader = """
    #version 330 core
    uniform vec3 u_LightDir;
    uniform sampler1D u_Texture;
    in vec3 v_Normal;
    void main() { 
        vec3 lightDir = normalize(u_LightDir); 
        float diffuseCos = max(0.0, dot(lightDir, v_Normal));
        //float diffuseCos = (dot(lightDir, v_Normal) + 1.0) / 2;
        gl_FragColor = texture1D(u_Texture, diffuseCos);
    } 
"""

r, R = 1, 3
gv, gu = np.mgrid[180:-180:181j, 0:360:181j]
gv, gu = np.radians(gv), np.radians(gu)
xs = (R + r * np.cos(gv)) * np.cos(gu)
zs = -(R + r * np.cos(gv)) * np.sin(gu)
ys = r * np.sin(gv)

vs = np.dstack((xs, ys, zs))
rows, cols = vs.shape[:2]
vs = vs.reshape(-1, 3)

idx = np.arange(rows*cols).reshape(rows, cols)
idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[1:,1:], idx[:-1, 1:]
idx = np.int32(np.dstack((idx_a, idx_b, idx_d, idx_c, idx_d, idx_b)).ravel())

vs = vs[idx]
a, b, c = vs[::3], vs[1::3], vs[2::3]
n = np.repeat(np.cross(b-a, a-c), 3, axis=0)

normal = np.zeros((rows*cols, 3), dtype=np.float32)
idx_arg = np.argsort(idx)
rise = np.where(np.diff(idx[idx_arg])==1)[0] + 1
rise = np.hstack((0,rise,len(idx)))

for i in range(rows*cols):
    normal[i] = np.sum(n[idx_arg[rise[i]:rise[i+1]]], axis=0)

normal = normal.reshape(rows, cols, -1)
normal[0] += normal[-1]
normal[-1] = normal[0]
normal[:,0] += normal[:,-1]
normal[:,-1] = normal[:,0]
normal = normal.reshape(-1, 3)[idx]

im = np.uint8(np.stack((np.arange(256), np.zeros(256), np.zeros(256)), axis=1))
texture = wxgl.Texture(im, ttype=wxgl.TEXTURE_1D, s_tile=wxgl.GL_CLAMP_TO_EDGE)

m = wxgl.Model(wxgl.TRIANGLES, vshader, fshader, visible=True, opacity=True, inside=True)
m.set_vertex('a_Position', vs)
m.set_normal('a_Normal', normal)
m.set_argument('u_LightDir', (-5,-1,-5))
m.add_texture('u_Texture', texture)
m.set_proj_matrix('u_ProjMatrix')
m.set_view_matrix('u_ViewMatrix')
m.set_model_matrix('u_ModelMatrix')
m.set_cull_mode('back')

glt.figure(elev=10)
glt.title('以法向量和光线向量的点积作为1D纹理坐标')
glt.model(m)
glt.show()
```

![doc_shader.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_shader.jpg)

