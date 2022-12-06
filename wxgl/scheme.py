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

        self.haxis = haxis.lower()                              # 高度轴
        self.bg = np.array(bg)                                  # 背景色
        self.fg = 1 - self.bg                                   # 前景色

        self.reset()

    def reset(self):
        """清除模型数据"""

        self.r_x = [1e12, -1e12]                                # 数据在x轴上的动态范围
        self.r_y = [1e12, -1e12]                                # 数据在y轴上的动态范围
        self.r_z = [1e12, -1e12]                                # 数据在z轴上的动态范围
        self.ticks = None                                       # 网格与坐标轴刻度 
        self.cruise = None                                      # 相机巡航函数
        self.animate = False                                    # 是否使用了动画函数
        self.models = [dict(), dict(), dict()]                  # 主视区、标题区、调色板区模型

    def set_cruise(self, func):
        """设置相机巡航函数"""
        
        if hasattr(func, '__call__'):
            self.cruise = func
            self.animate = True

    def set_range(self, r_x=None, r_y=None, r_z=None):
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

    def add_model(self, name, m):
        """添加模型"""

        if m.inside:
            self.set_range(r_x=m.r_x, r_y=m.r_y, r_z=m.r_z)

        self.models[0].update({name: m})

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

    def text(self, text, pos, color=None, size=32, align='left', valign='bottom', family=None, weight='normal', **kwds):
        """2d文字
 
        text        - 文本字符串
        pos         - 文本位置：元组、列表或numpy数组，shape=(2|3,)
        color       - 文本颜色：浮预定义颜色、十六进制颜色，或者点型元组、列表或numpy数组，None表示背景色的对比色
        size        - 字号：整型，默认32
        align       - 水平对齐方式：'left'-左对齐（默认），'center'-水平居中，'right'-右对齐
        valign      - 垂直对齐方式：'bottom'-底部对齐（默认），'middle'-垂直居中，'top'-顶部对齐
        family          - 字体：None表示当前默认的字体
        weight          - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            slide           - 幻灯片函数，默认None
            ambient         - 环境光，默认(1.0,1.0,1.0)
        """
 
        for key in kwds:
            if key not in ['name', 'visible', 'cull', 'slide', 'ambient']:
                raise KeyError('不支持的关键字参数：%s'%key)
 
        if not kwds.get('slide') is None:
            self.animate = True

        box = np.tile(np.array(pos, dtype=np.float32), (4,1))
        color = self.fg if color is None else util.format_color(color)
        texcoord = np.array([[0,0],[0,1],[1,0],[1,1]], dtype=np.float32)
        align = {'left':0, 'center':1, 'right':2}.get(align, 0) * 3 + {'top':0, 'middle':1, 'bottom':2}.get(valign, 2)
 
        im_text = util.text2img(text, size, color, bg=None, family=family, weight=weight)
        texture = Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        tsize = (size*im_text.shape[1]/im_text.shape[0], size)

        kwds.update({'inside': False})
        name = kwds.pop('name') if 'name' in kwds else uuid.uuid1().hex
        light = Text2dLight(kwds.pop('ambient') if 'ambient' in kwds else (1.0,1.0,1.0))
        kwds.update({'texture':texture, 'texcoord':texcoord, 'align':align, 'tsize':tsize})

        m = light.get_model(GL_TRIANGLE_STRIP, box, **kwds)
        self.add_model(name, m)

    def text3d(self, text, box, color=None, bg=None, align='center', family=None, weight='normal', size=64, **kwds):
        """3d文字
 
        text        - 文本字符串
        box         - 文本显示区域：左上、左下、右下、右上4个点的坐标，浮点型元组、列表或numpy数组，shape=(4,2|3)
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        bg          - 背景色，None表示背景透明
        align       - 文本宽度方向对齐方式
            'fill'          - 填充
            'left'          - 左对齐
            'right'         - 右对齐
            'center'        - 居中对齐
        family      - 字体：None表示当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        size        - 字号：整型，默认64。此参数影响文本显示质量，不改变文本大小
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient         - 环境光，默认(1.0,1.0,1.0)
        """
 
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'cull', 'slide', 'transform', 'ambient']:
                raise KeyError('不支持的关键字参数：%s'%key)
 
        if not kwds.get('slide') is None or not kwds.get('transform') is None:
            self.animate = True

        color = self.fg if color is None else util.format_color(color)
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
 
        im_text = util.text2img(text, size, color, bg=bg, family=family, weight=weight)
        texture = Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        texcoord = np.array([[0,0],[0,1],[1,1],[1,0]], dtype=np.float32)

        kwds.update({'opacity': False})
        name = kwds.pop('name') if 'name' in kwds else uuid.uuid1().hex
        light = BaseLight(kwds.pop('ambient') if 'ambient' in kwds else (1.0,1.0,1.0))
        kwds.update({'texture':texture, 'texcoord':texcoord})

        m = light.get_model(GL_QUADS, box, **kwds)
        self.add_model(name, m)

    def scatter(self, vs, size=1.0, color=None, data=None, cm='viridis', alpha=1.0, **kwds):
        """散列点
 
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        size        - 点的大小：数值或数值型元组、列表或numpy数组
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        data        - 数据集：元组、列表或numpy数组，shape=(n,)
        cm          - 调色板
        alpha       - 透明度
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            opacity         - 模型不透明属性，默认True（不透明）
            inside          - 模型顶点是否影响模型空间，默认True
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient         - 环境光，默认(1.0,1.0,1.0)
        """
 
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'slide', 'transform', 'ambient']:
                raise KeyError('不支持的关键字参数：%s'%key)
 
        if not kwds.get('slide') is None or not kwds.get('transform') is None:
            self.animate = True

        name = kwds.pop('name') if 'name' in kwds else uuid.uuid1().hex
        light = ScatterLight(kwds.pop('ambient') if 'ambient' in kwds else (1.0,1.0,1.0))
        vs = np.array(vs, dtype=np.float32)

        if isinstance(size, (int, float)):
            size = np.ones(vs.shape[0], dtype=np.float32) * size
        else:
            size = np.float32(size)
            if size.shape != (vs.shape[0],):
                raise KeyError('期望size参数为长度等于%d的浮点型数组'%vs.shape[0])
 
        if (not color is None) + (not data is None) > 1:
            raise KeyError('color参数和data参数互斥')
        elif data is None:
            color = util.format_color(color, vs.shape[0])
        else:
            data = np.array(data)
            if data.shape != (vs.shape[0],):
                raise KeyError('期望参数data为长度等于%d的一维数组'%vs.shape[0])
            color = util.cmap(data, cm, alpha=alpha)
 
        if self.haxis=='z':
            idx = np.argsort(-vs[...,1])
        elif vs.shape[1] == 3:
            idx = np.argsort(vs[...,2])
        else:
            idx = np.arange(vs.shape[0])
        
        m = light.get_model(GL_POINTS, vs[idx], color=color[idx], psize=size[idx], **kwds)
        self.add_model(name, m)

    def line(self, vs, color=None, data=None, cm='viridis', alpha=1.0, method='strip', width=None, stipple=None, **kwds):
        """线段
 
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        data        - 数据集：元组、列表或numpy数组，shape=(n,)
        cm          - 调色板
        alpha       - 透明度
        method      - 绘制方法
            'isolate'       - 独立线段
            'strip'         - 连续线段
            'loop'          - 闭合线段
        width       - 线宽：0.0~10.0之间，None使用默认设置
        stipple     - 线型：整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None使用默认设置
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认True（不透明）
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient         - 环境光，默认(1.0,1.0,1.0)
        """
 
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'slide', 'transform', 'ambient']:
                raise KeyError('不支持的关键字参数：%s'%key)
 
        if not kwds.get('slide') is None or not kwds.get('transform') is None:
            self.animate = True

        name = kwds.pop('name') if 'name' in kwds else uuid.uuid1().hex
        light = BaseLight(kwds.pop('ambient') if 'ambient' in kwds else (1.0,1.0,1.0))
        vs = np.array(vs, dtype=np.float32)
 
        if (not color is None) + (not data is None) > 1:
            raise KeyError('color参数和data参数互斥')
        elif data is None:
            color = util.format_color(color, vs.shape[0])
        else:
            data = np.array(data)
            if data.shape != (vs.shape[0],):
                raise KeyError('期望参数data为长度等于%d的一维数组'%vs.shape[0])
            color = util.cmap(data, cm, alpha=alpha)
 
        method = method.lower()
        if method == 'isolate':
            gltype = GL_LINES
        elif method == 'strip':
            gltype = GL_LINE_STRIP
        elif method == 'loop':
            gltype = GL_LINE_LOOP
        else:
            raise ValueError('不支持的线段方法：%s'%method)

        m = light.get_model(gltype, vs, color=color, lw=width, ls=stipple, **kwds)
        self.add_model(name, m)

    def surface(self, vs, color=None, data=None, cm='viridis', alpha=1.0, texture=None, texcoord=None, method='isolate', indices=None, closed=False, **kwds):
        """三角曲面
 
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        data        - 数据集：元组、列表或numpy数组，shape=(n,)
        cm          - 调色板
        alpha       - 透明度
        texture     - 纹理图片，或2D/3D纹理对象
        texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
        method      - 绘制方法
            'isolate'       - 独立三角面
            'strip'         - 带状三角面
            'fan'           - 扇面
        indices     - 顶点索引集，默认None，表示不使用索引
        closed      - 带状三角面或扇面两端闭合：布尔型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认True（不透明）
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
 
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
 
        if not kwds.get('slide') is None or not kwds.get('transform') is None:
            self.animate = True
 
        method = method.lower()
        if method == 'isolate':
            gltype = GL_TRIANGLES
        elif method == 'strip':
            gltype = GL_TRIANGLE_STRIP
        elif method == 'fan':
            gltype = GL_TRIANGLE_FAN
        else:
            raise ValueError('不支持的三角面方法：%s'%method)
 
        if gltype != GL_TRIANGLES and not indices is None:
            raise ValueError('带状三角面或扇面不支持indices参数')
 
        vs = np.array(vs, dtype=np.float32)
        normal = util.get_normal(gltype, vs, indices)

        if closed:
            if gltype == GL_TRIANGLE_STRIP:
                normal[0] += normal[-2]
                normal[1] += normal[-1]
                normal[-2] = normal[0]
                normal[-1] = normal[1]
            elif gltype == GL_TRIANGLE_FAN:
                normal[1] += normal[-1]
                normal[-1] = normal[1]

        if (not color is None) + (not data is None) + (not texture is None) > 1:
            raise KeyError('color参数、data参数和texture参数互斥')
        elif data is None and texture is None:
            color = util.format_color(color, vs.shape[0])
        elif texture is None:
            data = np.array(data)
            if data.shape != (vs.shape[0],):
                raise KeyError('期望参数data为长度等于%d的一维数组'%vs.shape[0])
            color = util.cmap(data, cm, alpha=alpha)
        else:
            if isinstance(texture, str):
                if os.path.exists(texture):
                    texture = Texture(texture)
                else:
                    raise ValueError('文件%s不存在'%texture)

            if not isinstance(texture, Texture) or texture.ttype != GL_TEXTURE_2D and texture.ttype != GL_TEXTURE_3D:
                raise ValueError('期望纹理参数texture为纹理图片或2D/3D纹理对象类型')

            texcoord = np.array(texcoord, dtype=np.float32)
            tn = 2 if texture.ttype == GL_TEXTURE_2D else 3

            if texcoord.shape != (vs.shape[0], tn):
                raise KeyError('期望纹理坐标参数texcoord为%d行%d列的浮点型数组'%(vs.shape[0], tn))
 
        name = kwds.pop('name') if 'name' in kwds else uuid.uuid1().hex
        light = kwds.pop('light') if 'light' in kwds else SunLight(direction=(0,1,0) if self.haxis=='z' else (0,0,-1))
        kwds.update({'normal':normal, 'color':color, 'texture':texture, 'texcoord':texcoord, 'indices':indices})

        m = light.get_model(gltype, vs, **kwds)
        self.add_model(name, m)

    def quad(self, vs, color=None, data=None, cm='viridis', alpha=1.0, texture=None, texcoord=None, method='isolate', indices=None, closed=False, **kwds):
        """四角曲面
        
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        data        - 数据集：元组、列表或numpy数组，shape=(n,)
        cm          - 调色板
        alpha       - 透明度
        texture     - 纹理图片，或2D/3D纹理对象
        texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
        method      - 绘制方法
            'isolate'       - 独立四角面
            'strip'         - 带状四角面
        indices     - 顶点索引集，默认None，表示不使用索引
        closed      - 带状四角面两端闭合：布尔型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认True（不透明）
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
 
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
 
        if not kwds.get('slide') is None or not kwds.get('transform') is None:
            self.animate = True
 
        method = method.upper()
        if method == "ISOLATE":
            gltype = GL_QUADS
        elif method == "STRIP":
            gltype = GL_QUAD_STRIP
        else:
            raise ValueError('不支持的四角面方法：%s'%method)
 
        if gltype == GL_QUAD_STRIP and not indices is None:
            raise ValueError('STRIP不支持indices参数')
 
        vs = np.array(vs, dtype=np.float32)
        normal = util.get_normal(gltype, vs, indices)

        if closed and gltype == GL_QUAD_STRIP:
            normal[0] += normal[-2]
            normal[1] += normal[-1]
            normal[-2] = normal[0]
            normal[-1] = normal[1]

        if (not color is None) + (not data is None) + (not texture is None) > 1:
            raise KeyError('color参数、data参数和texture参数互斥')
        elif data is None and texture is None:
            color = util.format_color(color, vs.shape[0])
        elif texture is None:
            data = np.array(data)
            if data.shape != (vs.shape[0],):
                raise KeyError('期望参数data为长度等于%d的一维数组'%vs.shape[0])
            color = util.cmap(data, cm, alpha=alpha)
        else:
            if isinstance(texture, str):
                if os.path.exists(texture):
                    texture = Texture(texture)
                else:
                    raise ValueError('文件%s不存在'%texture)

            if not isinstance(texture, Texture) or texture.ttype != GL_TEXTURE_2D and texture.ttype != GL_TEXTURE_3D:
                raise ValueError('期望纹理参数texture为纹理图片或2D/3D纹理对象类型')

            texcoord = np.array(texcoord, dtype=np.float32)
            tn = 2 if texture.ttype == GL_TEXTURE_2D else 3

            if texcoord.shape != (vs.shape[0], tn):
                raise KeyError('期望纹理坐标参数texcoord为%d行%d列的浮点型数组'%(vs.shape[0], tn))
 
        name = kwds.pop('name') if 'name' in kwds else uuid.uuid1().hex
        light = kwds.pop('light') if 'light' in kwds else SunLight(direction=(0,1,0) if self.haxis=='z' else (0,0,-1))
        kwds.update({'normal':normal, 'color':color, 'texture':texture, 'texcoord':texcoord, 'indices':indices})

        m = light.get_model(gltype, vs, **kwds)
        self.add_model(name, m)

    def mesh(self, xs, ys, zs, color=None, data=None, cm='viridis', alpha=1.0, texture=None, ur=(0,1), vr=(0,1), ccw=True, **kwds):
        """网格面
        
        xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)，m为网格行数，n为网格列数
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        data        - 数据集：元组、列表或numpy数组，shape=(m,n)
        cm          - 调色板
        alpha       - 透明度
        texture     - 纹理图片，或2D纹理对象
        ur          - u方向纹理坐标范围
        vr          - v方向纹理坐标范围
        ccw         - 逆时针三角面
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
 
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
 
        if not kwds.get('slide') is None or not kwds.get('transform') is None:
            self.animate = True
 
        vs = np.dstack((xs, ys, zs))
        rows, cols = vs.shape[:2]
        vs = vs.reshape(-1,3)
        texcoord = None

        gltype = GL_TRIANGLES
        idx = np.arange(rows*cols).reshape(rows, cols)
        idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[:-1, 1:], idx[1:,1:]
        if ccw:
            indices = np.int32(np.dstack((idx_a, idx_b, idx_c, idx_c, idx_b, idx_d)).ravel())
        else:
            indices = np.int32(np.dstack((idx_a, idx_c, idx_b, idx_b, idx_c, idx_d)).ravel())
        normal = util.get_normal(gltype, vs, indices).reshape(rows,cols,-1)

        if (not color is None) + (not data is None) + (not texture is None) > 1:
            raise KeyError('color参数、data参数和texture参数互斥')
        elif data is None and texture is None:
            color = util.format_color(color, rows*cols)
        elif texture is None:
            data = np.array(data)
            if data.shape != (rows, cols):
                raise KeyError('期望参数data为%d行%d列长度等于%d的二维数组'%(rows, cols))
            color = util.cmap(data, cm, alpha=alpha).reshape(-1, 4)
        else:
            if isinstance(texture, str):
                if os.path.exists(texture):
                    texture = Texture(texture)
                else:
                    raise ValueError('文件%s不存在'%texture)

            if not isinstance(texture, Texture) or texture.ttype != GL_TEXTURE_2D:
                raise ValueError('期望纹理参数texture为纹理图片或2D纹理对象类型')

            u = np.linspace(ur[0], ur[1], cols)
            v = np.linspace(vr[0], vr[1], rows)
            texcoord = np.float32(np.dstack(np.meshgrid(u,v)).reshape(-1,2))        
 
        name = kwds.pop('name') if 'name' in kwds else uuid.uuid1().hex
        light = kwds.pop('light') if 'light' in kwds else SunLight(direction=(0,1,0) if self.haxis=='z' else (0,0,-1))
        kwds.update({'normal':normal, 'color':color, 'texture':texture, 'texcoord':texcoord, 'indices':indices})

        m = light.get_model(gltype, vs, **kwds)
        self.add_model(name, m)

    def uvsphere(self, center, r, color=None, texture=None, ur=(0,1), vr=(0,1), uarc=(0,360), varc=(-90,90), cell=5, **kwds):
        """使用经纬度网格生成球
 
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片，或2D纹理对象
        ur          - u方向纹理坐标范围
        vr          - v方向纹理坐标范围
        uarc        - u方向范围：默认0°~360°
        varc        - v方向范围：默认-90°~90°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """

        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
 
        if not kwds.get('slide') is None or not kwds.get('transform') is None:
            self.animate = True

        u_0, u_1 = np.radians(min(uarc)), np.radians(max(uarc))
        v_0, v_1 = np.radians(max(varc)), np.radians(min(varc))

        cell = np.radians(cell)
        u_slices, v_slices = int(abs(u_0-u_1)/cell)+1, int(abs(v_0-v_1)/cell)+1
        gv, gu = np.mgrid[v_0:v_1:complex(0,v_slices), u_0:u_1:complex(0,u_slices)]
 
        if self.haxis == 'z':
            zs = r * np.sin(gv)
            xs = r * np.cos(gv)*np.cos(gu)
            ys = r * np.cos(gv)*np.sin(gu)
        else:
            ys = r * np.sin(gv)
            xs = r * np.cos(gv)*np.cos(gu)
            zs = -r * np.cos(gv)*np.sin(gu)

        vs = np.dstack((xs, ys, zs))
        rows, cols = vs.shape[:2]
        vs = vs.reshape(-1,3)
        texcoord = None

        gltype = GL_TRIANGLES
        idx = np.arange(rows*cols).reshape(rows, cols)
        idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[:-1, 1:], idx[1:,1:]
        indices = np.int32(np.dstack((idx_a, idx_b, idx_c, idx_c, idx_b, idx_d)).ravel())
        normal = util.get_normal(gltype, vs, indices).reshape(rows,cols,-1)

        if abs(uarc[1]-uarc[0]) == 360:
            normal[:,0] += normal[:,-1]
            normal[:,-1] = normal[:,0]

        if abs(varc[1]-varc[0]) == 180:
            normal[0] = normal[0,0]
            normal[-1] = normal[-1,0]

        if (not color is None) + (not texture is None) > 1:
            raise KeyError('color参数和texture参数互斥')
        elif texture is None:
            color = util.format_color(color, u_slices*v_slices)
        else:
            if isinstance(texture, str):
                if os.path.exists(texture):
                    texture = Texture(texture)
                else:
                    raise ValueError('文件%s不存在'%texture)

            if not isinstance(texture, Texture) or texture.ttype != GL_TEXTURE_2D:
                raise ValueError('期望纹理参数texture为纹理图片或2D纹理对象类型')

            u = np.linspace(ur[0], ur[1], cols)
            v = np.linspace(vr[0], vr[1], rows)
            texcoord = np.float32(np.dstack(np.meshgrid(u,v)).reshape(-1,2))
 
        name = kwds.pop('name') if 'name' in kwds else uuid.uuid1().hex
        light = kwds.pop('light') if 'light' in kwds else SunLight(direction=(0,1,0) if self.haxis=='z' else (0,0,-1))
        kwds.update({'normal':normal, 'color':color, 'texture':texture, 'texcoord':texcoord, 'indices':indices})

        m = light.get_model(gltype, vs, **kwds)
        self.add_model(name, m)

    def isosphere(self, center, r, color=None, iterations=4, **kwds):
        """通过对正二十面体的迭代细分生成球
        
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        iterations  - 迭代次数：整型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
 
        a, b = 0.525731, 0.850651
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
 
        for i in range(iterations):
            p0 = (vs[::3] + vs[1::3]) / 2
            p0 = r * p0 / np.linalg.norm(p0, axis=1).reshape(-1, 1)
            p1 = (vs[1::3] + vs[2::3]) / 2
            p1 = r * p1 / np.linalg.norm(p1, axis=1).reshape(-1, 1)
            p2 = (vs[::3] + vs[2::3]) / 2
            p2 = r * p2 / np.linalg.norm(p2, axis=1).reshape(-1, 1)
            vs = np.stack((vs[::3],p0,p2,vs[1::3],p1,p0,vs[2::3],p2,p1,p0,p1,p2),axis=1).reshape(-1,3)
        vs += np.array(center)
 
        self.surface(vs, color=color, method='isolate', **kwds)

    def cone(self, spire, center, r, color=None, bottom=True, arc=(0,360), cell=5, **kwds):
        """圆锥
 
        spire       - 锥尖：元组、列表或numpy数组
        center      - 锥底圆心：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        bottom      - 绘制锥底：布尔型
        arc         - 弧度角范围：默认0°~360°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
 
        spire = np.array(spire)
        center = np.array(center)
        m_rotate = util.y2v(spire - center)
 
        arc_0, arc_1, cell = np.radians(min(arc)), np.radians(max(arc)), np.radians(cell)
        slices = int(abs(arc_0-arc_1)/cell) + 1
 
        theta = np.linspace(arc_0, arc_1, slices)
        xs = r * np.cos(theta)
        zs = -r * np.sin(theta)
        ys = np.zeros_like(theta)
 
        vs = np.stack((xs,ys,zs), axis=1)
        vs = np.dot(vs, m_rotate) + center
        vs_c = np.vstack((spire, vs))
        color = util.format_color(color)
        closed = abs(arc[1]-arc[0]) == 360
 
        self.surface(vs_c, color=color, method='fan', closed=closed, **kwds)
        if bottom:
            vs_b = np.vstack((center, vs[::-1]))
            self.surface(vs_b, color=color, method='fan', closed=closed, **kwds)

    def _grid(self):
        """网格和刻度 """

        if self.r_x[0] >= self.r_x[-1] or self.r_y[0] >= self.r_y[-1] or self.r_z[0] >= self.r_z[-1]:
            return # '模型空间不存在，返回

        size = self.ticks['size']
        xfunc = self.ticks['xfunc']
        yfunc = self.ticks['yfunc']
        zfunc = self.ticks['zfunc']

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
        def text3d_ticks(text, box, color, bg, loc, cull, align):
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

            color = np.array(color, dtype=np.float32)
            bg = np.array(bg, dtype=np.float32)
            loc = np.repeat(np.array(loc, dtype=np.float32), 4)

            if color.ndim == 1:
                color = np.tile(color, (len(text), 1))
            if bg.ndim == 1:
                bg = np.tile(bg, (len(text), 1))

            im_arr, texcoord = list(), list()
            rows_max, cols_max = 0, 0
            for i in range(len(text)):
                im = util.text2img(text[i], 64, color[i], bg=bg[i])
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
 
                if align == 'left':
                    offset = (box[i][2]-box[i][1])*k_text/k_box
                    box[i][2] = box[i][1] + offset
                    box[i][3] = box[i][0] + offset
                elif align == 'right':
                    offset = (box[i][0] - box[i][3])*k_text/k_box
                    box[i][0] = box[i][3] + offset
                    box[i][1] = box[i][2] + offset
                elif align == 'center':
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

            return m.verify()

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
        self.quad(vs, color=[*self.fg, 0.8], fill=False, cull='front', method='isolate', opacity=False, light=BaseLight())
        self.quad(vs, color=[*self.fg, 0.1], cull='front', method='isolate', opacity=False, light=BaseLight())

        # 以下绘制标注文本
        # ----------------------------------------------------------------------------------------------------
        dx = xx[2] - xx[1]
        dy = yy[2] - yy[1]
        dz = zz[2] - zz[1]
        h = min(dx, dy, dz) * size/240 # 标注文字高度
        eps = 0.02 * h
        text, bg, box, loc = list(), list(), list(), list()

        for x in xx[1:-1]:
            x_str = xfunc(x)
            text.extend([x_str, x_str, x_str, x_str])
            bg.extend([[0.8,0,0], [0.8,0,0], [0.8,0,0], [0.8,0,0]])

            if self.haxis == 'z':
                loc.extend([10, 11, 12, 13])
                box.append([[x-dx,yy[-1]-eps,zz[-1]], [x-dx,yy[-1]-eps,zz[-1]-h], [x+dx,yy[-1]-eps,zz[-1]-h], [x+dx,yy[-1]-eps,zz[-1]]])
                box.append([[x+dx,yy[0]+eps,zz[-1]], [x+dx,yy[0]+eps,zz[-1]-h], [x-dx,yy[0]+eps,zz[-1]-h], [x-dx,yy[0]+eps,zz[-1]]])
                box.append([[x-dx,yy[-1]-eps,zz[0]+h], [x-dx,yy[-1]-eps,zz[0]], [x+dx,yy[-1]-eps,zz[0]], [x+dx,yy[-1]-eps,zz[0]+h]])
                box.append([[x+dx,yy[0]+eps,zz[0]+h], [x+dx,yy[0]+eps,zz[0]], [x-dx,yy[0]+eps,zz[0]], [x-dx,yy[0]+eps,zz[0]+h]])

            else:
                loc.extend([10, 11, 12, 13])
                box.append([[x-dx,yy[-1],zz[0]+eps], [x-dx,yy[-1]-h,zz[0]+eps], [x+dx,yy[-1]-h,zz[0]+eps], [x+dx,yy[-1],zz[0]+eps]])
                box.append([[x+dx,yy[-1],zz[-1]-eps], [x+dx,yy[-1]-h,zz[-1]-eps], [x-dx,yy[-1]-h,zz[-1]-eps], [x-dx,yy[-1],zz[-1]-eps]])
                box.append([[x-dx,yy[0]+h,zz[0]+eps], [x-dx,yy[0],zz[0]+eps], [x+dx,yy[0],zz[0]+eps], [x+dx,yy[0]+h,zz[0]+eps]])
                box.append([[x+dx,yy[0]+h,zz[-1]-eps], [x+dx,yy[0],zz[-1]-eps], [x-dx,yy[0],zz[-1]-eps], [x-dx,yy[0]+h,zz[-1]-eps]])

        for y in yy[1:-1]:
            y_str = yfunc(y)
            text.extend([y_str, y_str, y_str, y_str])
            bg.extend([[0,0.5,0], [0,0.5,0], [0,0.5,0], [0,0.5,0]])

            if self.haxis == 'z':
                loc.extend([20, 21, 22, 23])
                box.append([[xx[0]+eps,y-dy,zz[-1]], [xx[0]+eps,y-dy,zz[-1]-h], [xx[0]+eps,y+dy,zz[-1]-h], [xx[0]+eps,y+dy,zz[-1]]])
                box.append([[xx[-1]-eps,y+dy,zz[-1]], [xx[-1]-eps,y+dy,zz[-1]-h], [xx[-1]-eps,y-dy,zz[-1]-h], [xx[-1]-eps,y-dy,zz[-1]]])
                box.append([[xx[0]+eps,y-dy,zz[0]+h], [xx[0]+eps,y-dy,zz[0]], [xx[0]+eps,y+dy,zz[0]], [xx[0]+eps,y+dy,zz[0]+h]])
                box.append([[xx[-1]-eps,y+dy,zz[0]+h], [xx[-1]-eps,y+dy,zz[0]], [xx[-1]-eps,y-dy,zz[0]], [xx[-1]-eps,y-dy,zz[0]+h]])
            else:
                loc.extend([0, 1, 2, 3])
                box.append([[xx[0]+eps,y+dy,zz[-1]-h], [xx[0]+eps,y+dy,zz[-1]], [xx[0]+eps,y-dy,zz[-1]], [xx[0]+eps,y-dy,zz[-1]-h]])
                box.append([[xx[0]+h,y+dy,zz[0]+eps], [xx[0],y+dy,zz[0]+eps], [xx[0],y-dy,zz[0]+eps], [xx[0]+h,y-dy,zz[0]+eps]])
                box.append([[xx[-1]-eps,y+dy,zz[0]+h], [xx[-1]-eps,y+dy,zz[0]], [xx[-1]-eps,y-dy,zz[0]], [xx[-1]-eps,y-dy,zz[0]+h]])
                box.append([[xx[-1]-h,y+dy,zz[-1]-eps], [xx[-1],y+dy,zz[-1]-eps], [xx[-1],y-dy,zz[-1]-eps], [xx[-1]-h,y-dy,zz[-1]-eps]])

        for z in zz[1:-1]:
            z_str = zfunc(z)
            text.extend([z_str, z_str, z_str, z_str])
            bg.extend([[0,0,0.6], [0,0,0.6], [0,0,0.6], [0,0,0.6]])

            if self.haxis == 'z':
                loc.extend([0, 1, 2, 3])
                box.append([[xx[0]+eps,yy[0]+h,z+dz], [xx[0]+eps,yy[0],z+dz], [xx[0]+eps,yy[0],z-dz], [xx[0]+eps,yy[0]+h,z-dz]])
                box.append([[xx[0]+h,yy[-1]-eps,z+dz], [xx[0],yy[-1]-eps,z+dz], [xx[0],yy[-1]-eps,z-dz], [xx[0]+h,yy[-1]-eps,z-dz]])
                box.append([[xx[-1]-eps,yy[-1]-h,z+dz], [xx[-1]-eps,yy[-1],z+dz], [xx[-1]-eps,yy[-1],z-dz], [xx[-1]-eps,yy[-1]-h,z-dz]])
                box.append([[xx[-1]-h,yy[0]+eps,z+dz], [xx[-1],yy[0]+eps,z+dz], [xx[-1],yy[0]+eps,z-dz], [xx[-1]-h,yy[0]+eps,z-dz]])
            else:
                loc.extend([20, 21, 22, 23])
                box.append([[xx[0]+eps,yy[-1],z+dz], [xx[0]+eps,yy[-1]-h,z+dz], [xx[0]+eps,yy[-1]-h,z-dz], [xx[0]+eps,yy[-1],z-dz]])
                box.append([[xx[-1]-eps,yy[-1],z-dz], [xx[-1]-eps,yy[-1]-h,z-dz], [xx[-1]-eps,yy[-1]-h,z+dz], [xx[-1]-eps,yy[-1],z+dz]])
                box.append([[xx[0]+eps,yy[0]+h,z+dz], [xx[0]+eps,yy[0],z+dz], [xx[0]+eps,yy[0],z-dz], [xx[0]+eps,yy[0]+h,z-dz]])
                box.append([[xx[-1]-eps,yy[0]+h,z-dz], [xx[-1]-eps,yy[0],z-dz], [xx[-1]-eps,yy[0],z+dz], [xx[-1]-eps,yy[0]+h,z+dz]])

        name = uuid.uuid1().hex
        m = text3d_ticks(text, box, self.fg, bg, loc, 'back', 'center')
        self.add_model(name, m)

    def grid(self, **kwds):
        """网格和刻度
        kwds        - 关键字参数
            size            - 刻度文本字号，默认32
            xfunc           - x轴标注格式化函数
            yfunc           - y轴标注格式化函数
            zfunc           - z轴标注格式化函数
        """

        self.ticks = {
            'size':     kwds.get('size', 32),
            'xfunc':    kwds.get('xfunc', str),
            'yfunc':    kwds.get('yfunc', str),
            'zfunc':    kwds.get('zfunc', str)
        }

    def title(self, title, size=32, color=None, family=None, weight='normal'):
        """设置标题

        title       - 标题文本
        size        - 字号：整型，默认32
        color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
        family      - 字体：None表示当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        """

        color = self.fg if color is None else util.format_color(color)
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
        self.models[1].update({'caption_text': m_text})
        self.models[1].update({'caption_line': m_line})

    def colorbar(self, cm, data, tfunc=str, endpoint=True):
        """设置调色板

        cm          - 调色板名称
        data        - 值域范围或刻度序列：长度大于1的元组或列表
        kwds        - 关键字参数
        tfunc       - 刻度标注格式化函数，默认str
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
        color_line = util.format_color(self.fg, vs_line.shape[0])

        m_line = light.get_model(GL_LINES, vs_line, color=color_line, method='isolate', inside=False)
        self.models[2].update({'cb_line': m_line})

        # 绘制刻度文本
        # --------------------------------------------------------------------
        im_arr, texcoord, box = list(), list(), list()
        rows_max, cols_max = 0, 0
        for i in range(len(data)):
            im = util.text2img(tfunc(data[i]), 64, self.fg)
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
        self.models[2].update({'cb_label': m_label})

