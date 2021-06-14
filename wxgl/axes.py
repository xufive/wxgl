# -*- coding: utf-8 -*-

import re
import uuid
import numpy as np

from . import region


class WxGLAxes:
    """子图类"""
    
    def __init__(self, scene, pos, padding=(20,20,20,20)):
        """构造函数
        
        scene       - 所属场景对象
        pos         - 子图在画布上的位置和大小
                        三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                        四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
        padding     - 四元组，上、右、下、左四个方向距离边缘的留白像素
        """
        
        assert isinstance(padding, (list,tuple)) and len(padding) == 4, '期望参数padding是长度为4的元组或列表'
        
        self.scene = scene
        self.ff = self.scene.parent
        self.fig = self.scene.parent.parent
        self.cm = self.scene.cm
        
        if isinstance(pos, (str, int)) and re.compile(r'^[\d]{3}$').match(str(pos)):
            rows, cols, cell = [int(ch) for ch in str(pos)]
            i, j = (cell-1)//cols, (cell-1)%cols
            w_cell, h_cell = self.scene.size[0]/cols, self.scene.size[1]/rows 
            p = (padding[0]/h_cell, padding[1]/w_cell, padding[2]/h_cell, padding[3]/w_cell)
            box = ((j+p[3])/cols, 1-(i+1-p[2])/rows, (1-p[1]-p[3])/cols, (1-p[0]-p[2])/rows)
        elif isinstance(pos, (list,tuple)) and len(padding) == 4:
            w_cell, h_cell = self.scene.size[0], self.scene.size[1]
            p = (padding[0]/h_cell, padding[1]/w_cell, padding[2]/h_cell, padding[3]/w_cell)
            box = (pos[0]+p[3], pos[1]+p[2], pos[2]-p[1]-p[3], pos[3]+-p[0]-p[2])
        else:
            raise ValueError("期望参数pos是三个数字组成的整数或字符串，或者长度为4的元组或列表")
        
        self.reg_main = self.scene.add_region(box)
        self.reg_title = None
        self.reg_cb = None
    
    def plot(self, x, y, z=None, color=None, cm=None, size=0.0, width=1.0, style='solid', method='SINGLE', **kwds):
        """绘制点和线
        
        x/y/z       - 顶点的x/y/z坐标集，元组、列表或一维数组，长度相等。若zs为None，则自动补为全0数组
        color       - 颜色，或每个顶点对应的数据（使用cm参数映射为每一个顶点的颜色）
        cm          - 颜色映射表
        size        - 顶点大小。若为0或None，则表示不绘制点，只绘制线
        width       - 线宽，0.0~10.0之间的浮点数。若为0或None，则表示不绘制线，只绘制点
        style       - 线型
                        'solid'     - 实线
                        'dashed'    - 虚线
                        'dotted'    - 点线
                        'dash-dot'  - 虚点线
        method      - 绘制方法
                        'MULTI'     - 线段
                        'SINGLE'    - 连续线段
                        'LOOP'      - 闭合线段
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        regulate    - 顶点集几何变换，None或者元组、列表，其元素为位移向量三元组，或由旋转角度、旋转向量组成的二元组
                        rotate      - None或者旋转函数，以场景的自增计数器为输入，返回旋转角度和旋转向量组成的元组
                        translate   - None或者位移函数，以场景的自增计数器为输入，返回位移元组
                        order       - 几何变换的顺序
                            None        - 无变换（默认）
                            'R'         - 仅旋转变换
                            'T'         - 仅位移变换
                            'RT'        - 先旋转后位移
                            'TR'        - 先位移后旋转
        """
        
        if isinstance(x, (tuple,list)):
            x = np.array(x)
        
        if isinstance(y, (tuple,list)):
            y = np.array(y)
        
        if z is None:
            z = np.zeros(x.shape)
            self.scene.set_mode('2D')
            self.scene.set_style('white')
        elif isinstance(z, (tuple,list)):
            z = np.array(z)
        
        assert x.shape == y.shape == z.shape and x.ndim == 1, '参数xs/ys/zs长度不一致'
        
        if cm is None:
            color = self.cm.color2c(color)
        else:
            if isinstance(color, (tuple,list)):
                color = np.array(color)
            assert isinstance(color, np.ndarray) and color.shape == x.shape and x.ndim == 1, '期望参数color是和xyz长度相同的元组、列表或numpy数组'
            color = self.cm.cmap(color, cm)
        
        vs = np.stack((x, y, z), axis=1)
        style = {'solid':(1, 0xFFFF), 'dashed':(1, 0xFFF0), 'dotted':(1, 0xF0F0), 'dash-dot':(1, 0xFF18)}[style]
        
        if not width is None and width > 0:
            self.fig.add_widget(self.reg_main, 'line', vs, color, method=method, width=width, stipple=style, **kwds)
        if not size is None and size > 0:
            self.fig.add_widget(self.reg_main, 'point', vs, color, size=size, **kwds)
        
    def colorbar(self, drange, cmap, loc, **kwds):
        """绘制colorbar
        
        drange      - 值域范围，tuple类型
        cmap        - 调色板名称
        loc         - 位置，top|bottom|left|right
        kwds        - 关键字参数
                        length          - ColorBar所在视区的长边长度，默认短边长度为1
                        subject         - 标题
                        subject_size    - 标题字号
                        label_size      - 标注字号
                        label_format    - 标注格式化所用lambda函数
                        label_precision - 标注精度，形如'%.2f'或'%d'
                        tick_line       - 刻度线长度
                        endpoint        - 刻度是否包含值域范围的两个端点值
                        name            - 模型名
                        inside          - 是否更新数据动态范围
                        visible         - 是否显示
        """
        
        if loc == 'left':
            b0, b1, b2, b3 = self.reg_main.box
            box = (b0, b1, b2*0.2, b3)
            self.reg_main.reset_box((b0+b2*0.2, b1, b2*0.8, b3))
            reg_cb = self.scene.add_region(box, fixed=True)
        elif loc == 'right':
            b0, b1, b2, b3 = self.reg_main.box
            box = (b0+b2*0.8, b1, b2*0.2, b3)
            self.reg_main.reset_box((b0, b1, b2*0.8, b3))
            reg_cb = self.scene.add_region(box, fixed=True)
        elif loc == 'bottom':
            b0, b1, b2, b3 = self.reg_main.box
            box = (b0, b1, b2, b3*0.15)
            self.reg_main.reset_box((b0, b1+b3*0.15, b2, b3*0.85))
            reg_cb = self.scene.add_region(box, fixed=True)
        elif loc == 'top':
            b0, b1, b2, b3 = self.reg_main.box
            box = (b0, b1+b3*0.85, b2, b3*0.15)
            self.reg_main.reset_box((b0, b1, b2, b3*0.85))
            reg_cb = self.scene.add_region(box, fixed=True)
        
        self.fig.add_widget(reg_cb, 'colorbar', drange, cmap, loc, **kwds)
    
    def title(self, text, size=48, color=None, pos=(0,0,0), **kwds):
        """绘制标题
        
        text        - 文本字符串
        size        - 文字大小，整形
        color       - 文本颜色，预定义的颜色，或长度为3的列表或元组
        pos         - 文本位置，list或numpy.ndarray类型，shape=(3，)
        kwds        - 关键字参数
                        align       - left/right/center分别表示左对齐、右对齐、居中（默认）
                        valign      - top/bottom/middle分别表示上对齐、下对齐、垂直居中（默认）
                        family      - （系统支持的）字体
                        weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
        """
        
        for key in kwds:
            if key not in ['align', 'valign', 'family', 'weight']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        align = kwds.get('align', 'center')
        valign = kwds.get('valign', 'middle')
        weight = kwds.get('weight', 'bold')
        family = kwds.get('family', None)
        
        if not self.reg_title:
            b0, b1, b2, b3 = self.reg_main.box
            box = (b0, b1+b3*0.88, b2, b3*0.12)
            self.reg_main.reset_box((b0, b1, b2, b3*0.88))
            self.reg_title = self.scene.add_region(box, fixed=True)
        
        self.fig.add_widget(self.reg_title, 'text3d', text, size=size*4, color=color, pos=pos, **kwds)
    
    def text(self, text, size=32, color=None, pos=(0,0,0), **kwds):
        """绘制文本
        
        text        - 文本字符串
        size        - 文字大小，整形
        color       - 文本颜色，预定义的颜色，或长度为3的列表或元组
        pos         - 文本位置，list或numpy.ndarray类型，shape=(3，)
        kwds        - 关键字参数
                        align       - left/right/center分别表示左对齐、右对齐、居中（默认）
                        valign      - top/bottom/middle分别表示上对齐、下对齐、垂直居中（默认）
                        family      - （系统支持的）字体
                        weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
        """
        
        for key in kwds:
            if key not in ['align', 'valign', 'family', 'weight']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        align = kwds.get('align', 'center')
        valign = kwds.get('valign', 'middle')
        weight = kwds.get('weight', 'bold')
        family = kwds.get('family', None)
        
        self.fig.add_widget(self.reg_main, 'text3d', text, size=size, color=color, pos=pos, **kwds)
    
    def scatter(self, vs, color=None, size=1.0, cmap='hsv', caxis='z'):
        """绘制散点图
        
        vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
        color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
        size        - 顶点的大小，整型或浮点型
        cmap        - 颜色映射表，color为None时有效。使用vs的z坐标映射颜色
        caxis       - 用于颜色映射的坐标轴数据，2D模式下自动转为'y'
        """
        
        assert isinstance(vs, np.ndarray) and vs.ndim == 2, '期望参数vs是二维数组'
        assert isinstance(size, (float, int)), '期望参数size是整型或浮点型'
        assert cmap in self.cm.cms, '未知的颜色映射表名："%s"'%cmap
        
        if color is None:
            if self.scene.mode == '2D':
                caxis = 'y'
            
            if caxis == 'x':
                color = self.cm.cmap(vs[:,0], cmap)
            elif caxis == 'y':
                color = self.cm.cmap(vs[:,1], cmap)
            else:
                color = self.cm.cmap(vs[:,2], cmap)
        
        self.fig.add_widget(self.reg_main, 'point', vs, color, size=size)
    
    def mesh(self, xs, ys, zs, color=None, mode='FCBC', cmap='hsv', caxis='z', **kwds):
        """绘制mesh
        
        xs/ys/zs    - 顶点的x/y/z坐标集，二维数组
        color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
        mode        - 显示模式
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        cmap        - 颜色映射表，color为None时有效。使用zs映射颜色
        caxis       - 用于颜色映射的坐标轴数据，2D模式下自动转为'y'
        kwds        - 关键字参数
                        light       - 材质灯光颜色，None表示关闭材质灯光
                        slide       - 是否作为动画播放的帧
                        name        - 模型名
        """
        
        for key in kwds:
            if key not in ['light', 'slide', 'name']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        assert isinstance(xs, np.ndarray) and xs.ndim == 2, '期望参数vs是二维数组'
        assert isinstance(ys, np.ndarray) and ys.ndim == 2, '期望参数ys是二维数组'
        assert isinstance(zs, np.ndarray) and zs.ndim == 2, '期望参数zs是二维数组'
        assert xs.shape == ys.shape == zs.shape, '期望参数xs、ys和zs的具有相同的结构'
        assert cmap in self.cm.cms, '未知的颜色映射表名："%s"'%cmap
        
        if color is None:
            if self.scene.mode == '2D':
                caxis = 'y'
            
            if caxis == 'x':
                color = self.cm.cmap(xs, cmap)
            elif caxis == 'y':
                color = self.cm.cmap(ys, cmap)
            else:
                color = self.cm.cmap(zs, cmap)
        
        self.fig.add_widget(self.reg_main, 'mesh', xs, ys, zs, color, mode=mode, **kwds)
    
    def surface(self, vs, color=None, method='Q', mode='FCBC', texture=None, alpha=True, **kwds):
        """绘制surface
        
        vs          - 顶点坐标集，二维数组类型，shape=(n,3)
        color       - 顶点颜色或颜色集，可以混合使用纹理。None表示仅使用纹理
        method      - 绘制方法
                        'Q'         - 四边形
                                        0--3 4--7
                                        |  | |  |
                                        1--2 5--6
                        'T'         - 三角形
                                        0--2 3--5
                                         \/   \/
                                          1    4
                        'Q+'        - 边靠边的连续四边形
                                       0--2--4
                                       |  |  |
                                       1--3--5
                        'T+'        - 边靠边的连续三角形
                                       0--2--4
                                        \/_\/_\
                                         1  3  5
                        'F'         - 扇形
                        'P'         - 多边形
        mode        - 显示模式
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        texture     - 用于纹理的图像文件或数组对象，仅当method为Q时有效
        alpha       - 纹理是否使用透明通道，仅当texture存在时有效
        kwds        - 关键字参数
                        light       - 材质灯光颜色，None表示关闭材质灯光
                        slide       - 是否作为动画播放的帧
                        name        - 模型名
        """
        
        for key in kwds:
            if key not in ['light', 'slide', 'name']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        assert isinstance(vs, np.ndarray) and vs.ndim == 2, '期望参数vs是二维数组'
        
        if isinstance(texture, (str, np.ndarray)) and method == 'Q':
            texture = self.reg_main.create_texture(texture, alpha=alpha)
            texcoord = np.tile(np.array([[0,1],[0,0],[1,0],[1,1]]), (vs.shape[0]//4,1))
        else:
            texture, texcoord = None, None
        
        self.fig.add_widget(self.reg_main, 'surface', vs, color=color, method=method, mode=mode, texcoord=texcoord, texture=texture, **kwds)
    
    def pipe(self, vs, radius, color=None, slices=36, mode='FCBC', cmap='hsv', caxis='z'):
        """绘制圆管
        
        vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
        radius      - 圆管半径，浮点型
        color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
        slices      - 圆管面分片数（数值越大越精细）
        mode        - 显示模式
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        cmap        - 颜色映射表，color为None时有效。使用vs的z坐标映射颜色
        caxis       - 用于颜色映射的坐标轴数据，2D模式下自动转为'y'
        """
        
        assert isinstance(vs, np.ndarray) and vs.ndim == 2, '期望参数vs是二维数组'
        assert cmap in self.cm.cms, '未知的颜色映射表名："%s"'%cmap
        
        if color is None:
            if self.scene.mode == '2D':
                caxis = 'y'
            
            if caxis == 'x':
                color = self.cm.cmap(vs[:,0], cmap)
            elif caxis == 'y':
                color = self.cm.cmap(vs[:,1], cmap)
            else:
                color = self.cm.cmap(vs[:,2], cmap)
        
        self.fig.add_widget(self.reg_main, 'pipe', vs, radius, color, slices=slices, mode=mode)
    
    def sphere(self, center, radius, color, slices=90, mode='FLBL'):
        """绘制球体
        
        center      - 球心坐标，元组、列表或数组
        radius      - 半径，浮点型
        color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
        slices      - 球面分片数（数值越大越精细）
        mode        - 显示模式
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        """
        
        assert isinstance(center, (tuple, list, np.ndarray)), '期望参数center是元组、列表或数组'
        
        self.fig.add_widget(self.reg_main, 'sphere', center, radius, color, slices=slices, mode=mode)
    
    def cube(self, center, side, color, mode='FLBL'):
        """绘制六面体
        
        center      - 中心坐标，元组、列表或数组
        side        - 棱长，整型、浮点型，或长度为3的元组、列表数组
        color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
        mode        - 显示模式
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        """
        
        assert isinstance(center, (tuple, list, np.ndarray)), '期望参数center是元组、列表或数组'
        
        self.fig.add_widget(self.reg_main, 'cube', center, side, color, mode=mode)
    
    def cylinder(self, v_top, v_bottom, radius, color, slices=60, mode='FCBC'):
        """绘制圆柱体
        
        v_top       - 圆柱上端面的圆心坐标，元组、列表或numpy数组
        v_bottom    - 圆柱下端面的圆心坐标，元组、列表或numpy数组
        radius      - 半径，浮点型
        color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
        slices      - 圆柱面分片数（数值越大越精细）
        mode        - 显示模式
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        """
        
        assert isinstance(v_top, (tuple, list, np.ndarray)), '期望参数v_top是元组、列表或数组'
        assert isinstance(v_bottom, (tuple, list, np.ndarray)), '期望参数v_bottom是元组、列表或数组'
        
        self.fig.add_widget(self.reg_main, 'cylinder', v_top, v_bottom, radius, color, slices=slices, mode=mode)
    
    def cone(self, center, spire, radius, color, slices=60, mode='FCBC'):
        """绘制圆锥体
        
        center      - 锥底圆心坐标，元组、列表或数组
        spire       - 锥尖坐标，元组、列表或数组
        radius      - 半径，浮点型
        color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
        slices      - 锥面分片数（数值越大越精细）
        mode        - 显示模式
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        """
        
        assert isinstance(center, (tuple, list, np.ndarray)), '期望参数center是元组、列表或数组'
        
        self.fig.add_widget(self.reg_main, 'cone', center, spire, radius, color, slices=slices, mode=mode)
    
    def capsule(self, data, threshold, color, r_x=None, r_y=None, r_z=None, mode='FCBC', **kwds):
        """绘制囊（三维等值面）
        
        data        - 数据集，numpy.ndarray类型，shape=(layers,rows,cols)
        threshold   - 阈值，浮点型
        color       - 表面颜色
        r_x         - x的动态范围，元组
        r_y         - y的动态范围，元组
        r_z         - z的动态范围，元组
        mode        - 显示模式
                        None        - 使用当前设置
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否显示
                        light       - 材质灯光开关
        """
        
        self.fig.add_widget(self.reg_main, 'capsule', data, threshold, color, r_x=r_x, r_y=r_y, r_z=r_z, mode=mode, **kwds)
    
    def flow(self, ps, us, vs, ws, **kwds):
        """绘制流体
        
        ps          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
        us          - 顶点u分量集，numpy.ndarray类型，shape=(n,)
        vs          - 顶点v分量集，numpy.ndarray类型，shape=(n,)
        ws          - 顶点w分量集，numpy.ndarray类型，shape=(n,)
        kwds        - 关键字参数
                        color       - 轨迹线颜色，None表示使用速度映射颜色
                        actor       - 顶点模型类型，'point'|'line'两个选项
                        size        - point大小
                        width       - line宽度
                        length      - 轨迹线长度，以速度矢量的模为单位
                        duty        - 顶点line模型长度与轨迹线长度之比（占空比），建议值为0.4
                        frames      - 总帧数
                        interval    - 帧间隔，以ms为单位
                        threshold   - 高通阈值，滤除速度小于阈值的数据点
                        name        - 模型名
        """
        
        self.fig.add_widget(self.reg_main, 'flow', ps, us, vs, ws, **kwds)
        
    def ticks(self, **kwds):
        """显示网格和刻度
        
        kwds        - 关键字参数
                        segment_min     - 标注最少分段数量
                        segment_max     - 标注最多分段数量
                        label_2D3D      - 标注试用2D或3D文字
                        label_size      - 标注字号
                        xlabel_format   - x轴标注格式化所用lambda函数
                        ylabel_format   - y轴标注格式化所用lambda函数
                        zlabel_format   - z轴标注格式化所用lambda函数
                        
        """
        
        self.fig.add_widget(self.reg_main, 'ticks', **kwds)
    