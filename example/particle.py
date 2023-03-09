import numpy as np
import wxgl

vshader = """
    #version 330 core
    in vec4 a_Position;
    in float a_Psize;
    in float a_Speed;
    in float a_Swing;
    uniform float u_Timestamp;
    uniform mat4 u_ProjMatrix;
    uniform mat4 u_ViewMatrix;
    uniform mat4 u_ModelMatrix;
    void main() { 
        float y = a_Position.y - a_Speed * u_Timestamp;
        y += (int(1-y)/2) * 2;

        float x = a_Position.x + a_Swing * u_Timestamp;
        if (x > 1) x -= (int(x+1)/2) * 2;
        else if (x < -1) x += (int(1-x)/2) * 2;

        vec4 pos = vec4(x, y, a_Position.z, a_Position.w);
        gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * pos; 
        gl_PointSize = a_Psize; 
    }
"""

fshader = """
    #version 330 core
    uniform sampler2D u_Snow;
    void main() { 
        gl_FragColor = texture2D(u_Snow, gl_PointCoord); 
    } 
"""

n = 100 # 粒子数量
vs = np.random.random((n, 3)) * 2 - 1 # 粒子的xyz坐标均在[-1,1)区间内
psize = (vs[:,2] + 1.5) * 20 # 由远及近，点的大小从10到50
speed = np.random.random(n) * 0.0001 + 0.0001 # 下落速度：0.1/s~0.2/s
swing = np.random.random(n) * 0.0001 # 水平位移速度：-0.1/s~0.1/s
snow = wxgl.Texture('res/snow.png')

m = wxgl.Model(wxgl.POINTS, vshader, fshader, alive=True, sprite=True)
m.set_vertex('a_Position', vs)
m.set_psize('a_Psize', psize)
m.set_argument('a_Speed', speed)
m.set_argument('a_Swing', swing)
m.set_timestamp('u_Timestamp')
m.add_texture('u_Snow', snow)
m.set_proj_matrix('u_ProjMatrix')
m.set_view_matrix('u_ViewMatrix')
m.set_model_matrix('u_ModelMatrix')

app = wxgl.App(fovy=40)
app.title('雪花粒子')
app.model(m)
app.show()

