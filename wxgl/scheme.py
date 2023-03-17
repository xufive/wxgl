#!/usr/bin/env python3

import sys
import uuid
import numpy as np
from OpenGL.GL import *
from . texture import Texture
from . import util
from . light import *

PLATFORM = sys.platform.lower()

class Scheme:
    """应用于三维场景中的展示方案类"""

    def __init__(self, haxis='y', bg=(0.0,0.0,0.0)):
        """构造函数

        haxis       - 高度轴，默认y轴，可选z轴，不支持x轴
        bg          - 背景色，默认0.0, 0.0, 0.0)
        """

        self._reset()

        self.haxis = haxis.lower()                              # 高度轴
        self.bg = util.format_color(bg)                         # 背景色
        self.fg = 1 - self.bg                                   # 前景色

    def _reset(self):
        """清除模型数据"""

        self.r_x = [1e12, -1e12]                                # 数据在x轴上的动态范围
        self.r_y = [1e12, -1e12]                                # 数据在y轴上的动态范围
        self.r_z = [1e12, -1e12]                                # 数据在z轴上的动态范围
        self.cid = -1                                           # 缺省颜色id
        self.expost = dict()                                    # 需要在模型空间确定后绘制的模型，比如网格或坐标轴 
        self.cruise_func = None                                 # 相机巡航函数
        self.alive = False                                      # 是否使用了动画函数
        self.models = [dict(), dict(), dict()]                  # 主视区、标题区、调色板区模型
        self.widgets = dict()                                   # 由一个或多个模型组成的部件

    def _set_range(self, r_x=None, r_y=None, r_z=None):
        """设置坐标轴范围"""

        if r_x:
            self.r_x[0] = min(r_x[0], self.r_x[0])
            self.r_x[1] = max(r_x[1], self.r_x[1])

        if r_y:
            self.r_y[0] = min(r_y[0], self.r_y[0])
            self.r_y[1] = max(r_y[1], self.r_y[1])

        if r_z:
            self.r_z[0] = min(r_z[0], self.r_z[0])
            self.r_z[1] = max(r_z[1], self.r_z[1])

    def _format_color(self, color, repeat=None):
        """将颜色参数转为浮点型的numpy数组"""

        if color is None:
            self.cid = (self.cid+1)%10

        return util.format_color(color, self.cid, repeat=repeat)

    def _get_series(self, v_min, v_max, endpoint=False, extend=0):
        """返回标注序列

        v_min       - 数据最小值
        v_max       - 数据最大值
        endpoint    - 返回序列两端为v_min和v_max
        extend      - 值域外延系数
        """

        ks = (1, 2, 2.5, 5) # 分段选项
        s_min, s_max = 4, 7 # 分段数 
        r = v_max - v_min
        tmp = np.array([[abs(float(('%E'%(r/i)).split('E')[0])-k) for i in range(s_min,s_max)] for k in ks])
        i, j = divmod(tmp.argmin(), tmp.shape[1])
        step, steps = ks[i], j+s_min
        step *= pow(10, int(('%E'%(r/steps)).split('E')[1]))

        result = list()
        v = int(v_min/step)*step
        while v < v_max:
            if v > v_min:
                result.append(round(v, 6))
            v += step

        if endpoint:
            if result[0] > v_min:
                result.insert(0, v_min)
            if result[-1] < v_max:
                result.append(v_max)

        if extend > 0:
            delta = extend * r
            if result[0] - v_min + delta < step / 2:
                result.remove(result[0])
            if v_max - result[-1] + delta < step / 2:
                result.remove(result[-1])

            result.insert(0, v_min - delta)
            result.append(v_max + delta)

        return result

    def _line(self, vs, gltype, color, width, stipple, **kwds):
        """线段

        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        gltype      - 线的三种图元绘制方法之一
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        width       - 线宽：0.0~10.0之间，None使用默认设置
        stipple     - 线型：整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None使用默认设置
        kwds        - 关键字参数
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient     - 环境光，默认(1.0,1.0,1.0)
            name        - 模型或部件名
        """

        keys = ['visible', 'inside', 'slide', 'transform', 'ambient', 'name']
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)

        light = BaseLight(kwds.pop('ambient') if 'ambient' in kwds else (1.0,1.0,1.0))
        name = kwds.pop('name') if 'name' in kwds else None

        vs = np.array(vs, dtype=np.float32)
        color = self._format_color(color, vs.shape[0])

        self.model(light.get_model(gltype, vs, color=color, lw=width, ls=stipple, **kwds), name)

    def _surface(self, vs, gltype, color=None, texture=None, texcoord=None, **kwds):
        """三角面或四角面组成的曲面

        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        gltype      - 三角面和四角面的五种图元绘制方法之一
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片，或2D/2DArray/3D纹理对象
        texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
        kwds        - 关键字参数
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认True（不透明）
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        keys = ['visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name']
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)

        light = kwds.pop('light') if 'light' in kwds else SkyLight(direction=(-0.1,0.2,-1) if self.haxis=='z' else (-0.1,-1,-0.2))
        name = kwds.pop('name') if 'name' in kwds else None

        vs = np.array(vs, dtype=np.float32)
        normal = util.get_normal(gltype, vs)

        if gltype == GL_TRIANGLE_STRIP and (np.absolute(vs[0]-vs[-2])<1e-10).all() and (np.absolute(vs[1]-vs[-1])<1e-10).all():
            normal[0] += normal[-2]
            normal[1] += normal[-1]
            normal[-2] = normal[0]
            normal[-1] = normal[1]
        elif gltype == GL_TRIANGLE_FAN and (np.absolute(vs[1]-vs[-1])<1e-10).all():
            normal[1] += normal[-1]
            normal[-1] = normal[1]
        elif gltype == GL_QUAD_STRIP and (np.absolute(vs[0]-vs[-2])<1e-10).all() and (np.absolute(vs[1]-vs[-1])<1e-10).all():
            normal[0] += normal[-2]
            normal[1] += normal[-1]
            normal[-2] = normal[0]
            normal[-1] = normal[1]

        if not texture is None and not texcoord is None:
            if not isinstance(texture, Texture):
                texture = Texture(texture)
            texcoord = np.array(texcoord, dtype=np.float32)
            self.model(light.get_model(gltype, vs, normal=normal, texture=texture, texcoord=texcoord, **kwds), name)
        else:
            color = self._format_color(color, vs.shape[0])
            self.model(light.get_model(gltype, vs, normal=normal, color=color, **kwds), name)

    def _mesh(self, xs, ys, zs, gltype, color=None, texture=None, ccw=True, **kwds):
        """网格面

        xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)，m为网格行数，n为网格列数
        gltype      - 三角面和四角面的两种图元绘制方法之一
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片，或2D纹理对象
        ccw         - 顶点逆时针排序的面为正面
        kwds        - 关键字参数
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认不透明
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        keys = ['visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name']
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)

        name = kwds.pop('name') if 'name' in kwds else None
        light = kwds.pop('light') if 'light' in kwds else SkyLight(direction=(-0.1,0.2,-1) if self.haxis=='z' else (-0.1,-1,-0.2))

        vs = np.dstack((xs, ys, zs))
        rows, cols = vs.shape[:2]

        idx = np.arange(rows*cols).reshape(rows, cols)
        idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[:-1, 1:], idx[1:,1:]
        if ccw:
            if gltype == GL_QUADS:
                indices = np.int32(np.dstack((idx_a, idx_b, idx_d, idx_c)).ravel())
            else:
                indices = np.int32(np.dstack((idx_a, idx_b, idx_c, idx_c, idx_b, idx_d)).ravel())
        else:
            if gltype == GL_QUADS:
                indices = np.int32(np.dstack((idx_a, idx_c, idx_d, idx_b)).ravel())
            else:
                indices = np.int32(np.dstack((idx_a, idx_c, idx_b, idx_b, idx_c, idx_d)).ravel())
        normal = util.get_normal(gltype, vs, indices).reshape(rows, cols, -1)

        if (np.absolute(vs[0] - vs[-1]) < 1e-10).all(): # 首行尾行顶点重合
            normal[0] += normal[-1]
            normal[-1] = normal[0]

        if (np.absolute(vs[:,0] - vs[:,-1]) < 1e-10).all(): # 首列尾列顶点重合
            normal[:,0] += normal[:,-1]
            normal[:,-1] = normal[:,0]

        if (np.absolute(vs[0] - vs[0,0]) < 1e-10).all(): # 首行顶点重合
            normal[0] = normal[0,0]

        if (np.absolute(vs[-1] - vs[-1,0]) < 1e-10).all(): # 尾行顶点重合
            normal[-1] = normal[-1,0]

        if (np.absolute(vs[:,0] - vs[0,0]) < 1e-10).all(): # 首列顶点重合
            normal[:,0] = normal[0,0]

        if (np.absolute(vs[:,-1] - vs[-1,0]) < 1e-10).all(): # 尾列顶点重合
            normal[:,-1] = normal[0,-1]

        if not texture is None:
            if not isinstance(texture, Texture):
                texture = Texture(texture)

            u, v = np.linspace(0, 1, cols), np.linspace(0, 1, rows)
            texcoord = np.float32(np.dstack(np.meshgrid(u, v)).reshape(-1, 2))
            self.model(light.get_model(gltype, vs, normal=normal, texture=texture, texcoord=texcoord, indices=indices, **kwds), name)
        else:
            color = self._format_color(color, rows*cols)
            self.model(light.get_model(gltype, vs, normal=normal, color=color, indices=indices, **kwds), name)

    def _axes(self):
        """坐标轴"""

        name = self.expost['axes']['name']
        cx, cy, cz = [1,0,0], [0,1,0], [0,0,1]
        colors = np.repeat(np.array([cx, cy, cz]), 2, axis=0)

        dx = self.r_x[1]-self.r_x[0]
        dy = self.r_y[1]-self.r_y[0]
        dz = self.r_z[1]-self.r_z[0]
        x0 = (self.r_x[1]+self.r_x[0])/2
        y0 = (self.r_y[1]+self.r_y[0])/2
        z0 = (self.r_z[1]+self.r_z[0])/2
        dmax = max(dx, dy, dz)

        if dmax <= 0:
            r = 0.02
            vs = [[-1,0,0], [0.85,0,0], [0,-1,0], [0,0.85,0], [0,0,-1], [0,0,0.85]]
            cones = [[(0.85,0,0), (1,0,0)], [(0,0.85,0), (0,1,0)], [(0,0,0.85), (0,0,1)]]
        else:
            ext = 0.05 * dmax
            h = 0.07 * dmax
            r = 0.07 * h
            vs, cones = list(), list()

            if dx > 0:
                vs.extend([[self.r_x[0]-ext, y0, z0], [self.r_x[1]+ext, y0, z0]])
                cones.append([[self.r_x[1]+ext, y0, z0], [self.r_x[1]+ext+h, y0, z0]]) 
            else:
                vs.extend([[x0-ext, y0, z0], [x0+ext, y0, z0]])
                cones.append([[x0+ext, y0, z0], [x0+ext+h, y0, z0]]) 

            if dy > 0:
                vs.extend([[x0, self.r_y[0]-ext, z0], [x0, self.r_y[1]+ext, z0]])
                cones.append([[x0, self.r_y[1]+ext, z0], [x0, self.r_y[1]+ext+h, z0]]) 
            else:
                vs.extend([[x0, y0-ext, z0], [x0, y0+ext, z0]])
                cones.append([[x0, y0+ext, z0], [x0, y0+ext+h, z0]]) 

            if dz > 0:
                vs.extend([[x0, y0, self.r_z[0]-ext], [x0, y0, self.r_z[1]+ext]])
                cones.append([[x0, y0, self.r_z[1]+ext], [x0, y0, self.r_z[1]+ext+h]]) 
            else:
                vs.extend([[x0, y0, z0-ext], [x0, y0, z0+ext]])
                cones.append([[x0, y0, z0+ext], [x0, y0, z0+ext+h]]) 

        self.line(vs, color=colors, pair=True, inside=False)
        self.cone(cones[0][1], cones[0][0], r, color=cx, name=name, inside=False)
        self.cone(cones[1][1], cones[1][0], r, color=cy, name=name, inside=False)
        self.cone(cones[2][1], cones[2][0], r, color=cz, name=name, inside=False)
        self.circle(cones[0][0], r, vec=np.array(cones[0][0])-np.array(cones[0][1]), color=cx, name=name, inside=False)
        self.circle(cones[1][0], r, vec=np.array(cones[1][0])-np.array(cones[1][1]), color=cy, name=name, inside=False)
        self.circle(cones[2][0], r, vec=np.array(cones[2][0])-np.array(cones[2][1]), color=cz, name=name, inside=False)

    def _grid(self):
        """网格和刻度 """

        if self.r_x[0] >= self.r_x[-1] or self.r_y[0] >= self.r_y[-1] or self.r_z[0] >= self.r_z[-1]:
            return # '模型空间不存在，返回

        size = self.expost['grid']['size']
        xlabel = self.expost['grid']['xlabel']
        ylabel = self.expost['grid']['ylabel']
        zlabel = self.expost['grid']['zlabel']
        xf = self.expost['grid']['xf']
        yf = self.expost['grid']['yf']
        zf = self.expost['grid']['zf']
        name = self.expost['grid']['name']

        xx = self._get_series(*self.r_x, extend=0.03)
        yy = self._get_series(*self.r_y, extend=0.03)
        zz = self._get_series(*self.r_z, extend=0.03)

        def mesh2quad(xs, ys, zs):
            """mesh转quad"""

            vs = np.dstack((xs, ys, zs))
            rows, cols = vs.shape[:2]

            idx = np.arange(rows*cols).reshape(rows, cols)
            idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[1:,1:], idx[:-1, 1:]
            idx = np.int32(np.dstack((idx_a, idx_b, idx_c, idx_d)).ravel())

            return vs.reshape(-1,3)[idx]

        def text3d_ticks(text, box, color, loc, cull, align, bg, padding):
            """标注"""

            if PLATFORM == 'darwin':
                glsl_version = ''
                texcoord_type = 'vec2'
                sampler_type = 'sampler2D'
                texture_name = 'texture2D'
            else:
                glsl_version = '#version 330 core \n\n'
                texcoord_type = 'vec3'
                sampler_type = 'sampler2DArray'
                texture_name = 'texture'

            vshader = glsl_version + """
                attribute vec4 a_Position;
                attribute %s a_Texcoord;
                attribute float a_TickLoc;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                varying %s v_Texcoord;
                varying float v_Loc;

                void main() { 
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                    v_Texcoord = a_Texcoord;
                    v_Loc = a_TickLoc;
                }
            """ % (texcoord_type, texcoord_type)

            fshader = glsl_version + """
                varying %s v_Texcoord;
                varying float v_Loc;
                uniform vec3 u_AmbientColor;
                uniform %s u_Texture;
                uniform vec2 u_Ae;

                void main() { 
                    if (u_Ae[1] > 90.0 || u_Ae[1] < -90.0) discard;

                    if (v_Loc == 0.0 && (u_Ae[0] < 0.0 || u_Ae[0] >= 90.0)) discard;
                    if (v_Loc == 1.0 && (u_Ae[0] < -90.0 || u_Ae[0] >= 0.0)) discard;
                    if (v_Loc == 2.0 && u_Ae[0] >= -90.0) discard;
                    if (v_Loc == 3.0 && u_Ae[0] < 90.0) discard;

                    if (u_Ae[1] < 0.0) {
                        if (v_Loc == 10.0 || v_Loc == 11.0) discard;
                        if (v_Loc == 13.0 && u_Ae[0] >= -90.0 && u_Ae[0] < 90.0) discard;
                        if (v_Loc == 12.0 && (u_Ae[0] >= 90.0 || u_Ae[0] < -90.0)) discard;
                    }

                    if (u_Ae[1] >= 0.0) {
                        if (v_Loc == 12.0 || v_Loc == 13.0) discard;
                        if (v_Loc == 11.0 && u_Ae[0] >= -90.0 && u_Ae[0] < 90.0) discard;
                        if (v_Loc == 10.0 && (u_Ae[0] >= 90.0 || u_Ae[0] < -90.0)) discard;
                    }

                    if (u_Ae[1] < 0.0) {
                        if (v_Loc == 20.0 || v_Loc == 21.0) discard;
                        if (v_Loc == 23.0 && u_Ae[0] >= 0.0) discard;
                        if (v_Loc == 22.0 && u_Ae[0] < 0.0) discard;
                    }

                    if (u_Ae[1] >= 0.0) {
                        if (v_Loc == 22.0 || v_Loc == 23.0) discard;
                        if (v_Loc == 21.0 && u_Ae[0] >= 0.0) discard;
                        if (v_Loc == 20.0 && u_Ae[0] < 0.0) discard;
                    }

                    vec4 color = %s(u_Texture, v_Texcoord);
                    vec3 rgb = color.rgb * u_AmbientColor;
                    gl_FragColor = vec4(rgb, color.a);
                } 
            """ % (texcoord_type, sampler_type, texture_name)

            loc = np.repeat(np.array(loc, dtype=np.float32), 4)
            color = np.array(color, dtype=np.float32)

            if color.ndim == 1:
                color = np.tile(color, (len(text), 1))

            if bg is None:
                bg = [None for i in range(len(text))]

            im_arr, nim_arr, texcoord = list(), list(), list()
            rows_max, cols_max = 0, 0
            for i in range(len(text)):
                im = util.text2img(text[i], 64, color[i], bg=bg[i], padding=padding)
                rows_max = max(im.shape[0], rows_max)
                cols_max = max(im.shape[1], cols_max)
                im_arr.append(im)

                if PLATFORM == 'darwin':
                    texcoord.append(np.array([[0,0],[0,1],[1,1],[1,0]], dtype=np.float32))
                else:
                    texcoord.append(np.array([[0,0,i],[0,1,i],[1,1,i],[1,0,i]], dtype=np.float32))

            for im, agn in zip(im_arr, align):
                if im.shape[0] < rows_max:
                    n = rows_max - im.shape[0]
                    nu = n // 2
                    nd = n - nu

                    im = np.vstack((im, np.zeros((nd, *im.shape[1:]), dtype=np.uint8)))
                    if nu > 0:
                        im = np.vstack((np.zeros((nu, *im.shape[1:]), dtype=np.uint8), im))

                if im.shape[1] < cols_max:   
                    n = cols_max - im.shape[1]
                    if agn == 'left':
                        nl, nr = 0, n
                    elif agn == 'right':
                        nl, nr = n, 0
                    else:
                        nl = n // 2
                        nr = n - nl

                    if nr > 0:
                        im = np.hstack((im, np.zeros((im.shape[0], nr, im.shape[-1]), dtype=np.uint8)))
                    if nl > 0:
                        im = np.hstack((np.zeros((im.shape[0], nl, im.shape[-1]), dtype=np.uint8), im))

                nim_arr.append(im)

            box = np.stack(box, axis=0)
            for i in range(box.shape[0]):
                box_w = np.linalg.norm(box[i][0] - box[i][3])
                box_h = np.linalg.norm(box[i][0] - box[i][1])
                k_box, k_text = box_w/box_h, nim_arr[i].shape[1]/nim_arr[i].shape[0]

                if align[i] == 'left':
                    offset = (box[i][2]-box[i][1]) * k_text/k_box
                    box[i][2] = box[i][1] + offset
                    box[i][3] = box[i][0] + offset
                elif align[i] == 'right':
                    offset = (box[i][0] - box[i][3]) * k_text/k_box
                    box[i][0] = box[i][3] + offset
                    box[i][1] = box[i][2] + offset
                elif align[i] == 'center':
                    offset = (box[i][3] - box[i][0]) * (1-k_text/k_box)/2
                    box[i][0] += offset
                    box[i][1] += offset
                    box[i][2] -= offset
                    box[i][3] -= offset

            m_list = list()
            if PLATFORM == 'darwin':
                for i in range(len(nim_arr)):
                    texture = Texture(nim_arr[i], ttype=GL_TEXTURE_2D, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
                    m = Model(GL_QUADS, vshader, fshader, visible=True, opacity=True, inside=False)
                    m.set_vertex('a_Position', box[i], None)
                    m.set_texcoord('a_Texcoord', texcoord[i])
                    m.add_texture('u_Texture', texture)
                    m.set_argument('u_AmbientColor', (1.0,1.0,1.0))
                    m.set_proj_matrix('u_ProjMatrix')
                    m.set_view_matrix('u_ViewMatrix')
                    m.set_model_matrix('u_ModelMatrix')
                    m.set_argument('a_TickLoc', loc[i*4:i*4+4])
                    m.set_ae('u_Ae')
                    m.set_cull_mode(cull)
                    m_list.append(m)
            else:
                texcoord = np.vstack(texcoord)
                texture = Texture(np.stack(nim_arr), ttype=GL_TEXTURE_2D_ARRAY, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
                m = Model(GL_QUADS, vshader, fshader, visible=True, opacity=True, inside=False)
                m.set_vertex('a_Position', box, None)
                m.set_texcoord('a_Texcoord', texcoord)
                m.add_texture('u_Texture', texture)
                m.set_argument('u_AmbientColor', (1.0,1.0,1.0))
                m.set_proj_matrix('u_ProjMatrix')
                m.set_view_matrix('u_ViewMatrix')
                m.set_model_matrix('u_ModelMatrix')
                m.set_argument('a_TickLoc', loc)
                m.set_ae('u_Ae')
                m.set_cull_mode(cull)
                m_list.append(m)

            return m_list

        # 以下绘制网格
        # ----------------------------------------------------------------------------------------------------
        xs, ys = np.meshgrid(xx, yy[::-1])
        zs = np.ones(xs.shape) * zz[-1]
        xs_front = mesh2quad(xs, ys, zs)

        xs, ys = np.meshgrid(xx[::-1], yy[::-1])
        zs = np.ones(xs.shape) * zz[0]
        xs_back = mesh2quad(xs, ys, zs)

        xs, zs = np.meshgrid(xx, zz)
        ys = np.ones(xs.shape) * yy[-1]
        xs_top = mesh2quad(xs, ys, zs)

        xs, zs = np.meshgrid(xx, zz[::-1])
        ys = np.ones(xs.shape) * yy[0]
        xs_bottom = mesh2quad(xs, ys, zs)

        zs, ys = np.meshgrid(zz, yy[::-1])
        xs = np.ones(zs.shape) * xx[0]
        xs_left = mesh2quad(xs, ys, zs)

        zs, ys = np.meshgrid(zz[::-1], yy[::-1])
        xs = np.ones(zs.shape) * xx[-1]
        xs_right = mesh2quad(xs, ys, zs)

        vs = np.vstack((xs_front, xs_back, xs_top, xs_bottom, xs_left, xs_right))
        light = BaseLight()
        bg = np.where(self.bg>0.5, self.bg-0.05, self.bg)
        bg = np.where(bg<0.5, bg+0.05, bg)
        self._surface(vs, GL_QUADS, color=[*self.fg, 0.3], fill=False, cull='front', opacity=False, light=light, name=name)
        self._surface(vs, GL_QUADS, color=[*bg, 1.0], cull='front', opacity=False, light=light, name=name)
        self._surface(vs, GL_QUADS, color=[*self.fg, 0.3], fill=False, cull='front', opacity=False, light=light, name=name)

        # 以下绘制标注文本
        # ----------------------------------------------------------------------------------------------------
        dx = xx[2] - xx[1]
        dy = yy[2] - yy[1]
        dz = zz[2] - zz[1]
        h = min(dx, dy, dz) * size/200 # 标注文字高度
        dh, qh, hh, gh = 0.1*h, 0.25*h, 0.5*h, 1.1*h
        text, box, loc, align = list(), list(), list(), list()

        for x in xx[1:-1]:
            x_str = xf(x)
            text.extend([x_str, x_str, x_str, x_str])
            align.extend(['center', 'center', 'center', 'center'])

            if self.haxis == 'z':
                loc.extend([10, 11, 12, 13])
                box.append([[x-dx,yy[-1],zz[-1]+gh], [x-dx,yy[-1],zz[-1]+dh], [x+dx,yy[-1],zz[-1]+dh], [x+dx,yy[-1],zz[-1]+gh]])
                box.append([[x+dx,yy[0],zz[-1]+gh], [x+dx,yy[0],zz[-1]+dh], [x-dx,yy[0],zz[-1]+dh], [x-dx,yy[0],zz[-1]+gh]])
                box.append([[x-dx,yy[-1],zz[0]-dh], [x-dx,yy[-1],zz[0]-gh], [x+dx,yy[-1],zz[0]-gh], [x+dx,yy[-1],zz[0]-dh]])
                box.append([[x+dx,yy[0],zz[0]-dh], [x+dx,yy[0],zz[0]-gh], [x-dx,yy[0],zz[0]-gh], [x-dx,yy[0],zz[0]-dh]])
            else:
                loc.extend([10, 11, 12, 13])
                box.append([[x-dx,yy[-1]+gh,zz[0]], [x-dx,yy[-1]+dh,zz[0]], [x+dx,yy[-1]+dh,zz[0]], [x+dx,yy[-1]+gh,zz[0]]])
                box.append([[x+dx,yy[-1]+gh,zz[-1]], [x+dx,yy[-1]+dh,zz[-1]], [x-dx,yy[-1]+dh,zz[-1]], [x-dx,yy[-1]+gh,zz[-1]]])
                box.append([[x-dx,yy[0]-dh,zz[0]], [x-dx,yy[0]-gh,zz[0]], [x+dx,yy[0]-gh,zz[0]], [x+dx,yy[0]-dh,zz[0]]])
                box.append([[x+dx,yy[0]-dh,zz[-1]], [x+dx,yy[0]-gh,zz[-1]], [x-dx,yy[0]-gh,zz[-1]], [x-dx,yy[0]-dh,zz[-1]]])

        for y in yy[1:-1]:
            y_str = yf(y)
            text.extend([y_str, y_str, y_str, y_str])

            if self.haxis == 'z':
                loc.extend([20, 21, 22, 23])
                align.extend(['center', 'center', 'center', 'center'])
                box.append([[xx[0],y-dy,zz[-1]+gh], [xx[0],y-dy,zz[-1]+dh], [xx[0],y+dy,zz[-1]+dh], [xx[0],y+dy,zz[-1]+gh]])
                box.append([[xx[-1],y+dy,zz[-1]+gh], [xx[-1],y+dy,zz[-1]+dh], [xx[-1],y-dy,zz[-1]+dh], [xx[-1],y-dy,zz[-1]+gh]])
                box.append([[xx[0],y-dy,zz[0]-dh], [xx[0],y-dy,zz[0]-gh], [xx[0],y+dy,zz[0]-gh], [xx[0],y+dy,zz[0]-dh]])
                box.append([[xx[-1],y+dy,zz[0]-dh], [xx[-1],y+dy,zz[0]-gh], [xx[-1],y-dy,zz[0]-gh], [xx[-1],y-dy,zz[0]-dh]])
            else:
                loc.extend([0, 1, 2, 3])
                align.extend(['right', 'right', 'right', 'right'])
                box.append([[xx[0],y+hh,zz[-1]+dz], [xx[0],y-hh,zz[-1]+dz], [xx[0],y-hh,zz[-1]+qh], [xx[0],y+hh,zz[-1]+qh]])
                box.append([[xx[0]-dx,y+hh,zz[0]], [xx[0]-dx,y-hh,zz[0]], [xx[0]-qh,y-hh,zz[0]], [xx[0]-qh,y+hh,zz[0]]])
                box.append([[xx[-1],y+hh,zz[0]-dz], [xx[-1],y-hh,zz[0]-dz], [xx[-1],y-hh,zz[0]-qh], [xx[-1],y+hh,zz[0]-qh]])
                box.append([[xx[-1]+dx,y+hh,zz[-1]], [xx[-1]+dx,y-hh,zz[-1]], [xx[-1]+qh,y-hh,zz[-1]], [xx[-1]+qh,y+hh,zz[-1]]])

        for z in zz[1:-1]:
            z_str = zf(z)
            text.extend([z_str, z_str, z_str, z_str])

            if self.haxis == 'z':
                loc.extend([0, 1, 2, 3])
                align.extend(['right', 'right', 'right', 'right'])
                box.append([[xx[0],yy[0]-dy,z+hh], [xx[0],yy[0]-dy,z-hh], [xx[0],yy[0]-qh,z-hh], [xx[0],yy[0]-qh,z+hh]])
                box.append([[xx[0]-dx,yy[-1],z+hh], [xx[0]-dx,yy[-1],z-hh], [xx[0]-qh,yy[-1],z-hh], [xx[0]-qh,yy[-1],z+hh]])
                box.append([[xx[-1],yy[-1]+dy,z+hh], [xx[-1],yy[-1]+dy,z-hh], [xx[-1],yy[-1]+qh,z-hh], [xx[-1],yy[-1]+qh,z+hh]])
                box.append([[xx[-1]+dx,yy[0],z+hh], [xx[-1]+dx,yy[0],z-hh], [xx[-1]+qh,yy[0],z-hh], [xx[-1]+qh,yy[0],z+hh]])
            else:
                loc.extend([20, 21, 22, 23])
                align.extend(['center', 'center', 'center', 'center'])
                box.append([[xx[0],yy[-1]+gh,z+dz], [xx[0],yy[-1]+dh,z+dz], [xx[0],yy[-1]+dh,z-dz], [xx[0],yy[-1]+gh,z-dz]])
                box.append([[xx[-1],yy[-1]+gh,z-dz], [xx[-1],yy[-1]+dh,z-dz], [xx[-1],yy[-1]+dh,z+dz], [xx[-1],yy[-1]+gh,z+dz]])
                box.append([[xx[0],yy[0]-dh,z+dz], [xx[0],yy[0]-gh,z+dz], [xx[0],yy[0]-gh,z-dz], [xx[0],yy[0]-dh,z-dz]])
                box.append([[xx[-1],yy[0]-dh,z-dz], [xx[-1],yy[0]-gh,z-dz], [xx[-1],yy[0]-gh,z+dz], [xx[-1],yy[0]-dh,z+dz]])

        text.extend([xlabel, xlabel, xlabel, xlabel])
        align.extend(['center', 'center', 'center', 'center'])
        x = (xx[-1]+xx[-2])/2
        if self.haxis == 'z':
            loc.extend([10, 11, 12, 13])
            box.append([[x,yy[-1],zz[-1]+gh], [x,yy[-1],zz[-1]+dh], [x+h,yy[-1],zz[-1]+dh], [x+h,yy[-1],zz[-1]+gh]])
            box.append([[x+h,yy[0],zz[-1]+gh], [x+h,yy[0],zz[-1]+dh], [x,yy[0],zz[-1]+dh], [x,yy[0],zz[-1]+gh]])
            box.append([[x,yy[-1],zz[0]-dh], [x,yy[-1],zz[0]-gh], [x+h,yy[-1],zz[0]-gh], [x+h,yy[-1],zz[0]-dh]])
            box.append([[x+h,yy[0],zz[0]-dh], [x+h,yy[0],zz[0]-gh], [x,yy[0],zz[0]-gh], [x,yy[0],zz[0]-dh]])
        else:
            loc.extend([10, 11, 12, 13])
            box.append([[x,yy[-1]+gh,zz[0]], [x,yy[-1]+dh,zz[0]], [x+h,yy[-1]+dh,zz[0]], [x+h,yy[-1]+gh,zz[0]]])
            box.append([[x+h,yy[-1]+gh,zz[-1]], [x+h,yy[-1]+dh,zz[-1]], [x,yy[-1]+dh,zz[-1]], [x,yy[-1]+gh,zz[-1]]])
            box.append([[x,yy[0]-dh,zz[0]], [x,yy[0]-gh,zz[0]], [x+h,yy[0]-gh,zz[0]], [x+h,yy[0]-dh,zz[0]]])
            box.append([[x+h,yy[0]-dh,zz[-1]], [x+h,yy[0]-gh,zz[-1]], [x,yy[0]-gh,zz[-1]], [x,yy[0]-dh,zz[-1]]])

        text.extend([ylabel, ylabel, ylabel, ylabel])
        if self.haxis == 'z':
            align.extend(['center', 'center', 'center', 'center'])
            y = (yy[-1]+yy[-2])/2
            loc.extend([20, 21, 22, 23])
            box.append([[xx[0],y,zz[-1]+gh], [xx[0],y,zz[-1]+dh], [xx[0],y+h,zz[-1]+dh], [xx[0],y+h,zz[-1]+gh]])
            box.append([[xx[-1],y+h,zz[-1]+gh], [xx[-1],y+h,zz[-1]+dh], [xx[-1],y,zz[-1]+dh], [xx[-1],y,zz[-1]+gh]])
            box.append([[xx[0],y,zz[0]-dh], [xx[0],y,zz[0]-gh], [xx[0],y+h,zz[0]-gh], [xx[0],y+h,zz[0]-dh]])
            box.append([[xx[-1],y+h,zz[0]-dh], [xx[-1],y+h,zz[0]-gh], [xx[-1],y,zz[0]-gh], [xx[-1],y,zz[0]-dh]])
        else:
            align.extend(['right', 'right', 'right', 'right'])
            y = (yy[-1]+yy[-2])/2
            loc.extend([0, 1, 2, 3])
            box.append([[xx[0],y+h,zz[-1]+gh], [xx[0],y,zz[-1]+gh], [xx[0],y,zz[-1]+dh], [xx[0],y+h,zz[-1]+dh]])
            box.append([[xx[0]-gh,y+h,zz[0]], [xx[0]-gh,y,zz[0]], [xx[0]-dh,y,zz[0]], [xx[0]-dh,y+h,zz[0]]])
            box.append([[xx[-1],y+h,zz[0]-gh], [xx[-1],y,zz[0]-gh], [xx[-1],y,zz[0]-dh], [xx[-1],y+h,zz[0]-dh]])
            box.append([[xx[-1]+gh,y+h,zz[-1]], [xx[-1]+gh,y,zz[-1]], [xx[-1]+dh,y,zz[-1]], [xx[-1]+dh,y+h,zz[-1]]])

        text.extend([zlabel, zlabel, zlabel, zlabel])
        if self.haxis == 'z':
            align.extend(['right', 'right', 'right', 'right'])
            z = (zz[-1]+zz[-2])/2
            loc.extend([0, 1, 2, 3])
            box.append([[xx[0],yy[0]-gh,z+h], [xx[0],yy[0]-gh,z], [xx[0],yy[0]-dh,z], [xx[0],yy[0]-dh,z+h]])
            box.append([[xx[0]-gh,yy[-1],z+h], [xx[0]-gh,yy[-1],z], [xx[0]-dh,yy[-1],z], [xx[0]-dh,yy[-1],z+h]])
            box.append([[xx[-1],yy[-1]+gh,z+h], [xx[-1],yy[-1]+gh,z], [xx[-1],yy[-1]+dh,z], [xx[-1],yy[-1]+dh,z+h]])
            box.append([[xx[-1]+gh,yy[0],z+h], [xx[-1]+gh,yy[0],z], [xx[-1]+dh,yy[0],z], [xx[-1]+dh,yy[0],z+h]])
        else:
            align.extend(['center', 'center', 'center', 'center'])
            z = (zz[-1]+zz[-2])/2
            loc.extend([20, 21, 22, 23])
            box.append([[xx[0],yy[-1]+gh,z+h], [xx[0],yy[-1]+dh,z+h], [xx[0],yy[-1]+dh,z], [xx[0],yy[-1]+gh,z]])
            box.append([[xx[-1],yy[-1]+gh,z], [xx[-1],yy[-1]+dh,z], [xx[-1],yy[-1]+dh,z+h], [xx[-1],yy[-1]+gh,z+h]])
            box.append([[xx[0],yy[0]-dh,z+h], [xx[0],yy[0]-gh,z+h], [xx[0],yy[0]-gh,z], [xx[0],yy[0]-dh,z]])
            box.append([[xx[-1],yy[0]-dh,z], [xx[-1],yy[0]-gh,z], [xx[-1],yy[0]-gh,z+h], [xx[-1],yy[0]-dh,z+h]])

        color = [self.fg for i in range(len(box)-12)] + [self.bg for i in range(12)]
        bg = [None for i in range(len(box)-12)] + [self.fg for i in range(12)]

        for m in text3d_ticks(text, box, color, loc, 'back', align, bg, 8):
            self.model(m, name=name)

    def xrange(self, range_tuple):
        """设置x轴范围"""

        self._set_range(r_x=range_tuple)

    def yrange(self, range_tuple):
        """设置y轴范围"""

        self._set_range(r_y=range_tuple)

    def zrange(self, range_tuple):
        """设置z轴范围"""

        self._set_range(r_z=range_tuple)

    def cruise(self, func):
        """设置相机巡航函数
        func        - 以时间t（毫秒）为参数的函数，返回包含下述key的字典
            azim        - 方位角：None或表达式
            elev        - 高度角：None或表达式
            dist        - 相机到OES坐标系原定的距离：None或表达式
        """

        if hasattr(func, '__call__'):
            self.cruise_func = func
            self.alive = True

    def axes(self, name=None):
        """坐标轴

        name        - 部件名
        """

        self.expost.update({'axes': {'name': uuid.uuid1().hex if name is None else name}})

    def grid(self, **kwds):
        """网格和刻度
        kwds        - 关键字参数
            size            - 文本字号，默认32
            xlabel          - x轴名称
            ylabel          - y轴名称
            zlabel          - z轴名称
            xf              - x轴标注格式化函数
            yf              - y轴标注格式化函数
            zf              - z轴标注格式化函数
            name            - 部件名
        """

        for key in kwds:
            if key not in ['size', 'xlabel', 'ylabel', 'zlabel', 'xf', 'yf', 'zf', 'name']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        self.expost.update({'grid': {
            'size':     kwds.get('size', 32),
            'xlabel':   kwds.get('xlabel', 'X'),
            'ylabel':   kwds.get('ylabel', 'Y'),
            'zlabel':   kwds.get('zlabel', 'Z'),
            'xf':       kwds.get('xf', str),
            'yf':       kwds.get('yf', str),
            'zf':       kwds.get('zf', str),
            'name':     kwds.get('name', uuid.uuid1().hex)
        }})

    def title(self, title, size=32, color=None, family=None, weight='normal'):
        """设置标题

        title       - 标题文本
        size        - 字号：整型，默认32
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        family      - 字体：None表示当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        """

        color = self.fg if color is None else self._format_color(color)
        im_text = util.text2img(title, 64, color, family=family, weight=weight)
        texture = Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        texcoord = np.array([[0,0],[0,1],[1,1],[1,0]], dtype=np.float32)
        h = size/48
 
        box = np.array([[-1,h-0.6,0],[-1,-0.6,0],[1,-0.6,0],[1,h-0.6,0]], dtype=np.float32)
        box_width = np.linalg.norm(box[0] - box[3])
        box_height = np.linalg.norm(box[0] - box[1])
        k_box, k_text = box_width/box_height, im_text.shape[1]/im_text.shape[0]
        offset = (box[3] - box[0])*(1-k_text/k_box)/2
        box[0] += offset
        box[1] += offset
        box[2] -= offset
        box[3] -= offset

        vs = [[-0.8,-0.9,0], [0,-0.9,0], [0.8,-0.9,0]]
        color = [[*color[:3],0.2], [*color[:3],1.0], [*color[:3],0.2]]

        light = BaseLight(fixed=True)
        m_text = light.get_model(GL_QUADS, box, texture=texture, texcoord=texcoord, opacity=False, inside=False)
        m_line = light.get_model(GL_LINE_STRIP, vs, color=color, lw=1)
        m_text.verify()
        m_line.verify()
        self.models[1].update({'caption_text': m_text})
        self.models[1].update({'caption_line': m_line})

    def colorbar(self, data, cm='viridis', ff=str, endpoint=True):
        """调色板

        data        - 值域范围或刻度序列：长度大于1的元组或列表
        cm          - 调色板名称
        kwds        - 关键字参数
        ff          - 刻度标注格式化函数
        endpoint    - 刻度是否包含值域范围的两个端点值
        """
 
        light = BaseLight(fixed=True)
        left, right, top, bottom = -0.8, -0.3, 0.8, -0.8
        w, h = 0.2, 0.025 # 刻度线长度、标注文本高度

        # 绘制颜色条
        # --------------------------------------------------------------------
        vs_bar = list()
        colors = util.get_cm_colors(cm)
        qs = np.linspace(bottom, top, len(colors)+1)
        for i in range(len(colors)):
            vs_bar.extend([[left,qs[i+1],0], [left,qs[i],0], [right,qs[i],0], [right,qs[i+1],0]])

        vs_bar = np.array(vs_bar, dtype=np.float32)
        color_bar = np.repeat(np.array(colors, dtype=np.float32), 4, axis=0)

        m_bar = light.get_model(GL_QUADS, vs_bar, color=color_bar, inside=False)
        m_bar.verify()
        self.models[2].update({'cb_bar': m_bar})

        # 绘制刻度线
        # --------------------------------------------------------------------
        dmin, dmax = data[0], data[-1]
        if len(data) == 2:
            data = self._get_series(data[0], data[-1], endpoint)

        vs_line, ys = list(), list()
        for t in data:
            y = (top-bottom)*(t-dmin)/(dmax-dmin) + bottom
            vs_line.extend([[right,y,0], [right+w,y,0]])
            ys.append(y)

        vs_line = np.array(vs_line, dtype=np.float32)
        color_line = self._format_color(self.fg, vs_line.shape[0])

        m_line = light.get_model(GL_LINES, vs_line, color=color_line, inside=False)
        m_line.verify()
        self.models[2].update({'cb_line': m_line})

        # 绘制刻度文本
        # --------------------------------------------------------------------
        im_arr, tcrd_arr, box = list(), list(), list()
        rows_max, cols_max = 0, 0
        for i in range(len(data)):
            im = util.text2img(ff(data[i]), 64, self.fg)
            rows_max = max(im.shape[0], rows_max)
            cols_max = max(im.shape[1], cols_max)
            im_arr.append(im)

            tcrd_arr.append(np.array([[0,0,i],[0,1,i],[1,1,i],[1,0,i]], dtype=np.float32))
            box.append([[0,ys[i]+h,0], [0,ys[i]-h,0], [1,ys[i]-h,0], [1,ys[i]+h,0]])
        
        nim_arr = list()
        for im in im_arr:
            if im.shape[0] < rows_max:
                n = rows_max - im.shape[0]
                nu = n // 2
                nd = n - nu
                
                im = np.vstack((im, np.zeros((nd, *im.shape[1:]), dtype=np.uint8)))
                if nu > 0:
                    im = np.vstack((np.zeros((nu, *im.shape[1:]), dtype=np.uint8), im))
            
            if im.shape[1] < cols_max:   
                n = cols_max - im.shape[1]
                nl = n // 2
                nr = n - nl
                
                im = np.hstack((im, np.zeros((im.shape[0], nr, im.shape[-1]), dtype=np.uint8)))
                if nl > 0:
                    im = np.hstack((np.zeros((im.shape[0], nl, im.shape[-1]), dtype=np.uint8), im))
            
            nim_arr.append(im)

        box = np.stack(box, axis=0)
        for i in range(box.shape[0]):
            box_width = np.linalg.norm(box[i][0] - box[i][3])
            box_height = np.linalg.norm(box[i][0] - box[i][1])
            k_box, k_text = box_width/box_height, nim_arr[i].shape[1]/nim_arr[i].shape[0]

            offset = (box[i][2]-box[i][1])*k_text/k_box
            if PLATFORM == 'darwin':
                offset *= 3.5

            box[i][2] = box[i][1] + offset
            box[i][3] = box[i][0] + offset

        if PLATFORM == 'darwin':
            for i in range(len(nim_arr)):
                texture = Texture(nim_arr[i], ttype=GL_TEXTURE_2D, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
                m_label = light.get_model(GL_QUADS, box[i], texture=texture, texcoord=tcrd_arr[i][:,:2], opacity=False, inside=False)
                m_label.verify()
                self.models[2].update({'cb_label_%d'%i: m_label})
        else:
            texture = Texture(np.stack(nim_arr), ttype=GL_TEXTURE_2D_ARRAY, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
            texcoord = np.vstack(tcrd_arr)

            m_label = light.get_model(GL_QUADS, box, texture=texture, texcoord=texcoord, opacity=False, inside=False)
            m_label.verify()
            self.models[2].update({'cb_label': m_label})

    def model(self, m, name=None):
        """添加模型"""

        m.verify()

        if m.inside:
            self._set_range(r_x=m.r_x, r_y=m.r_y, r_z=m.r_z)

        if m.alive:
            self.alive = True

        mid = uuid.uuid1().hex
        if name is None:
            name = mid
        
        m.name = name
        self.models[0].update({mid: m})

        if name in self.widgets:
            self.widgets[name].append(mid)
        else:
            self.widgets.update({name:[mid]})

    def text(self, text, pos, **kwds):
        """2D文字

        text        - 文本字符串
        pos         - 文本位置：元组、列表或numpy数组，shape=(2|3,)
        kwds        - 关键字参数
            color       - 文本颜色：浮预定义颜色、十六进制颜色，或者点型元组、列表或numpy数组，None表示背景色的对比色
            size        - 字号：整型，默认32
            align       - 水平对齐方式：'left'-左对齐（默认），'center'-水平居中，'right'-右对齐
            valign      - 垂直对齐方式：'bottom'-底部对齐（默认），'middle'-垂直居中，'top'-顶部对齐
            family      - 字体：None表示当前默认的字体
            weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            slide       - 幻灯片函数，默认None
            ambient     - 环境光，默认(1.0,1.0,1.0)
            name        - 模型或部件名
        """

        keys = ['color', 'size', 'align', 'valign', 'family', 'weight', 'visible', 'inside', 'slide', 'ambient', 'name']
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)

        color = kwds.get('color', self.fg)
        size = kwds.get('size', 32)
        align = kwds.get('align', 'left')
        valign = kwds.get('valign', 'bottom')
        family = kwds.get('family')
        weight = kwds.get('weight', 'normal')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        slide = kwds.get('slide')
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        name = kwds.get('name')

        box = np.tile(np.array(pos, dtype=np.float32), (4,1))
        texcoord = np.array([[0,0],[0,1],[1,0],[1,1]], dtype=np.float32)
        align = {'left':0, 'center':1, 'right':2}.get(align, 0)*3 + {'top':0, 'middle':1, 'bottom':2}.get(valign, 2)

        im_text = util.text2img(text, size, self._format_color(color), bg=None, family=family, weight=weight)
        texture = Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        tsize = (size*im_text.shape[1]/im_text.shape[0], size)
        light = Text2dLight(ambient)
        vid = np.array([0,1,2,3], dtype=np.float32)

        self.model(light.get_model(GL_TRIANGLE_STRIP, box, 
            texture     = texture, 
            texcoord    = texcoord, 
            align       = align, 
            tsize       = tsize,
            vid         = vid,
            visible     = visible,
            inside      = inside,
            slide       = slide
        ), name)

    def scatter(self, vs, **kwds):
        """散列点

        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            size        - 点的大小：数值或数值型元组、列表或numpy数组
            data        - 数据集：元组、列表或numpy数组，shape=(n,)
            cm          - 调色板
            texture     - 纹理图片，或2D纹理对象
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient     - 环境光，默认(1.0,1.0,1.0)
            name        - 模型或部件名
        """

        keys = ['color', 'size', 'data', 'cm', 'texture', 'visible', 'inside', 'slide', 'transform', 'ambient', 'name']
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)

        color = kwds.get('color')
        size = kwds.get('size', 3.0)
        data = kwds.get('data')
        cm = kwds.get('cm', 'viridis')
        texture = kwds.get('texture')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        name = kwds.get('name')

        light = ScatterLight(ambient)
        vs = np.array(vs, dtype=np.float32)
        size = np.ones(vs.shape[0], dtype=np.float32) * size if isinstance(size, (int, float)) else np.float32(size)

        if self.haxis=='z':
            idx = np.argsort(-vs[...,1])
        elif vs.shape[1] == 3:
            idx = np.argsort(vs[...,2])
        else:
            idx = np.arange(vs.shape[0])

        if PLATFORM == 'darwin' and not texture is None:
            texture = None
            print('MacOS平台不支持点精灵模式')
            
        if not texture is None:
            if not isinstance(texture, Texture):
                texture = Texture(texture)
            color = None
        elif data is None:
            color = self._format_color(color, vs.shape[0])[idx]
        else:
            color = util.cmap(np.array(data), cm)[idx]

        self.model(light.get_model(GL_POINTS, vs[idx], 
            color       = color, 
            psize       = size[idx],
            texture     = texture,
            visible     = visible,
            inside      = inside,
            slide       = slide,
            transform   = transform
        ), name)

    def line(self, vs, **kwds):
        """线段

        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            data        - 数据集：元组、列表或numpy数组，shape=(n,)
            cm          - 调色板
            width       - 线宽：0.0~10.0之间，None使用默认设置
            stipple     - 线型：整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None使用默认设置
            pair        - 顶点两两成对绘制多条线段，默认False
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient     - 环境光，默认(1.0,1.0,1.0)
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        data = kwds.pop('data') if 'data' in kwds else None
        cm = kwds.pop('cm') if 'cm' in kwds else 'viridis'
        width = kwds.pop('width') if 'width' in kwds else None
        stipple = kwds.pop('stipple') if 'stipple' in kwds else None
        pair = kwds.pop('pair') if 'pair' in kwds else False

        gltype = GL_LINES if pair else GL_LINE_STRIP
        if not data is None:
            color = util.cmap(np.array(data), cm)

        self._line(vs, gltype, color, width, stipple, **kwds)

    def surface(self, vs, **kwds):
        """由三角面（默认）或四角面构成的曲面

        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            data        - 数据集：元组、列表或numpy数组，shape=(n,)
            cm          - 调色板
            texture     - 纹理图片，或2D/2DArray/3D纹理对象
            texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
            quad        - 使用四角面构成曲面，默认False（使用三角面）
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认True（不透明）
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        data = kwds.pop('data') if 'data' in kwds else None
        cm = kwds.pop('cm') if 'cm' in kwds else 'viridis'
        texture = kwds.pop('texture') if 'texture' in kwds else None
        texcoord = kwds.pop('texcoord') if 'texcoord' in kwds else None
        quad = kwds.pop('quad') if 'quad' in kwds else False
        gltype = GL_QUADS if quad else GL_TRIANGLES

        if not texture is None and not texcoord is None:
            self._surface(vs, gltype, texture=texture, texcoord=texcoord, **kwds)
        else:
            if not data is None:
                color = util.cmap(np.array(data), cm)
            self._surface(vs, gltype, color=color, **kwds)

    def mesh(self, xs, ys, zs, **kwds):
        """网格面

        xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)，m为网格行数，n为网格列数
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            data        - 数据集：元组、列表或numpy数组，shape=(m,n)
            cm          - 调色板
            texture     - 纹理图片，或2D纹理对象
            quad        - 使用四角面构成网格面，默认False（使用三角面）
            ccw         - 顶点逆时针排序的面为正面，默认True
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认不透明
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        data = kwds.pop('data') if 'data' in kwds else None
        cm = kwds.pop('cm') if 'cm' in kwds else 'viridis'
        texture = kwds.pop('texture') if 'texture' in kwds else None
        quad = kwds.pop('quad') if 'quad' in kwds else False
        ccw = kwds.pop('ccw') if 'ccw' in kwds else True
        gltype = GL_QUADS if quad else GL_TRIANGLES

        if not texture is None:
            self._mesh(xs, ys, zs, gltype, texture=texture, ccw=ccw, **kwds)
        else:
            if not data is None:
                color = util.cmap(np.array(data), cm)
            self._mesh(xs, ys, zs, gltype, color=color, ccw=ccw, **kwds)

    def text3d(self, text, box, **kwds):
        """3D文字

        text        - 文本字符串
        box         - 文本显示区域：左上、左下、右下、右上4个点的坐标，浮点型元组、列表或numpy数组，shape=(4,2|3)
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            bg          - 背景色，None表示背景透明
            align       - 对齐方式：'left'-左对齐（默认），'center'-水平居中，'right'-右对齐，'fill'-填充
            family      - 字体：None表示当前默认的字体
            weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
            size        - 字号：整型，默认64。此参数影响文本显示质量，不改变文本大小
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            light       - 光照模型（默认基础光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else self.fg
        bg = kwds.pop('bg') if 'bg' in kwds else None
        align = kwds.pop('align') if 'align' in kwds else 'left'
        family = kwds.pop('family') if 'family' in kwds else None
        weight = kwds.pop('weight') if 'weight' in kwds else 'normal'
        size = kwds.pop('size') if 'size' in kwds else 64

        if 'light' not in kwds: 
            kwds.update({'light': BaseLight()})

        im_text = util.text2img(text, size, self._format_color(color), bg=bg, family=family, weight=weight)
        texture = Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        texcoord = np.array([[0,0],[0,1],[1,1],[1,0]], dtype=np.float32)

        box = np.array(box, dtype=np.float32)
        box_width = np.linalg.norm(box[0] - box[3])
        box_height = np.linalg.norm(box[0] - box[1])
        k_box, k_text = box_width/box_height, im_text.shape[1]/im_text.shape[0]

        if align == 'left':
            offset = (box[2]-box[1])*k_text/k_box
            box[2] = box[1] + offset
            box[3] = box[0] + offset
        elif align == 'right':
            offset = (box[0] - box[3])*k_text/k_box
            box[0] = box[3] + offset
            box[1] = box[2] + offset
        elif align == 'center':
            offset = (box[3] - box[0])*(1-k_text/k_box)/2
            box[0] += offset
            box[1] += offset
            box[2] -= offset
            box[3] -= offset

        self._surface(box, GL_QUADS, texture=texture, texcoord=texcoord, **kwds)

    def cone(self, spire, center, r, **kwds):
        """圆锥

        spire       - 锥尖：元组、列表或numpy数组
        center      - 锥底圆心：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            arc         - 弧度角范围：默认0°~360°
            cell        - 网格精度：默认5°
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认不透明
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        arc = kwds.pop('arc') if 'arc' in kwds else (0,360)
        cell = kwds.pop('cell') if 'cell' in kwds else 5

        spire = np.array(spire)
        center = np.array(center)
        m_rotate = util.y2v(spire - center)

        arc_0, arc_1, cell = np.radians(arc[0]), np.radians(arc[1]), np.radians(cell)
        slices = int(abs(arc_0-arc_1)/cell) + 1

        theta = np.linspace(arc_0, arc_1, slices)
        xs = r * np.cos(theta)
        zs = -r * np.sin(theta)
        ys = np.zeros_like(theta)

        vs = np.stack((xs,ys,zs), axis=1)
        vs = np.dot(vs, m_rotate) + center
        vs_c = np.vstack((spire, vs))
        color = self._format_color(color)

        self._surface(vs_c, GL_TRIANGLE_FAN, color=color, **kwds)

    def cylinder(self, c1, c2, r, **kwds):
        """柱

        c1          - 圆柱端面圆心：元组、列表或numpy数组
        c2          - 圆柱端面圆心：元组、列表或numpy数组
        r           - 圆柱半径：浮点型
        kwds        - 关键字参数
            color       - 颜色：浮点型元组、列表或numpy数组
            arc         - 弧度角范围：默认0°~360°
            cell        - 网格精度：默认5°
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认不透明
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        arc = kwds.pop('arc') if 'arc' in kwds else (0,360)
        cell = kwds.pop('cell') if 'cell' in kwds else 5

        c1 = np.array(c1)
        c2 = np.array(c2)
        m_rotate = util.y2v(c1 - c2)

        arc_0, arc_1, cell = np.radians(arc[0]), np.radians(arc[1]), np.radians(cell)
        slices = int(abs(arc_0-arc_1)/cell) + 1

        theta = np.linspace(arc_0, arc_1, slices)
        xs = r * np.cos(theta)
        zs = -r * np.sin(theta)
        ys = np.zeros_like(theta)
        vs = np.stack((xs,ys,zs), axis=1)
        vs = np.dot(vs, m_rotate)
        vs = np.stack((vs+c1, vs+c2), axis=0)

        xs = vs[..., 0]
        ys = vs[..., 1]
        zs = vs[..., 2]

        self.mesh(xs, ys, zs, color=color, **kwds)

    def sphere(self, center, r, **kwds):
        """由经纬度网格生成的球

        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            vec         - 指向北极的向量
            uarc        - u方向范围：默认0°~360°
            varc        - v方向范围：默认-90°~90°
            cell        - 网格精度：默认5°
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认不透明
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        vec = kwds.pop('vec') if 'vec' in kwds else (0,1,0)
        uarc = kwds.pop('uarc') if 'uarc' in kwds else (0,360)
        varc = kwds.pop('varc') if 'varc' in kwds else (-90,90)
        cell = kwds.pop('cell') if 'cell' in kwds else 5

        u0, u1 = np.radians(uarc[0]), np.radians(uarc[1])
        v0, v1 = np.radians(varc[1]), np.radians(varc[0])
        cell = np.radians(cell)
        ulen, vlen = int(abs(u0-u1)/cell)+1, int(abs(v0-v1)/cell)+1
        gv, gu = np.mgrid[v0:v1:complex(0,vlen), u0:u1:complex(0,ulen)]

        ys = r * np.sin(gv)
        xs = r * np.cos(gv)*np.cos(gu)
        zs = -r * np.cos(gv)*np.sin(gu)

        m_rotate = util.y2v(vec)
        vs = np.dstack((xs, ys, zs))
        vs = np.dot(vs, m_rotate) + np.array(center)

        self._mesh(vs[...,0], vs[...,1], vs[...,2], GL_QUADS, color=color, ccw=True, **kwds)

    def circle(self, center, r, **kwds):
        """圆

        center      - 圆心：元组、列表或numpy数组
        r           - 半径：浮点型
        kwds        - 关键字参数
            color       - 颜色：浮点型元组、列表或numpy数组
            arc         - 弧度角范围：默认0°~360°
            cell        - 网格精度：默认5°
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认不透明
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        vec = kwds.pop('vec') if 'vec' in kwds else (0,1,0)
        arc = kwds.pop('arc') if 'arc' in kwds else (0,360)
        cell = kwds.pop('cell') if 'cell' in kwds else 5

        center = np.array(center)
        m_rotate = util.y2v(vec)

        arc_0, arc_1, cell = np.radians(arc[0]), np.radians(arc[1]), np.radians(cell)
        slices = int(abs(arc_0-arc_1)/cell) + 1

        theta = np.linspace(arc_0, arc_1, slices)
        xs = r * np.cos(theta)
        zs = -r * np.sin(theta)
        ys = np.zeros_like(theta)

        vs = np.stack((xs,ys,zs), axis=1)
        vs = np.dot(vs, m_rotate) + center
        vs = np.vstack((center, vs))

        self._surface(vs, GL_TRIANGLE_FAN, color=color, **kwds)

    def cube(self, center, side, **kwds):
        """立方体

        center      - 中心坐标，元组、列表或numpy数组
        side        - 棱长：数值或长度为3的元组、列表、numpy数组
        kwds        - 关键字参数
            color       - 颜色：浮点型元组、列表或numpy数组
            vec         - 立方体上表面法向量
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认不透明
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        vec = kwds.pop('vec') if 'vec' in kwds else (0,1,0)

        if isinstance(side, (tuple, list, np.ndarray)):
            x, y, z = side[0]/2, side[1]/2, side[2]/2
        else:
            x, y, z = side/2, side/2, side/2

        vs_front = np.array(((-x,y,z),(-x,-y,z),(x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)))
        vs_back = np.array(((x,y,-z),(x,-y,-z),(-x,-y,-z),(-x,-y,-z),(-x,y,-z),(x,y,-z)))
        vs_top = np.array(((-x,y,-z),(-x,y,z),(x,y,z),(x,y,z),(x,y,-z),(-x,y,-z)))
        vs_bottom = np.array(((-x,-y,z),(-x,-y,-z),(x,-y,-z),(x,-y,-z),(x,-y,z),(-x,-y,z)))
        vs_left = np.array(((-x,y,-z),(-x,-y,-z),(-x,-y,z),(-x,-y,z),(-x,y,z),(-x,y,-z)))
        vs_right = np.array(((x,y,z),(x,-y,z),(x,-y,-z),(x,-y,-z),(x,y,-z),(x,y,z)))

        vs = np.vstack((vs_front, vs_back, vs_top, vs_bottom, vs_left, vs_right))
        m_rotate = util.y2v(vec)
        vs = np.dot(vs, m_rotate) + center

        self._surface(vs, GL_TRIANGLES, color=color, **kwds)

    def torus(self, center, r1, r2, **kwds):
        """球环

        center      - 球环中心坐标：元组、列表或numpy数组
        r1          - 球半径：浮点型
        r2          - 环半径：浮点型
        kwds        - 关键字参数
            color       - 颜色：浮点型元组、列表或numpy数组
            vec         - 环面法向量
            uarc        - u方向范围：默认0°~360°
            varc        - v方向范围：默认0°~360°
            cell        - 网格精度：默认5°
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认不透明
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        vec = kwds.pop('vec') if 'vec' in kwds else (0,1,0)
        uarc = kwds.pop('uarc') if 'uarc' in kwds else (0,360)
        varc = kwds.pop('varc') if 'varc' in kwds else (0,360)
        cell = kwds.pop('cell') if 'cell' in kwds else 5

        u_0, u_1 = np.radians(uarc[0]), np.radians(uarc[1])
        v_0, v_1 = np.radians(varc[1]), np.radians(varc[0])
        cell = np.radians(cell)
        u_slices, v_slices = round(abs(u_0-u_1)/cell), round(abs(v_0-v_1)/cell)
        gv, gu = np.mgrid[v_0:v_1:complex(0,v_slices), u_0:u_1:complex(0,u_slices)]

        xs = (r2 + r1 * np.cos(gv)) * np.cos(gu)
        zs = -(r2 + r1 * np.cos(gv)) * np.sin(gu)
        ys = r1 * np.sin(gv)

        m_rotate = util.y2v(vec)
        vs = np.dot(np.dstack((xs, ys, zs)), m_rotate) + center
        xs, ys, zs = vs[...,0], vs[...,1], vs[...,2]

        self.mesh(xs, ys, zs, color=color, **kwds)

    def isosurface(self, data, level, **kwds):
        """基于MarchingCube算法的三维等值面

        data        - 数据集：三维numpy数组
        level       - 阈值：浮点型
        kwds        - 关键字参数
            color       - 颜色：浮点型元组、列表或numpy数组
            xr          - 数据集对应的点的x轴的动态范围
            yr          - 数据集对应的点的y轴的动态范围
            zr          - 数据集对应的点的z轴的动态范围
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            opacity     - 模型不透明属性，默认不透明
            cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列
            light       - 光照模型（默认户外光照模型）
            name        - 模型或部件名
        """

        color = kwds.pop('color') if 'color' in kwds else None
        xr = kwds.pop('xr') if 'xr' in kwds else None
        yr = kwds.pop('yr') if 'yr' in kwds else None
        zr = kwds.pop('zr') if 'zr' in kwds else None

        vs, ids = util._isosurface(data, level)
        indices = ids.ravel()

        xs = vs[:,0] if xr is None else (xr[1] - xr[0]) * vs[:,0] / data.shape[0] + xr[0]
        ys = vs[:,1] if yr is None else (yr[1] - yr[0]) * vs[:,1] / data.shape[1] + yr[0]
        zs = vs[:,2] if zr is None else (zr[1] - zr[0]) * vs[:,2] / data.shape[2] + zr[0]
        vs = np.stack((xs, ys, zs), axis=1)[indices]

        self._surface(vs, GL_TRIANGLES, color=color, **kwds)

