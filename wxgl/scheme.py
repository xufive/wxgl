#!/usr/bin/env python3

import os
import uuid
import numpy as np
from OpenGL.GL import *
from . light import *
from . texture import Texture
from . import util

class Scheme:
    """应用于三维场景中的展示方案类"""

    def __init__(self, haxis='y', bg=(0.0,0.0,0.0)):
        """构造函数

        haxis       - 高度轴，默认y轴，可选z轴，不支持x轴
        bg          - 背景色，默认0.0, 0.0, 0.0)
        """

        self.reset()

        self.haxis = haxis.lower()                              # 高度轴
        self.bg = util.format_color(bg)                         # 背景色
        self.fg = 1 - self.bg                                   # 前景色

    def reset(self):
        """清除模型数据"""

        self.r_x = [1e12, -1e12]                                # 数据在x轴上的动态范围
        self.r_y = [1e12, -1e12]                                # 数据在y轴上的动态范围
        self.r_z = [1e12, -1e12]                                # 数据在z轴上的动态范围
        self.cid = -1                                           # 缺省颜色id
        self.ticks = None                                       # 网格与坐标轴刻度 
        self.cruise_func = None                                 # 相机巡航函数
        self.alive = False                                      # 是否使用了动画函数
        self.models = [dict(), dict(), dict()]                  # 主视区、标题区、调色板区模型
        self.widget = dict()                                    # 由一个或多个模型组成的部件

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

        self.cid = (self.cid+1)%10

        return util.format_color(color, self.cid, repeat=repeat)

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
        """设置相机巡航函数"""
        
        if hasattr(func, '__call__'):
            self.cruise_func = func
            self.alive = True

    def model(self, m, name=None):
        """添加模型"""

        m.verify()

        if m.inside:
            self._set_range(r_x=m.r_x, r_y=m.r_y, r_z=m.r_z)

        if m.alive:
            self.alive = True

        mid = uuid.uuid1().hex
        self.models[0].update({mid: m})
        
        if name is None:
            name = mid

        if name in self.widget:
            self.widget[name].append(mid)
        else:
            self.widget.update({name:[mid]})

    def _get_series(self, v_min, v_max, endpoint=False, extend=0):
        """返回标注序列
 
        v_min       - 数据最小值
        v_max       - 数据最大值
        endpoint    - 返回序列两端为v_min和v_max
        extend      - 值域外延系数
        """
 
        ks = (1, 2, 2.5, 5) # 分段选项
        s_min, s_max = 3, 5 # 分段数 
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

    def text(self, text, pos, **kwds):
        """2d文字
 
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
        family = kwds.get('family', None)
        weight = kwds.get('weight', 'normal')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        slide = kwds.get('slide', None)
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        name = kwds.get('name', None)

        box = np.tile(np.array(pos, dtype=np.float32), (4,1))
        texcoord = np.array([[0,0],[0,1],[1,0],[1,1]], dtype=np.float32)
        align = {'left':0, 'center':1, 'right':2}.get(align, 0)*3 + {'top':0, 'middle':1, 'bottom':2}.get(valign, 2)
 
        im_text = util.text2img(text, size, self._format_color(color), bg=None, family=family, weight=weight)
        texture = Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        tsize = (size*im_text.shape[1]/im_text.shape[0], size)
        light = Text2dLight(ambient)

        self.model(light.get_model(GL_TRIANGLE_STRIP, box, 
            texture     = texture, 
            texcoord    = texcoord, 
            align       = align, 
            tsize       = tsize,
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
            alpha       - 透明度
            texture     - 纹理图片，或2D纹理对象
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient     - 环境光，默认(1.0,1.0,1.0)
            name        - 模型或部件名
        """

        keys = ['color', 'size', 'data', 'cm', 'alpha', 'texture', 'visible', 'inside', 'slide', 'transform', 'ambient', 'name']
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.get('color', self.fg)
        size = kwds.get('size', 3.0)
        data = kwds.get('data', None)
        cm = kwds.get('cm', 'viridis')
        alpha = kwds.get('alpha', 1.0)
        texture = kwds.get('texture', None)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        slide = kwds.get('slide', None)
        transform = kwds.get('transform', None)
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        name = kwds.get('name', None)

        light = ScatterLight(ambient)
        vs = np.array(vs, dtype=np.float32)
        size = np.ones(vs.shape[0], dtype=np.float32) * size if isinstance(size, (int, float)) else np.float32(size)

        if self.haxis=='z':
            idx = np.argsort(-vs[...,1])
        elif vs.shape[1] == 3:
            idx = np.argsort(vs[...,2])
        else:
            idx = np.arange(vs.shape[0])
 
        if not texture is None:
            if isinstance(texture, str) and os.path.exists(texture):
                texture = Texture(texture)
            else:
                raise ValueError('文件不存在：%s'%texture)
            
            if isinstance(texture, Texture):
                color = None
            else:       
                raise ValueError('期望texture参数是wxgl.Texture对象')
        elif data is None:
            color = self._format_color(color, vs.shape[0])[idx]
        else:
            color = util.cmap(np.array(data), cm, alpha=alpha)[idx]
 
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
            alpha       - 透明度
            method      - 绘制方法：'isolate'-独立线段，'strip'-连续线段（默认），'loop'-闭合线段
            width       - 线宽：0.0~10.0之间，None使用默认设置
            stipple     - 线型：整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None使用默认设置
            visible     - 是否可见，默认True
            inside      - 模型顶点是否影响模型空间，默认True
            slide       - 幻灯片函数，默认None
            transform   - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient     - 环境光，默认(1.0,1.0,1.0)
            name        - 模型或部件名
        """
 
        keys = [
            'color','data','cm','alpha','method','width','stipple',
            'visible','inside','slide','transform','ambient','name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.get('color', None)
        data = kwds.get('data', None)
        cm = kwds.get('cm', 'viridis')
        alpha = kwds.get('alpha', 1.0)
        method = kwds.get('method', 'strip')
        width = kwds.get('width', None)
        stipple = kwds.get('stipple', None)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        slide = kwds.get('slide', None)
        transform = kwds.get('transform', None)
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        name = kwds.get('name', None)

        light = BaseLight(kwds.pop('ambient') if 'ambient' in kwds else (1.0,1.0,1.0))
        gltype = {'isolate':GL_LINES, 'strip':GL_LINE_STRIP, 'loop':GL_LINE_LOOP}[method.lower()]
        vs = np.array(vs, dtype=np.float32)
        color = self._format_color(color, vs.shape[0]) if data is None else util.cmap(np.array(data), cm, alpha=alpha)

        self.model(light.get_model(gltype, vs, 
            color       = color, 
            lw          = width, 
            ls          = stipple, 
            visible     = visible,
            inside      = inside,
            slide       = slide,
            transform   = transform
        ), name)

    def surface(self, vs, **kwds):
        """三角曲面
 
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            data        - 数据集：元组、列表或numpy数组，shape=(n,)
            cm          - 调色板
            alpha       - 透明度
            texture     - 纹理图片，或2D/2DArray/3D纹理对象
            texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
            method      - 绘制方法：'isolate'-独立三角面（默认），'strip'-带状三角面，'fan'-扇面
            indices     - 顶点索引集，默认None，表示不使用索引
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
 
        keys = [
            'color', 'data', 'cm', 'alpha', 'texture', 'texcoord', 'method', 'indices', 
            'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.get('color', None)
        data = kwds.get('data', None)
        cm = kwds.get('cm', 'viridis')
        alpha = kwds.get('alpha', 1.0)
        texture = kwds.get('texture', None)
        texcoord = kwds.get('texcoord', None)
        method = kwds.get('method', 'isolate')
        indices = kwds.get('indices', None)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull', None)
        fill = kwds.get('fill', None)
        slide = kwds.get('slide', None)
        transform = kwds.get('transform', None)
        light = kwds.get('light', SkyLight(direction=(-0.1,0.2,-1) if self.haxis=='z' else (-0.1,-1,-0.2)))
        name = kwds.get('name', None)

        gltype = {'isolate':GL_TRIANGLES, 'strip':GL_TRIANGLE_STRIP, 'fan':GL_TRIANGLE_FAN}[method.lower()]
        vs = np.array(vs, dtype=np.float32)
        normal = util.get_normal(gltype, vs, indices)

        if gltype == GL_TRIANGLE_STRIP and (np.absolute(vs[0]-vs[-2])<1e-10).all() and (np.absolute(vs[1]-vs[-1])<1e-10).all():
            normal[0] += normal[-2]
            normal[1] += normal[-1]
            normal[-2] = normal[0]
            normal[-1] = normal[1]
        elif gltype == GL_TRIANGLE_FAN and (np.absolute(vs[1]-vs[-1])<1e-10).all():
            normal[1] += normal[-1]
            normal[-1] = normal[1]

        if not texture is None:
            if isinstance(texture, str) and os.path.exists(texture):
                texture = Texture(texture)
            else:
                raise ValueError('文件不存在：%s'%texture)
            
            if isinstance(texture, Texture):
                color = None
                texcoord = np.array(texcoord, dtype=np.float32)
            else:       
                raise ValueError('期望texture参数是wxgl.Texture对象')
        elif data is None:
            color = self._format_color(color, vs.shape[0])
        else:
            color = util.cmap(np.array(data), cm, alpha=alpha)
 
        self.model(light.get_model(gltype, vs, 
            normal      = normal,
            color       = color,
            texture     = texture,
            texcoord    = texcoord,
            indices     = indices, 
            visible     = visible,
            inside      = inside,
            opacity     = opacity,
            cull        = cull,
            fill        = fill,
            slide       = slide,
            transform   = transform
        ), name)

    def quad(self, vs, **kwds):
        """四角曲面
        
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            data        - 数据集：元组、列表或numpy数组，shape=(n,)
            cm          - 调色板
            alpha       - 透明度
            texture     - 纹理图片，或2D/2DArray/3D纹理对象
            texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
            method      - 绘制方法：'isolate'-独立四角面（默认），'strip'- 带状四角面
            indices     - 顶点索引集，默认None，表示不使用索引
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
 
        keys = [
            'color', 'data', 'cm', 'alpha', 'texture', 'texcoord', 'method', 'indices', 
            'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.get('color', None)
        data = kwds.get('data', None)
        cm = kwds.get('cm', 'viridis')
        alpha = kwds.get('alpha', 1.0)
        texture = kwds.get('texture', None)
        texcoord = kwds.get('texcoord', None)
        method = kwds.get('method', 'isolate')
        indices = kwds.get('indices', None)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull', None)
        fill = kwds.get('fill', None)
        slide = kwds.get('slide', None)
        transform = kwds.get('transform', None)
        light = kwds.get('light', SkyLight(direction=(-0.1,0.2,-1) if self.haxis=='z' else (-0.1,-1,-0.2)))
        name = kwds.get('name', None)

        gltype = {'isolate':GL_QUADS, 'strip':GL_QUAD_STRIP}[method.lower()]
        vs = np.array(vs, dtype=np.float32)
        normal = util.get_normal(gltype, vs, indices)

        if gltype == GL_QUAD_STRIP and (np.absolute(vs[0]-vs[-2])<1e-10).all() and (np.absolute(vs[1]-vs[-1])<1e-10).all():
            normal[0] += normal[-2]
            normal[1] += normal[-1]
            normal[-2] = normal[0]
            normal[-1] = normal[1]

        if not texture is None:
            if isinstance(texture, str) and os.path.exists(texture):
                texture = Texture(texture)
            else:
                raise ValueError('文件不存在：%s'%texture)
            
            if isinstance(texture, Texture):
                color = None
                texcoord = np.array(texcoord, dtype=np.float32)
            else:       
                raise ValueError('期望texture参数是wxgl.Texture对象')
        elif data is None:
            color = self._format_color(color, vs.shape[0])
        else:
            color = util.cmap(np.array(data), cm, alpha=alpha)
 
        self.model(light.get_model(gltype, vs, 
            normal      = normal,
            color       = color,
            texture     = texture,
            texcoord    = texcoord,
            indices     = indices, 
            visible     = visible,
            inside      = inside,
            opacity     = opacity,
            cull        = cull,
            fill        = fill,
            slide       = slide,
            transform   = transform
        ), name)

    def mesh(self, xs, ys, zs, **kwds):
        """网格面
        
        xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)，m为网格行数，n为网格列数
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            data        - 数据集：元组、列表或numpy数组，shape=(m,n)
            cm          - 调色板
            alpha       - 透明度
            texture     - 纹理图片，或2D纹理对象
            texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2)
            ccw         - 逆时针三角面，默认True
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
 
        keys = [
            'color', 'data', 'cm', 'alpha', 'texture', 'texcoord', 'ccw', 
            'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.get('color', None)
        data = kwds.get('data', None)
        cm = kwds.get('cm', 'viridis')
        alpha = kwds.get('alpha', 1.0)
        texture = kwds.get('texture', None)
        texcoord = kwds.get('texcoord', None)
        ccw = kwds.get('ccw', True)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull', None)
        fill = kwds.get('fill', None)
        slide = kwds.get('slide', None)
        transform = kwds.get('transform', None)
        light = kwds.get('light', SkyLight(direction=(-0.1,0.2,-1) if self.haxis=='z' else (-0.1,-1,-0.2)))
        name = kwds.get('name', None)

        gltype = GL_TRIANGLES
        vs = np.dstack((xs, ys, zs))
        rows, cols = vs.shape[:2]

        idx = np.arange(rows*cols).reshape(rows, cols)
        idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[:-1, 1:], idx[1:,1:]
        if ccw:
            indices = np.int32(np.dstack((idx_a, idx_b, idx_c, idx_c, idx_b, idx_d)).ravel())
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
            if isinstance(texture, str) and os.path.exists(texture):
                texture = Texture(texture)
            else:
                raise ValueError('文件不存在：%s'%texture)

            if isinstance(texture, Texture):
                color = None
                if texcoord is None:
                    u = np.linspace(0, 1, cols)
                    v = np.linspace(0, 1, rows)
                    texcoord = np.float32(np.dstack(np.meshgrid(u, v)).reshape(-1, 2))
            else:       
                raise ValueError('期望texture参数是wxgl.Texture对象')
        elif data is None:
            color = self._format_color(color, rows*cols)
        else:
            color = util.cmap(np.array(data), cm, alpha=alpha).reshape(-1, 4)
 
        self.model(light.get_model(gltype, vs, 
            normal      = normal,
            color       = color,
            texture     = texture,
            texcoord    = texcoord,
            indices     = indices, 
            visible     = visible,
            inside      = inside,
            opacity     = opacity,
            cull        = cull,
            fill        = fill,
            slide       = slide,
            transform   = transform
        ), name)

    def text3d(self, text, box, **kwds):
        """3d文字
 
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
 
        keys = [
            'color', 'bg', 'align', 'family', 'weight', 'size', 
            'visible', 'inside', 'cull', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
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

        self.quad(box, texture=texture, texcoord=texcoord, **kwds) 

    def uvsphere(self, center, r, **kwds):
        """使用经纬度网格生成球
 
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            texture     - 纹理图片，或2D纹理对象
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

        keys = [
            'color', 'texture', 'uarc', 'varc', 'cell', 
            'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.pop('color') if 'color' in kwds else None
        texture = kwds.pop('texture') if 'texture' in kwds else None
        uarc = kwds.pop('uarc') if 'uarc' in kwds else (0,360)
        varc = kwds.pop('varc') if 'varc' in kwds else (-90,90)
        cell = kwds.pop('cell') if 'cell' in kwds else 5
 
        u0, u1 = np.radians(uarc[0]), np.radians(uarc[1])
        v0, v1 = np.radians(varc[1]), np.radians(varc[0])
        cell = np.radians(cell)
        ulen, vlen = int(abs(u0-u1)/cell)+1, int(abs(v0-v1)/cell)+1
        gv, gu = np.mgrid[v0:v1:complex(0,vlen), u0:u1:complex(0,ulen)]
 
        if self.haxis == 'z':
            zs = r * np.sin(gv)
            xs = r * np.cos(gv)*np.cos(gu)
            ys = r * np.cos(gv)*np.sin(gu)
        else:
            ys = r * np.sin(gv)
            xs = r * np.cos(gv)*np.cos(gu)
            zs = -r * np.cos(gv)*np.sin(gu)

        self.mesh(xs, ys, zs, color=color, texture=texture, **kwds)

    def isosphere(self, center, r, **kwds):
        """通过对正二十面体的迭代细分生成球
        
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            iterate     - 迭代次数：整型
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

        keys = ['color', 'iterate', 'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name']
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.pop('color') if 'color' in kwds else None
        iterate = kwds.pop('iterate') if 'iterate' in kwds else 5
 
        b = pow((5 + pow(5, 0.5)) / 10, 0.5)
        a = b * (pow(5, 0.5) - 1) / 2
        vs = np.array([
            [-a,0,b], [a,0,b], [-a,0,-b], [a,0,-b],
            [0,b,a], [0,b,-a], [0,-b,a], [0,-b,-a],
            [b,a,0], [-b,a,0], [b,-a,0], [-b,-a,0]
        ])
        idx = np.array([
            1,4,0,  4,9,0,  4,5,9,  8,5,4,  1,8,4,
		    1,10,8, 10,3,8, 8,3,5,  3,2,5,  3,7,2,
		    3,10,7, 10,6,7, 6,11,7, 6,0,11, 6,1,0,
		    10,1,6, 11,0,9, 2,11,9, 5,2,9,  11,2,7
        ])
        vs = vs[idx]
 
        for i in range(iterate):
            p0 = (vs[::3] + vs[1::3]) / 2
            p0 = r * p0 / np.linalg.norm(p0, axis=1).reshape(-1, 1)
            p1 = (vs[1::3] + vs[2::3]) / 2
            p1 = r * p1 / np.linalg.norm(p1, axis=1).reshape(-1, 1)
            p2 = (vs[::3] + vs[2::3]) / 2
            p2 = r * p2 / np.linalg.norm(p2, axis=1).reshape(-1, 1)
            vs = np.stack((vs[::3],p0,p2,vs[1::3],p1,p0,vs[2::3],p2,p1,p0,p1,p2),axis=1).reshape(-1,3)
        vs += np.array(center)
 
        self.surface(vs, color=color, method='isolate', **kwds)

    def cube(self, center, side, **kwds):
        """六面体
        
        center      - 中心坐标，元组、列表或numpy数组
        side        - 棱长：数值或长度为3的元组、列表、numpy数组
        kwds        - 关键字参数
            vec         - 六面体上表面法向量
            color       - 颜色：浮点型元组、列表或numpy数组
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
 
        keys = ['vec', 'color', 'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name']
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        vec = kwds.pop('vec') if 'vec' in kwds else (0,1,0)
        color = kwds.pop('color') if 'color' in kwds else None
 
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
 
        self.surface(vs, color=color, method='isolate', **kwds)

    def circle(self, center, r, **kwds):
        """圆
        
        center      - 锥底圆心：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        kwds        - 关键字参数
            vec         - 圆面法向量
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
 
        keys = [
            'vec', 'color', 'arc', 'cell', 
            'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        vec = kwds.pop('vec') if 'vec' in kwds else (0,1,0)
        color = kwds.pop('color') if 'color' in kwds else None
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
 
        self.surface(vs, color=color, method='fan', **kwds)

    def cone(self, spire, center, r, **kwds):
        """圆锥
 
        spire       - 锥尖：元组、列表或numpy数组
        center      - 锥底圆心：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        kwds        - 关键字参数
            color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
            bottom      - 绘制锥底：布尔型
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

        keys = [
            'color', 'bottom', 'arc', 'cell', 
            'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.pop('color') if 'color' in kwds else None
        bottom = kwds.pop('bottom') if 'bottom' in kwds else False
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
 
        self.surface(vs_c, color=color, method='fan', **kwds)
        if bottom:
            vs_b = np.vstack((center, vs[::-1]))
            self.surface(vs_b, color=color, method='fan', **kwds)

    def cylinder(self, c1, c2, r, **kwds):
        """圆柱
        
        c1          - 圆柱端面圆心：元组、列表或numpy数组
        c2          - 圆柱端面圆心：元组、列表或numpy数组
        r           - 圆柱半径：浮点型
        kwds        - 关键字参数
            color       - 颜色：浮点型元组、列表或numpy数组
            texture     - 纹理：wxgl.Texture对象
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
        
        keys = [
            'color', 'texture', 'arc', 'cell', 
            'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.pop('color') if 'color' in kwds else None
        texture = kwds.pop('texture') if 'texture' in kwds else None
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
 
        self.mesh(xs, ys, zs, color=color, texture=texture, **kwds)

    def torus(self, center, r1, r2, **kwds):
        """球环
 
        center      - 球环中心坐标：元组、列表或numpy数组
        r1          - 球半径：浮点型
        r2          - 环半径：浮点型
        kwds        - 关键字参数
            vec         - 环面法向量
            color       - 颜色：浮点型元组、列表或numpy数组
            texture     - 纹理：wxgl.Texture对象
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

        keys = [
            'vec', 'color', 'texture', 'uarc', 'varc', 'cell', 
            'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        vec = kwds.pop('vec') if 'vec' in kwds else (0,1,0)
        color = kwds.pop('color') if 'color' in kwds else None
        texture = kwds.pop('texture') if 'texture' in kwds else None
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
 
        self.mesh(xs, ys, zs, color=color, texture=texture, **kwds)

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

        keys = [
            'color', 'xr', 'yr', 'zr',  
            'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light', 'name'
        ]
        for key in kwds:
            if key not in keys:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.pop('color') if 'color' in kwds else None
        xr = kwds.pop('xr') if 'xr' in kwds else None
        yr = kwds.pop('yr') if 'yr' in kwds else None
        zr = kwds.pop('zr') if 'zr' in kwds else None
 
        vs, ids = util._isosurface(data, level)
        indices = ids.ravel()
 
        xs = vs[:,0] if xr is None else (xr[1] - xr[0]) * vs[:,0] / data.shape[0] + xr[0]
        ys = vs[:,1] if yr is None else (yr[1] - yr[0]) * vs[:,1] / data.shape[1] + yr[0]
        zs = vs[:,2] if zr is None else (zr[1] - zr[0]) * vs[:,2] / data.shape[2] + zr[0]
        vs = np.stack((xs, ys, zs), axis=1)
 
        self.surface(vs, color=color, method='isolate', indices=indices, **kwds)

    def axes(self, length=1, color=((1,0,0),(0,1,0),(0,0,1)), name=None):
        """坐标轴

        length      - 坐标半轴长度
        color       - 坐标轴颜色
        name        - 部件名
        """

        if name is None:
            name = uuid.uuid1().hex

        vs = [[-length,0,0], [0.85*length,0,0], [0,-length,0], [0,0.85*length,0], [0,0,-length], [0,0,0.85*length]]
        colors = np.repeat(np.array(color), 2, axis=0)

        self.line(vs, color=colors, method='isolate')
        self.cone((length,0,0), (0.85*length,0,0), 0.02*length, color=color[0], bottom=True, name=name)
        self.cone((0,length,0), (0,0.85*length,0), 0.02*length, color=color[1], bottom=True, name=name)
        self.cone((0,0,length), (0,0,0.85*length), 0.02*length, color=color[2], bottom=True, name=name)

    def _grid(self):
        """网格和刻度 """

        if self.r_x[0] >= self.r_x[-1] or self.r_y[0] >= self.r_y[-1] or self.r_z[0] >= self.r_z[-1]:
            return # '模型空间不存在，返回

        size = self.ticks['size']
        xf = self.ticks['xf']
        yf = self.ticks['yf']
        zf = self.ticks['zf']
        name = self.ticks['name']

        xx = self._get_series(*self.r_x, extend=0.03)
        yy = self._get_series(*self.r_y, extend=0.03)
        zz = self._get_series(*self.r_z, extend=0.03)

        # -----------------------------------------------------------------------------------------
        def mesh2quad(xs, ys, zs):
            """mesh转quad"""
 
            vs = np.dstack((xs, ys, zs))
            rows, cols = vs.shape[:2]
 
            idx = np.arange(rows*cols).reshape(rows, cols)
            idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[1:,1:], idx[:-1, 1:]
            idx = np.int32(np.dstack((idx_a, idx_b, idx_c, idx_d)).ravel())
 
            return vs.reshape(-1,3)[idx]

        # -----------------------------------------------------------------------------------------
        def text3d_ticks(text, box, color, loc, cull, align, bg=None, padding=0):
            """标注"""

            vshader = """
                #version 330 core
 
                in vec4 a_Position;
                in vec3 a_Texcoord;
                in float a_TickLoc;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                out vec3 v_Texcoord;
                out float v_Loc;
 
                void main() { 
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                    v_Texcoord = a_Texcoord;
                    v_Loc = a_TickLoc;
                }
            """

            fshader = """
                #version 330 core
 
                in vec3 v_Texcoord;
                in float v_Loc;
                uniform vec3 u_AmbientColor;
                uniform sampler2DArray u_Texture;
                uniform vec2 u_Ae;
 
                void main() { 
                    if (u_Ae[1] > 90 || u_Ae[1] < -90) discard;

                    if (v_Loc == 0.0 && (u_Ae[0] < 0 || u_Ae[0] >= 90)) discard;
                    if (v_Loc == 1.0 && (u_Ae[0] < -90 || u_Ae[0] >= 0)) discard;
                    if (v_Loc == 2.0 && u_Ae[0] >= -90) discard;
                    if (v_Loc == 3.0 && u_Ae[0] < 90) discard;

                    if (u_Ae[1] < 0) {
                        if (v_Loc == 10.0 || v_Loc == 11.0) discard;
                        if (v_Loc == 13.0 && u_Ae[0] >= -90 && u_Ae[0] < 90) discard;
                        if (v_Loc == 12.0 && (u_Ae[0] >= 90 || u_Ae[0] < -90)) discard;
                    }

                    if (u_Ae[1] >= 0) {
                        if (v_Loc == 12.0 || v_Loc == 13.0) discard;
                        if (v_Loc == 11.0 && u_Ae[0] >= -90 && u_Ae[0] < 90) discard;
                        if (v_Loc == 10.0 && (u_Ae[0] >= 90 || u_Ae[0] < -90)) discard;
                    }

                    if (u_Ae[1] < 0) {
                        if (v_Loc == 20.0 || v_Loc == 21.0) discard;
                        if (v_Loc == 23.0 && u_Ae[0] >= 0) discard;
                        if (v_Loc == 22.0 && u_Ae[0] < 0) discard;
                    }
 
                    if (u_Ae[1] >= 0) {
                        if (v_Loc == 22.0 || v_Loc == 23.0) discard;
                        if (v_Loc == 21.0 && u_Ae[0] >= 0) discard;
                        if (v_Loc == 20.0 && u_Ae[0] < 0) discard;
                    }

                    vec4 color = texture(u_Texture, v_Texcoord);
                    vec3 rgb = color.rgb * u_AmbientColor;
                    gl_FragColor = vec4(rgb, color.a);
                } 
            """

            loc = np.repeat(np.array(loc, dtype=np.float32), 4)
            color = np.array(color, dtype=np.float32)

            if color.ndim == 1:
                color = np.tile(color, (len(text), 1))
            
            if bg is None:
                bg = [None for i in range(len(text))]
            else:
                bg = np.array(bg, dtype=np.float32)
                if bg.ndim == 1:
                    bg = np.tile(bg, (len(text), 1))

            im_arr, texcoord = list(), list()
            rows_max, cols_max = 0, 0
            for i in range(len(text)):
                im = util.text2img(text[i], 64, color[i], bg=bg[i], padding=padding)
                rows_max = max(im.shape[0], rows_max)
                cols_max = max(im.shape[1], cols_max)
                im_arr.append(im)
                texcoord.append(np.array([[0,0,i],[0,1,i],[1,1,i],[1,0,i]], dtype=np.float32))
            
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
 
                if align[i] == 'left':
                    offset = (box[i][2]-box[i][1])*k_text/k_box
                    box[i][2] = box[i][1] + offset
                    box[i][3] = box[i][0] + offset
                elif align[i] == 'right':
                    offset = (box[i][0] - box[i][3])*k_text/k_box
                    box[i][0] = box[i][3] + offset
                    box[i][1] = box[i][2] + offset
                elif align[i] == 'center':
                    offset = (box[i][3] - box[i][0])*(1-k_text/k_box)/2
                    box[i][0] += offset
                    box[i][1] += offset
                    box[i][2] -= offset
                    box[i][3] -= offset
 
            texture = Texture(np.stack(nim_arr), ttype=GL_TEXTURE_2D_ARRAY, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
            texcoord = np.vstack(texcoord)
 
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

            return m

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
        self.quad(vs, color=[*self.fg, 0.3], fill=False, cull='front', method='isolate', opacity=False, light=light, name=name)
        self.quad(vs, color=[*bg, 1.0], cull='front', method='isolate', opacity=False, light=light, name=name)
        self.quad(vs, color=[*self.fg, 0.3], fill=False, cull='front', method='isolate', opacity=False, light=light, name=name)

        # 以下绘制标注文本
        # ----------------------------------------------------------------------------------------------------
        dx = xx[2] - xx[1]
        dy = yy[2] - yy[1]
        dz = zz[2] - zz[1]
        h = min(dx, dy, dz) * size/200 # 标注文字高度
        hh, d1 = 0.5*h, 1.0*h
        text, box, loc, align = list(), list(), list(), list()

        for x in xx[1:-1]:
            x_str = xf(x)
            text.extend([x_str, x_str, x_str, x_str])
            align.extend(['center', 'center', 'center', 'center'])

            if self.haxis == 'z':
                loc.extend([10, 11, 12, 13])
                box.append([[x-dx,yy[-1],zz[-1]+h], [x-dx,yy[-1],zz[-1]], [x+dx,yy[-1],zz[-1]], [x+dx,yy[-1],zz[-1]+h]])
                box.append([[x+dx,yy[0],zz[-1]+h], [x+dx,yy[0],zz[-1]], [x-dx,yy[0],zz[-1]], [x-dx,yy[0],zz[-1]+h]])
                box.append([[x-dx,yy[-1],zz[0]], [x-dx,yy[-1],zz[0]-h], [x+dx,yy[-1],zz[0]-h], [x+dx,yy[-1],zz[0]]])
                box.append([[x+dx,yy[0],zz[0]], [x+dx,yy[0],zz[0]-h], [x-dx,yy[0],zz[0]-h], [x-dx,yy[0],zz[0]]])
            else:
                loc.extend([10, 11, 12, 13])
                box.append([[x-dx,yy[-1]+h,zz[0]], [x-dx,yy[-1],zz[0]], [x+dx,yy[-1],zz[0]], [x+dx,yy[-1]+h,zz[0]]])
                box.append([[x+dx,yy[-1]+h,zz[-1]], [x+dx,yy[-1],zz[-1]], [x-dx,yy[-1],zz[-1]], [x-dx,yy[-1]+h,zz[-1]]])
                box.append([[x-dx,yy[0],zz[0]], [x-dx,yy[0]-h,zz[0]], [x+dx,yy[0]-h,zz[0]], [x+dx,yy[0],zz[0]]])
                box.append([[x+dx,yy[0],zz[-1]], [x+dx,yy[0]-h,zz[-1]], [x-dx,yy[0]-h,zz[-1]], [x-dx,yy[0],zz[-1]]])

        for y in yy[1:-1]:
            y_str = yf(y)
            text.extend([y_str, y_str, y_str, y_str])

            if self.haxis == 'z':
                loc.extend([20, 21, 22, 23])
                align.extend(['center', 'center', 'center', 'center'])
                box.append([[xx[0],y-dy,zz[-1]+h], [xx[0],y-dy,zz[-1]], [xx[0],y+dy,zz[-1]], [xx[0],y+dy,zz[-1]+h]])
                box.append([[xx[-1],y+dy,zz[-1]+h], [xx[-1],y+dy,zz[-1]], [xx[-1],y-dy,zz[-1]], [xx[-1],y-dy,zz[-1]+h]])
                box.append([[xx[0],y-dy,zz[0]], [xx[0],y-dy,zz[0]-h], [xx[0],y+dy,zz[0]-h], [xx[0],y+dy,zz[0]]])
                box.append([[xx[-1],y+dy,zz[0]], [xx[-1],y+dy,zz[0]-h], [xx[-1],y-dy,zz[0]-h], [xx[-1],y-dy,zz[0]]])
            else:
                loc.extend([0, 1, 2, 3])
                align.extend(['right', 'right', 'right', 'right'])
                box.append([[xx[0],y+hh,zz[-1]+dz], [xx[0],y-hh,zz[-1]+dz], [xx[0],y-hh,zz[-1]], [xx[0],y+hh,zz[-1]]])
                box.append([[xx[0]-dx,y+hh,zz[0]], [xx[0]-dx,y-hh,zz[0]], [xx[0],y-hh,zz[0]], [xx[0],y+hh,zz[0]]])
                box.append([[xx[-1],y+hh,zz[0]-dz], [xx[-1],y-hh,zz[0]-dz], [xx[-1],y-hh,zz[0]], [xx[-1],y+hh,zz[0]]])
                box.append([[xx[-1]+dx,y+hh,zz[-1]], [xx[-1]+dx,y-hh,zz[-1]], [xx[-1],y-hh,zz[-1]], [xx[-1],y+hh,zz[-1]]])

        for z in zz[1:-1]:
            z_str = zf(z)
            text.extend([z_str, z_str, z_str, z_str])

            if self.haxis == 'z':
                loc.extend([0, 1, 2, 3])
                align.extend(['right', 'right', 'right', 'right'])
                box.append([[xx[0],yy[0]-dy,z+hh], [xx[0],yy[0]-dy,z-hh], [xx[0],yy[0],z-hh], [xx[0],yy[0],z+hh]])
                box.append([[xx[0]-dx,yy[-1],z+hh], [xx[0]-dx,yy[-1],z-hh], [xx[0],yy[-1],z-hh], [xx[0],yy[-1],z+hh]])
                box.append([[xx[-1],yy[-1]+dy,z+hh], [xx[-1],yy[-1]+dy,z-hh], [xx[-1],yy[-1],z-hh], [xx[-1],yy[-1],z+hh]])
                box.append([[xx[-1]+dx,yy[0],z+hh], [xx[-1]+dx,yy[0],z-hh], [xx[-1],yy[0],z-hh], [xx[-1],yy[0],z+hh]])
            else:
                loc.extend([20, 21, 22, 23])
                align.extend(['center', 'center', 'center', 'center'])
                box.append([[xx[0],yy[-1]+h,z+dz], [xx[0],yy[-1],z+dz], [xx[0],yy[-1],z-dz], [xx[0],yy[-1]+h,z-dz]])
                box.append([[xx[-1],yy[-1]+h,z-dz], [xx[-1],yy[-1],z-dz], [xx[-1],yy[-1],z+dz], [xx[-1],yy[-1]+h,z+dz]])
                box.append([[xx[0],yy[0],z+dz], [xx[0],yy[0]-h,z+dz], [xx[0],yy[0]-h,z-dz], [xx[0],yy[0],z-dz]])
                box.append([[xx[-1],yy[0],z-dz], [xx[-1],yy[0]-h,z-dz], [xx[-1],yy[0]-h,z+dz], [xx[-1],yy[0],z+dz]])

        text.extend(['X', 'X', 'X', 'X'])
        align.extend(['center', 'center', 'center', 'center'])
        x = (xx[-1]+xx[-2])/2
        if self.haxis == 'z':
            loc.extend([10, 11, 12, 13])
            box.append([[x,yy[-1],zz[-1]+d1], [x,yy[-1],zz[-1]], [x+d1,yy[-1],zz[-1]], [x+d1,yy[-1],zz[-1]+d1]])
            box.append([[x+d1,yy[0],zz[-1]+d1], [x+d1,yy[0],zz[-1]], [x,yy[0],zz[-1]], [x,yy[0],zz[-1]+d1]])
            box.append([[x,yy[-1],zz[0]], [x,yy[-1],zz[0]-d1], [x+d1,yy[-1],zz[0]-d1], [x+d1,yy[-1],zz[0]]])
            box.append([[x+d1,yy[0],zz[0]], [x+d1,yy[0],zz[0]-d1], [x,yy[0],zz[0]-d1], [x,yy[0],zz[0]]])
        else:
            loc.extend([10, 11, 12, 13])
            box.append([[x,yy[-1]+d1,zz[0]], [x,yy[-1],zz[0]], [x+d1,yy[-1],zz[0]], [x+d1,yy[-1]+d1,zz[0]]])
            box.append([[x+d1,yy[-1]+d1,zz[-1]], [x+d1,yy[-1],zz[-1]], [x,yy[-1],zz[-1]], [x,yy[-1]+d1,zz[-1]]])
            box.append([[x,yy[0],zz[0]], [x,yy[0]-d1,zz[0]], [x+d1,yy[0]-d1,zz[0]], [x+d1,yy[0],zz[0]]])
            box.append([[x+d1,yy[0],zz[-1]], [x+d1,yy[0]-d1,zz[-1]], [x,yy[0]-d1,zz[-1]], [x,yy[0],zz[-1]]])

        text.extend(['Y', 'Y', 'Y', 'Y'])
        align.extend(['center', 'center', 'center', 'center'])
        if self.haxis == 'z':
            y = (yy[-1]+yy[-2])/2
            loc.extend([20, 21, 22, 23])
            box.append([[xx[0],y,zz[-1]+d1], [xx[0],y,zz[-1]], [xx[0],y+d1,zz[-1]], [xx[0],y+d1,zz[-1]+d1]])
            box.append([[xx[-1],y+d1,zz[-1]+d1], [xx[-1],y+d1,zz[-1]], [xx[-1],y,zz[-1]], [xx[-1],y,zz[-1]+d1]])
            box.append([[xx[0],y,zz[0]], [xx[0],y,zz[0]-d1], [xx[0],y+d1,zz[0]-d1], [xx[0],y+d1,zz[0]]])
            box.append([[xx[-1],y+d1,zz[0]], [xx[-1],y+d1,zz[0]-d1], [xx[-1],y,zz[0]-d1], [xx[-1],y,zz[0]]])
        else:
            y = (yy[-1]+yy[-2])/2
            loc.extend([0, 1, 2, 3])
            box.append([[xx[0],y+d1,zz[-1]+d1], [xx[0],y,zz[-1]+d1], [xx[0],y,zz[-1]], [xx[0],y+d1,zz[-1]]])
            box.append([[xx[0]-d1,y+d1,zz[0]], [xx[0]-d1,y,zz[0]], [xx[0],y,zz[0]], [xx[0],y+d1,zz[0]]])
            box.append([[xx[-1],y+d1,zz[0]-d1], [xx[-1],y,zz[0]-d1], [xx[-1],y,zz[0]], [xx[-1],y+d1,zz[0]]])
            box.append([[xx[-1]+d1,y+d1,zz[-1]], [xx[-1]+d1,y,zz[-1]], [xx[-1],y,zz[-1]], [xx[-1],y+d1,zz[-1]]])

        text.extend(['Z', 'Z', 'Z', 'Z'])
        align.extend(['center', 'center', 'center', 'center'])
        if self.haxis == 'z':
            z = (zz[-1]+zz[-2])/2
            loc.extend([0, 1, 2, 3])
            box.append([[xx[0],yy[0]-d1,z+d1], [xx[0],yy[0]-d1,z], [xx[0],yy[0],z], [xx[0],yy[0],z+d1]])
            box.append([[xx[0]-d1,yy[-1],z+d1], [xx[0]-d1,yy[-1],z], [xx[0],yy[-1],z], [xx[0],yy[-1],z+d1]])
            box.append([[xx[-1],yy[-1]+d1,z+d1], [xx[-1],yy[-1]+d1,z], [xx[-1],yy[-1],z], [xx[-1],yy[-1],z+d1]])
            box.append([[xx[-1]+d1,yy[0],z+d1], [xx[-1]+d1,yy[0],z], [xx[-1],yy[0],z], [xx[-1],yy[0],z+d1]])
        else:
            z = (zz[-1]+zz[-2])/2
            loc.extend([20, 21, 22, 23])
            box.append([[xx[0],yy[-1]+d1,z+d1], [xx[0],yy[-1],z+d1], [xx[0],yy[-1],z], [xx[0],yy[-1]+d1,z]])
            box.append([[xx[-1],yy[-1]+d1,z], [xx[-1],yy[-1],z], [xx[-1],yy[-1],z+d1], [xx[-1],yy[-1]+d1,z+d1]])
            box.append([[xx[0],yy[0],z+d1], [xx[0],yy[0]-d1,z+d1], [xx[0],yy[0]-d1,z], [xx[0],yy[0],z]])
            box.append([[xx[-1],yy[0],z], [xx[-1],yy[0]-d1,z], [xx[-1],yy[0]-d1,z+d1], [xx[-1],yy[0],z+d1]])

        color = [self.fg for i in range(len(box)-12)] + [self.bg for i in range(12)]
        bg = [self.bg for i in range(len(box)-12)] + [self.fg for i in range(12)]
        m = text3d_ticks(text, box, color, loc, 'back', align, bg=bg, padding=20)
        self.model(m, name=name)

    def grid(self, **kwds):
        """网格和刻度
        kwds        - 关键字参数
            size            - 刻度文本字号，默认32
            xf              - x轴标注格式化函数
            yf              - y轴标注格式化函数
            zf              - z轴标注格式化函数
            name            - 部件名
        """

        for key in kwds:
            if key not in ['size', 'xf', 'yf', 'zf', 'name']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        self.ticks = {
            'size':     kwds.get('size', 32),
            'xf':       kwds.get('xf', str),
            'yf':       kwds.get('yf', str),
            'zf':       kwds.get('zf', str),
            'name':     kwds.get('name', uuid.uuid1().hex)
        }

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

        light = BaseLight(mvp=False)
        m_text = light.get_model(GL_QUADS, box, texture=texture, texcoord=texcoord, opacity=False, inside=False)
        m_line = light.get_model(GL_LINE_STRIP, vs, color=color, lw=1)
        m_text.verify()
        m_line.verify()
        self.models[1].update({'caption_text': m_text})
        self.models[1].update({'caption_line': m_line})

    def colorbar(self, cm, data, ff=str, endpoint=True):
        """设置调色板

        cm          - 调色板名称
        data        - 值域范围或刻度序列：长度大于1的元组或列表
        kwds        - 关键字参数
        ff          - 刻度标注格式化函数，默认str
        endpoint    - 刻度是否包含值域范围的两个端点值
        """
 
        light = BaseLight(mvp=False)
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

        vs_line = list()
        ys = list()
        texcoord = np.array([[0,0],[0,1],[1,1],[1,0]], dtype=np.float32)
        for t in data:
            y = (top-bottom)*(t-dmin)/(dmax-dmin) + bottom
            vs_line.extend([[right,y,0], [right+w,y,0]])
            ys.append(y)

        vs_line = np.array(vs_line, dtype=np.float32)
        color_line = self._format_color(self.fg, vs_line.shape[0])

        m_line = light.get_model(GL_LINES, vs_line, color=color_line, method='isolate', inside=False)
        m_line.verify()
        self.models[2].update({'cb_line': m_line})

        # 绘制刻度文本
        # --------------------------------------------------------------------
        im_arr, texcoord, box = list(), list(), list()
        rows_max, cols_max = 0, 0
        for i in range(len(data)):
            im = util.text2img(ff(data[i]), 64, self.fg)
            rows_max = max(im.shape[0], rows_max)
            cols_max = max(im.shape[1], cols_max)
            im_arr.append(im)
            texcoord.append(np.array([[0,0,i],[0,1,i],[1,1,i],[1,0,i]], dtype=np.float32))
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
            box[i][2] = box[i][1] + offset
            box[i][3] = box[i][0] + offset
 
        texture = Texture(np.stack(nim_arr), ttype=GL_TEXTURE_2D_ARRAY, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        texcoord = np.vstack(texcoord)
        
        m_label = light.get_model(GL_QUADS, box, texture=texture, texcoord=texcoord, opacity=False, inside=False)
        m_label.verify()
        self.models[2].update({'cb_label': m_label})

