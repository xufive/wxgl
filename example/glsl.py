import sys
import numpy as np
import wxgl

if sys.platform.lower() == 'darwin': # MacOS系统
    vshader = """
        attribute vec4 a_Position;
        attribute vec3 a_Normal;
        uniform mat4 u_ProjMatrix;
        uniform mat4 u_ViewMatrix;
        uniform mat4 u_ModelMatrix;
        varying vec3 v_Normal;

        mat4 inverse(mat4 m) {
            float Coef00 = m[2][2] * m[3][3] - m[3][2] * m[2][3];
            float Coef02 = m[1][2] * m[3][3] - m[3][2] * m[1][3];
            float Coef03 = m[1][2] * m[2][3] - m[2][2] * m[1][3];
               
            float Coef04 = m[2][1] * m[3][3] - m[3][1] * m[2][3];
            float Coef06 = m[1][1] * m[3][3] - m[3][1] * m[1][3];
            float Coef07 = m[1][1] * m[2][3] - m[2][1] * m[1][3];
               
            float Coef08 = m[2][1] * m[3][2] - m[3][1] * m[2][2];
            float Coef10 = m[1][1] * m[3][2] - m[3][1] * m[1][2];
            float Coef11 = m[1][1] * m[2][2] - m[2][1] * m[1][2];
               
            float Coef12 = m[2][0] * m[3][3] - m[3][0] * m[2][3];
            float Coef14 = m[1][0] * m[3][3] - m[3][0] * m[1][3];
            float Coef15 = m[1][0] * m[2][3] - m[2][0] * m[1][3];
               
            float Coef16 = m[2][0] * m[3][2] - m[3][0] * m[2][2];
            float Coef18 = m[1][0] * m[3][2] - m[3][0] * m[1][2];
            float Coef19 = m[1][0] * m[2][2] - m[2][0] * m[1][2];
               
            float Coef20 = m[2][0] * m[3][1] - m[3][0] * m[2][1];
            float Coef22 = m[1][0] * m[3][1] - m[3][0] * m[1][1];
            float Coef23 = m[1][0] * m[2][1] - m[2][0] * m[1][1];
               
            const vec4 SignA = vec4( 1.0, -1.0,  1.0, -1.0);
            const vec4 SignB = vec4(-1.0,  1.0, -1.0,  1.0);
               
            vec4 Fac0 = vec4(Coef00, Coef00, Coef02, Coef03);
            vec4 Fac1 = vec4(Coef04, Coef04, Coef06, Coef07);
            vec4 Fac2 = vec4(Coef08, Coef08, Coef10, Coef11);
            vec4 Fac3 = vec4(Coef12, Coef12, Coef14, Coef15);
            vec4 Fac4 = vec4(Coef16, Coef16, Coef18, Coef19);
            vec4 Fac5 = vec4(Coef20, Coef20, Coef22, Coef23);
               
            vec4 Vec0 = vec4(m[1][0], m[0][0], m[0][0], m[0][0]);
            vec4 Vec1 = vec4(m[1][1], m[0][1], m[0][1], m[0][1]);
            vec4 Vec2 = vec4(m[1][2], m[0][2], m[0][2], m[0][2]);
            vec4 Vec3 = vec4(m[1][3], m[0][3], m[0][3], m[0][3]);
               
            vec4 Inv0 = SignA * (Vec1 * Fac0 - Vec2 * Fac1 + Vec3 * Fac2);
            vec4 Inv1 = SignB * (Vec0 * Fac0 - Vec2 * Fac3 + Vec3 * Fac4);
            vec4 Inv2 = SignA * (Vec0 * Fac1 - Vec1 * Fac3 + Vec3 * Fac5);
            vec4 Inv3 = SignB * (Vec0 * Fac2 - Vec1 * Fac4 + Vec2 * Fac5);
               
            mat4 Inverse = mat4(Inv0, Inv1, Inv2, Inv3);
            vec4 Row0 = vec4(Inverse[0][0], Inverse[1][0], Inverse[2][0], Inverse[3][0]);
            float Determinant = dot(m[0], Row0);
            Inverse /= Determinant;
               
            return Inverse;
        }

                mat4 transpose(mat4 m) {
                    mat4 result = mat4(0.0);
                    for (int i=0; i<4; i++)
                        for (int j=0; j<4; j++)
                            result[i][j] = m[j][i];

                    return result;
                }
        void main() { 
            gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
            mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
            v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
        }
    """
    
    fshader = """
        uniform vec3 u_LightDir;
        uniform sampler1D u_Texture;
        varying vec3 v_Normal;
        void main() { 
            vec3 lightDir = normalize(u_LightDir); 
            float diffuseCos = max(0.0, dot(lightDir, v_Normal));
            gl_FragColor = texture1D(u_Texture, diffuseCos);
        } 
    """
else: # Windows和Linux系统
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

m = wxgl.Model(wxgl.TRIANGLES, vshader, fshader)
m.set_vertex('a_Position', vs)
m.set_normal('a_Normal', normal)
m.set_argument('u_LightDir', (-5,-1,-5))
m.add_texture('u_Texture', texture)
m.set_proj_matrix('u_ProjMatrix')
m.set_view_matrix('u_ViewMatrix')
m.set_model_matrix('u_ModelMatrix')
m.set_cull_mode('back')

app = wxgl.App(elev=20)
app.title('以法向量和光线向量的点积作为1D纹理坐标')
app.model(m)
app.show()

