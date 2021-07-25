# -*- coding: utf-8 -*-

import re
import uuid
import numpy as np
from scipy import ndimage

from . import region
from . import util


class WxGLAxes:
    """子图类"""
    
    def __init__(self, scene, pos):
        """构造函数
        
        scene       - 所属场景对象
        pos         - 子图在画布上的位置和大小
                        三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                        四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
        """
        
        self.scene = scene
        self.ff = self.scene.parent
        self.fig = self.ff.parent
        self.cm = self.scene.cm
        
        w, h = self.scene.size
        margin, padding = 0.05, 0.01
        
        if isinstance(pos, (str, int)) and re.compile(r'^[1-9]{3}$').match(str(pos)): 
            rows, cols, cell = [int(ch) for ch in str(pos)]
            i, j = (cell-1)//cols, (cell-1)%cols
            cw, ch = (1-2*margin)/cols, (1-2*margin)/rows
            box = (margin+padding+j*cw, margin+padding+(rows-1-i)*ch, cw-2*padding, ch-2*padding)
        elif isinstance(pos, (list,tuple)) and len(pos) == 4:
            box = (pos[0]+padding, pos[1]+padding, pos[2]-2*padding, pos[3]-2*padding)
        else:
            raise ValueError("期望参数pos是三个数字组成的整数或字符串，或者长度为4的元组或列表")
        
        self.reg_main = self.scene.add_region(box)      # 主视区
        self.reg_title = None                           # 标题视区
        self.reg_cb_r = None                            # 右侧色条视区
        self.reg_cb_l = None                            # 左侧色条视区
        self.reg_cb_b = None                            # 底部色条视区
        self.reg_cb_br = None                           # 底部右侧色条视区
        self.reg_cb_bl = None                           # 底部左侧色条视区
        
        self.grid_is_show = True                        # 网格是否显示
        self.axis_is_show = True                        # 坐标轴是否显示（仅2D模式有效）
        self.ci = 0                                     # 默认颜色选择指针
        self.cbargs = None                              # ColorBar参数
        
        self.drange = None
        self.cbcm = None
        
        self.labelx = 'X'                               # x轴名称
        self.labely = 'Y'                               # y轴名称
        self.labelz = 'Z'                               # z轴名称
        self.xf = str                                   # x轴标注格式化函数
        self.yf = str                                   # y轴标注格式化函数
        self.zf = str                                   # z轴标注格式化函数
        self.xd = 0                                     # x轴标注密度
        self.yd = 0                                     # y轴标注密度
        self.zd = 0                                     # z轴标注密度
        self.rotatex = False                            # x轴标注是否旋转
        self.reversey = False                           # y轴是否反转
    
    def get_color(self):
        """返回下一个可用的默认颜色"""
        
        color = self.cm.default_colors[self.ci]
        self.ci = (self.ci+1)%len(self.cm.default_colors)
        
        return color
    
    def set_2d_mode(self):
        """设置scene为2D模式"""
        
        h2d_offset = -0.1 if self.axis_is_show else 0
        zoom = 1.5 if self.scene.zoom == 1 else self.scene.zoom
        
        self.scene.set_proj('ortho')
        self.scene.set_mode('2D')
        self.scene.set_style(self.fig.style2d)
        self.scene.set_posture(zoom=zoom, oecs=(h2d_offset,0,0), dist=5, azimuth=0, elevation=0, save=True)
    
    def xlabel(self, xlabel):
        """设置x轴名称，text为文本字符串"""
        
        self.labelx = xlabel
    
    def ylabel(self, ylabel):
        """设置y轴名称"""
        
        self.labely = ylabel
    
    def zlabel(self, zlabel):
        """设置z轴名称"""
        
        self.labelz = zlabel
    
    def xformat(self, xf):
        """格式化x轴的标注"""
        
        self.xf = xf
    
    def yformat(self, yf):
        """格式化y轴的标注"""
        
        self.yf = yf
    
    def zformat(self, zf):
        """格式化z轴的标注"""
        
        self.zf = zf
    
    def xdensity(self, xd):
        """设置x轴标注疏密度"""
        
        self.xd = xd
    
    def ydensity(self, yd):
        """设置y轴标注疏密度"""
        
        self.yd = yd
    
    def zdensity(self, zd):
        """设置z轴标注疏密度"""
        
        self.zd = zd
    
    def axis(self, visible):
        """设置坐标轴是否可见"""
        
        self.axis_is_show = visible
        if self.scene.mode == '2D':
            h2d_offset = -0.1 if self.axis_is_show else 0
            self.scene.set_posture(oecs=(h2d_offset,0,0), save=True)
    
    def grid(self, visible):
        """设置网格是否可见"""
        
        self.grid_is_show = visible
    
    def xrotate(self):
        """旋转x轴的标注"""
        
        self.rotatex = True
    
    def title(self, text, size=64, color=None, **kwds):
        """绘制标题
        
        text        - 文本字符串
        size        - 文字大小，整形，默认64
        color       - 文本颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
        kwds        - 关键字参数
                        family      - （系统支持的）字体，None表示当前默认的字体
                        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        """
        
        for key in kwds:
            if key not in ['family', 'weight']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        family = kwds.get('family', None)
        weight = kwds.get('weight', 'bold')
        kwds = {'family':family, 'weight':weight, 'align':'center-middle', 'inside':False, 'light':0}
        
        if self.reg_title is None:
            if self.reg_cb_b is None and self.reg_cb_bl is None and self.reg_cb_br is None:
                k = 0.15
            else:
                k = 0.17647
            
            a0, a1, a2, a3 = self.reg_main.box
            x, w = a0, a2
            self.reg_main.reset_box((a0, a1, a2, a3*(1-k)))
            
            if not self.reg_cb_r is None:
                b0, b1, b2, b3 = self.reg_cb_r.box
                w += b2
                self.reg_cb_r.reset_box((b0, b1, b2, b3*(1-k)))
            
            if not self.reg_cb_l is None:
                c0, c1, c2, c3 = self.reg_cb_l.box
                x = c0
                w += c2
                self.reg_cb_l.reset_box((c0, c1, c2, c3*(1-k)))
            
            box = (x, a1+a3*(1-k), w, a3*k)
            self.reg_title = self.scene.add_region(box, fixed=True, proj='ortho')
        
        box = np.array([[-1,0,0],[-1,-0.3,0],[1,-0.3,0],[1,0,0]])
        self.fig.add_widget(self.reg_title, 'text3d', text, box, size=size, color=color, **kwds)
        
    def colorbar(self, drange=None, cm=None, loc='right', **kwds):
        """绘制colorbar
        
        drange      - 值域范围或标注序列，元组或列表，None表示使用当前设置
        cm          - 调色板名称，None表示使用当前设置
        loc         - 位置
                        right           - 右侧
                        left            - 左侧
                        bottom          - 底部
                        bottom-left     - 底部
                        bottom-right    - 底部
        kwds        - 关键字参数
                        subject         - 标题
                        subject_size    - 标题字号，默认44
                        tick_size       - 刻度字号，默认40
                        tick_format     - 刻度标注格式化函数，默认str
                        density         - 刻度密度，最少和最多刻度线组成的元组，默认(3,6)
                        endpoint        - 刻度是否包含值域范围的两个端点值
        """
        
        if drange is None:
            if self.cbargs:
                drange = self.cbargs['drange']
            else:
                return
                
        if cm is None:
            if self.cbargs:
                cm = self.cbargs['cm']
            else:
                return
        
        if not loc in ('right','left','bottom','bottom-left','bottom-right'):
            raise ValueError('不支持的位置选项：%s'%loc)
        
        if loc == 'right':
            if self.reg_cb_r is None:
                k = 0.15 if self.reg_cb_l is None else 0.17647
                a0, a1, a2, a3 = self.reg_main.box
                self.reg_main.reset_box((a0, a1, a2*(1-k), a3))
                
                box = (a0+a2*(1-k), a1, a2*k, a3)
                self.reg_cb_r = self.scene.add_region(box, fixed=True, proj='ortho')
            
            self.fig.add_widget(self.reg_cb_r, 'colorbar', drange, cm, mode='VR', **kwds)
        elif loc == 'left':
            if self.reg_cb_l is None:
                k = 0.15 if self.reg_cb_r is None else 0.17647
                a0, a1, a2, a3 = self.reg_main.box
                self.reg_main.reset_box((a0+a2*k, a1, a2*(1-k), a3))
                
                box = (a0, a1, a2*k, a3)
                self.reg_cb_l = self.scene.add_region(box, fixed=True, proj='ortho')
            
            self.fig.add_widget(self.reg_cb_l, 'colorbar', drange, cm, mode='VL', **kwds)
        else:
            if self.reg_cb_b is None and self.reg_cb_bl is None and self.reg_cb_br is None:
                k = 0.15 if self.reg_title is None else 0.17647
                h = self.reg_main.box[-1]*k
                
                a0, a1, a2, a3 = self.reg_main.box
                self.reg_main.reset_box((a0, a1+a3*k, a2, a3*(1-k)))
                
                if not self.reg_cb_r is None:
                    b0, b1, b2, b3 = self.reg_cb_r.box
                    self.reg_cb_r.reset_box((b0, b1+b3*k, b2, b3*(1-k)))
                
                if not self.reg_cb_l is None:
                    c0, c1, c2, c3 = self.reg_cb_l.box
                    self.reg_cb_l.reset_box((c0, c1+c3*k, c2, c3*(1-k)))
            elif self.reg_title is None:
                h = 0.17647*self.reg_main.box[-1]
            else:
                h = self.reg_title.box[-1]
            
            a0, a1, a2, a3 = self.reg_main.box
            if loc == 'bottom-left':
                box = (a0, a1-h, 0.6*a2, h)
                self.reg_cb_bl = self.scene.add_region(box, fixed=True, proj='ortho')
                self.fig.add_widget(self.reg_cb_bl, 'colorbar', drange, cm, mode='H', **kwds)
            elif loc == 'bottom-right':
                box = (a0+0.4*a2, a1-h, 0.6*a2, h)
                self.reg_cb_br = self.scene.add_region(box, fixed=True, proj='ortho')
                self.fig.add_widget(self.reg_cb_br, 'colorbar', drange, cm, mode='H', **kwds)
            else:
                box = (a0, a1-h, a2, h)
                self.reg_cb_b = self.scene.add_region(box, fixed=True, proj='ortho')
                self.fig.add_widget(self.reg_cb_b, 'colorbar', drange, cm, mode='H', **kwds)
        
        self.cbargs = None
    
    def text(self, text, pos, size=40, color=None, align=None, family=None, weight='normal', **kwds):
        """绘制文本
        
        text        - 文本字符串
        pos         - 文本位置，元组、列表或numpy数组
        size        - 文字大小，整形，默认40
        color       - 文本颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
        align       - 对齐方式
                        None            - 2D模式默认'left-bottom'，3D模式默认横排文字
                        'left-top'      - 以pos为左上角（仅2D模式有效）
                        'left-middle'   - 以pos为左侧中（仅2D模式有效）
                        'left-bottom'   - 以pos为左下角（仅2D模式有效）
                        'right-top'     - 以pos为右上角（仅2D模式有效）
                        'right-middle'  - 以pos为右侧中（仅2D模式有效）
                        'right-bottom'  - 以pos为右下角（仅2D模式有效）
                        'center-top'    - 以pos为中间上（仅2D模式有效）
                        'center-middle' - 以pos为中心点（仅2D模式有效）
                        'center-bottom' - 以pos为中间下（仅2D模式有效）
                        'VR'            - 竖排文字，自上而下（仅3D模式有效）
                        'VL'            - 竖排文字，自下而上（仅3D模式有效）
        family      - （系统支持的）字体
        weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
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
        
        if len(pos) == 2:
            self.set_2d_mode()
            
            x, y = pos
            if align == 'left-top':
                box = np.array([[x,y,0],[x,y-0.1,0],[x+0.1,y-0.1,0],[x+0.1,y,0]])
            elif align == 'left-middle':
                box = np.array([[x,y+0.1,0],[x,y-0.1,0],[x+0.1,y-0.1,0],[x+0.1,y+0.1,0]])
            elif align == 'right-top':
                box = np.array([[x-0.1,y,0],[x-0.1,y-0.1,0],[x,y-0.1,0],[x,y,0]])
            elif align == 'right-bottom':
                box = np.array([[x-0.1,y+0.1,0],[x-0.1,y,0],[x,y,0],[x,y+0.1,0]])
            elif align == 'right-middle':
                box = np.array([[x-0.1,y+0.1,0],[x-0.1,y-0.1,0],[x,y-0.1,0],[x,y+0.1,0]])
            elif align == 'center-top':
                box = np.array([[x-0.1,y,0],[x-0.1,y-0.1,0],[x+0.1,y-0.1,0],[x+0.1,y,0]])
            elif align == 'center-bottom':
                box = np.array([[x-0.1,y+0.1,0],[x-0.1,y,0],[x+0.1,y,0],[x+0.1,y+0.1,0]])
            elif align == 'center-middle':
                box = np.array([[x-0.1,y+0.1,0],[x-0.1,y-0.1,0],[x+0.1,y-0.1,0],[x+0.1,y+0.1,0]])
            else:
                box = np.array([[x,y+0.1,0],[x,y,0],[x+0.1,y,0],[x+0.1,y+0.1,0]])
                align = 'left-bottom'
            
            kwds.update({'light':0, 'inside':False})
            self.fig.add_widget(self.reg_main, 'text3d', text, box, size=size, color=color, family=family, weight=weight, align=align, **kwds)
        else:
            if align not in ('VR', 'VL'):
                align = None
            kwds.update({'inside':False})
            self.fig.add_widget(self.reg_main, 'text', text, pos, size=size, color=color, family=family, weight=weight, align=align, **kwds)
    
    def text3d(self, text, box, size=32, color=None, family=None, weight='normal', align=None, **kwds):
        """绘制3D文字
        
        text        - 文本字符串
        box         - 文本显式区域的左上、左下、右下、右上4个点的坐标，浮点型元组、列表或numpy数组
        size        - 文字大小，整型
        color       - 文本颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
        family      - （系统支持的）字体，None表示当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        align       - 对齐方式
                        None            - 自动填充box（默认）
                        'left-top'      - 水平左对齐，垂直上对齐
                        'left-middle'   - 水平左对齐，垂直居中对齐
                        'left-bottom'   - 水平左对齐，垂直下对齐
                        'right-top'     - 水平右对齐，垂直上对齐
                        'right-middle'  - 水平右对齐，垂直居中对齐
                        'right-bottom'  - 水平右对齐，垂直下对齐
                        'center-top'    - 水平居中对齐，垂直上对齐
                        'center-middle' - 水平居中对齐，垂直居中对齐
                        'center-bottom' - 水平居中对齐，垂直下对齐
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
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
        
        kwds.update({'light':0, 'inside':False})
        self.fig.add_widget(self.reg_main, 'text3d', text, box, size=size, color=color, family=family, weight=weight, align=align, **kwds)
    
    def plot(self, xs, ys, zs=None, color=None, cm=None, drange=None, size=0, width=1, style='solid', **kwds):
        """绘制点和线
        
        xs/ys/zs    - 点的x/y/z坐标集，等长的一维元组、列表或numpy数组。若zs为None，则自动切换为2D模式
        color       - 颜色，或每个顶点对应的数据（此种情况下cm参数不能为None）
        cm          - 颜色映射表，仅当参数color为每个顶点对应的数据时有效
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        size        - 点的大小，若为0或None，则表示不绘制点，只绘制线
        width       - 线宽，0.0~10.0之间的浮点数。若为0或None，则表示不绘制线，只绘制点
        style       - 线型
                        'solid'     - 实线 
                        'dashed'    - 虚线
                        'dotted'    - 点线
                        'dash-dot'  - 虚点线
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
        
        # xs/ys/zs参数处理
        if isinstance(xs, (tuple,list)):
            xs = np.array(xs)
        
        if isinstance(ys, (tuple,list)):
            ys = np.array(ys)
        
        if zs is None:
            self.set_2d_mode()
            zs = np.zeros(xs.shape)
        elif isinstance(zs, (tuple,list)):
            zs = np.array(zs)
        
        assert isinstance(xs, np.ndarray) and xs.ndim == 1, '期望参数xs是一维的元组、列表或numpy数组'
        assert isinstance(ys, np.ndarray) and ys.ndim == 1, '期望参数ys是一维的元组、列表或numpy数组'
        assert isinstance(zs, np.ndarray) and zs.ndim == 1, '期望参数zs是一维的元组、列表或numpy数组'
        assert xs.shape == ys.shape == zs.shape, '期望参数xs/ys/zs长度一致'
        
        vs = np.stack((xs, ys, zs), axis=1)
        
        # color参数处理
        if cm is None:
            if color is None: # 如果没有指定颜色，则顺序选择默认的颜色
                color = self.get_color()
            
            color = self.cm.color2c(color)
            cbargs = None
        else:
            if isinstance(color, (tuple,list)):
                color = np.array(color)
            
            if not isinstance(color, np.ndarray) or not color.ndim == 1 or not color.shape[0] == vs.shape[0]:
                raise ValueError('参数cm有效时，期望参数color是和xs/ys/zs等长的元组、列表或numpy数组')
            
            if drange is None:
                cbargs = {'cm':cm, 'drange':(np.nanmin(color), np.nanmax(color))}
            else:
                cbargs = None
            
            color = self.cm.cmap(color, cm, drange=drange, drop=True)
        
        # style参数处理
        if not style in ('solid', 'dashed', 'dotted','dash-dot'):
            raise ValueError('期望参数style是solid|dashed|dotted|dash-dot之一')
        stipple = {'solid':(1, 0xFFFF), 'dashed':(1, 0xFFF0), 'dotted':(1, 0xF0F0), 'dash-dot':(1, 0xFF18)}[style]
        
        # 添加到部件库
        if not width is None and width > 0:
            self.fig.add_widget(self.reg_main, 'line', vs, color, width=width, stipple=stipple, method='SINGLE', **kwds)
        if not size is None and size > 0:
            self.fig.add_widget(self.reg_main, 'point', vs, color, size=size, **kwds)
        
        # ColorBar参数
        self.cbargs = cbargs
        
    def line(self, vs, color=None, cm=None, drange=None, width=1, method='multi', style='solid', **kwds):
        """绘制线段
        
        vs          - 点坐标集，二维元组、列表或numpy数组
        color       - 颜色，或每个顶点对应的数据（此种情况下cm参数不能为None）
        cm          - 颜色映射表，仅当参数color为每个顶点对应的数据时有效
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        width       - 线宽，0.0~10.0之间，None表示使用当前设置
        method      - 绘制方法
                        'multi'     - 线段
                        'single'    - 连续线段
                        'loop'      - 闭合线段
        style       - 线型
                        'solid'     - 实线 
                        'dashed'    - 虚线
                        'dotted'    - 点线
                        'dash-dot'  - 虚点线
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
        
        # vs参数处理
        if isinstance(vs, (tuple,list)):
            vs = np.array(vs)
        assert isinstance(vs, np.ndarray) and vs.ndim == 2, '期望参数vs是二维的numpy数组，或类似结构的元组、列表'
        
        if vs.shape[-1] == 2:
            z = np.zeros((vs.shape[0],1))
            vs = np.hstack((vs,z))
            self.set_2d_mode()
        
        # color参数处理
        if cm is None:
            if color is None: # 如果没有指定颜色，则顺序选择默认的颜色
                color = self.get_color()
            
            color = self.cm.color2c(color)
            cbargs = None
        else:
            if isinstance(color, (tuple,list)):
                color = np.array(color)
            
            if not isinstance(color, np.ndarray) or not color.ndim == 1 or not color.shape[0] == vs.shape[0]:
                raise ValueError('参数cm有效时，期望参数color是和vs等长的元组、列表或numpy数组')
            
            if drange is None:
                cbargs = {'cm':cm, 'drange':(np.nanmin(color), np.nanmax(color))}
            else:
                cbargs = None
            
            color = self.cm.cmap(color, cm, drange=drange, drop=True)
        
        # method参数处理
        if not method.lower() in ('multi', 'single', 'loop'):
            raise ValueError('期望参数method是multi|single|loop之一')
        method = method.upper()
        
        # style参数处理
        if not style in ('solid', 'dashed', 'dotted','dash-dot'):
            raise ValueError('期望参数style是solid|dashed|dotted|dash-dot之一')
        stipple = {'solid':(1, 0xFFFF), 'dashed':(1, 0xFFF0), 'dotted':(1, 0xF0F0), 'dash-dot':(1, 0xFF18)}[style]
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, 'line', vs, color, width=width, method=method, stipple=stipple, **kwds)
        
        # ColorBar参数
        self.cbargs = cbargs
    
    def scatter(self, vs, color=None, cm=None, drange=None, size=1.0, **kwds):
        """绘制散点图
        
        vs          - 点坐标集，二维元组、列表或numpy数组
        color       - 颜色，或每个点对应的数据（此种情况下cm参数不能为None）
        cm          - 颜色映射表，仅当参数color为每个点对应的数据时有效
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        size        - 点或每个点的大小
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
        
        # vs参数处理
        if isinstance(vs, (tuple,list)):
            vs = np.array(vs)
        assert isinstance(vs, np.ndarray) and vs.ndim == 2, '期望参数vs是二维的numpy数组，或类似结构的元组、列表'
        
        if vs.shape[-1] == 2:
            z = np.zeros((vs.shape[0],1))
            vs = np.hstack((vs,z))
            self.set_2d_mode()
        
        # color参数处理
        if cm is None:
            if color is None: # 如果没有指定颜色，则顺序选择默认的颜色
                color = self.get_color()
            
            color = self.cm.color2c(color, size=len(vs))
            cbargs = None
        else:
            if isinstance(color, (tuple,list)):
                color = np.array(color)
            
            if not isinstance(color, np.ndarray) or not color.ndim == 1 or not color.shape[0] == vs.shape[0]:
                raise ValueError('参数cm有效时，期望参数color是和vs等长的元组、列表或numpy数组')
            
            if drange is None:
                cbargs = {'cm':cm, 'drange':(np.nanmin(color), np.nanmax(color))}
            else:
                cbargs = {'cm':cm, 'drange':drange}
            
            color = self.cm.cmap(color, cm, drange=drange, drop=True)
        
        # size参数处理
        if isinstance(size, (float, int)):
            self.fig.add_widget(self.reg_main, 'point', vs, color, size=size, **kwds)
        else:
            if isinstance(size, (tuple,list)):
                size = np.array(size)
            
            if not isinstance(size, np.ndarray) or not size.ndim == 1 or not size.shape[0] == vs.shape[0]:
                raise ValueError('期望参数size是和vs等长的元组、列表或numpy数组')
            
            for i in range(len(size)):
                self.fig.add_widget(self.reg_main, 'point', vs[i:i+1], color[i], size=size[i], **kwds)
        
        # ColorBar参数
        self.cbargs = cbargs
    
    def mesh(self, xs, ys, zs=None, color=None, cm=None, drange=None, texture=None, **kwds):
        """绘制网格
        
        xs/ys/zs    - 点的x/y/z坐标集，结构相同的二维元组、列表或数组。若zs为None，则自动切换为2D模式
        color       - 颜色，或每个点对应的数据。texture为None时该参数有效
        cm          - 颜色映射表
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        texture     - 纹理图片文件或numpy数组形式的图像数据
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        # xs/ys/zs参数处理
        if isinstance(xs, (tuple,list)):
            xs = np.array(xs)
        
        if isinstance(ys, (tuple,list)):
            ys = np.array(ys)
        
        if zs is None:
            self.set_2d_mode()
            kwds.update({'light':0})
            zs = np.zeros(xs.shape)
        elif isinstance(zs, (tuple,list)):
            zs = np.array(zs)
        
        assert isinstance(xs, np.ndarray) and xs.ndim == 2, '期望参数xs是二维数组，或类似结构的元组、列表'
        assert isinstance(ys, np.ndarray) and ys.ndim == 2, '期望参数ys是二维数组，或类似结构的元组、列表'
        assert isinstance(zs, np.ndarray) and zs.ndim == 2, '期望参数zs是二维数组，或类似结构的元组、列表'
        assert xs.shape == ys.shape == zs.shape, '期望参数xs/ys/zs结构相同'
        
        # color参数处理
        if texture is None:
            if color is None:
                color = self.get_color() # 顺序选择默认的颜色
            
            if isinstance(color, str):
                c = self.cm.color2c(color, size=(2,2))
                cbargs = None
            else:
                if isinstance(color, (tuple,list)):
                    color = np.array(color)
                assert isinstance(color, np.ndarray), '期望参数color是numpy数组，或类似结构的元组、列表'
                
                if color.ndim == 1:
                    c = self.cm.color2c(color, size=(2,2))
                    cbargs = None
                elif color.ndim == 2 and not cm is None:
                    if drange is None:
                        cbargs = {'cm':cm, 'drange':(np.nanmin(color), np.nanmax(color))}
                    else:
                        cbargs = {'cm':cm, 'drange':drange}
                    
                    c = self.cm.cmap(color, cm, drange=drange)
                else:
                    raise ValueError("期望参数color是单个颜色的表述或类二维数组，或参数cm不应为None")
            texture = np.uint8(c*255)
        else:
            cbargs = None
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, '_mesh', xs, ys, zs, texture, **kwds)
        
        # ColorBar参数
        self.cbargs = cbargs
    
    def surface(self, vs, color=None, texture=None, texcoord=None, method='Q', **kwds):
        """绘制表面
        
        vs          - 点坐标集，二维元组、列表或numpy数组
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据。纹理图片左上、左下、右下和右上对应纹理坐标(0,1)、(0,0)、(1,0)和(1,1)
        texcoord    - 顶点的纹理坐标集，元组、列表或numpy数组，shape=(n,2)
        method      - 绘制方法
                        'Q'         - 四边形（默认）
                                        0--3 4--7
                                        |  | |  |
                                        1--2 5--6
                        'T'         - 三角形
                                        0--2 3--5
                                         \/   \/
                                          1    4
                        'F'         - 扇形（vs首元素为中心点，其余元素为圆弧上顺序排列的点）
                        'P'         - 多边形（vs为多边形顺序列出的顶点）
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        # vs参数处理
        if isinstance(vs, (tuple,list)):
            vs = np.array(vs)
        assert isinstance(vs, np.ndarray) and vs.ndim == 2, '期望参数vs是二维的numpy数组，或类似结构的元组、列表'
        
        if vs.shape[-1] == 2:
            self.set_2d_mode()
            kwds.update({'light':0})
            z = np.zeros((vs.shape[0],1))
            vs = np.hstack((vs,z))
        
        if method == 'P':
            assert texture is None and texcoord is None, '绘制多边形不支持texture参数和texcoord参数'
        
        if texture is None or texcoord is None:
            if color is None:
                color = self.get_color() # 顺序选择默认的颜色
            
            c = self.cm.color2c(color, size=(2,2))
            texture = np.uint8(c*255)
            texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, '_surface', vs, texture, texcoord, method, **kwds)
        
        # ColorBar参数
        self.cbargs = None
    
    def _qtf(self, method, vs, color, cm, drange, texture, texcoord, **kwds):
        """绘制四角面、三角面和扇面的底层公用函数"""
        
        # vs参数处理
        if isinstance(vs, (tuple,list)):
            vs = np.array(vs)
        assert isinstance(vs, np.ndarray) and vs.ndim == 2, '期望参数vs是二维的numpy数组，或类似结构的元组、列表'
        
        if vs.shape[-1] == 2:
            self.set_2d_mode()
            kwds.update({'light':0})
            z = np.zeros((vs.shape[0],1))
            vs = np.hstack((vs,z))
        
        # color参数处理
        if texture is None:
            if color is None:
                color = self.get_color() # 顺序选择默认的颜色
            
            if isinstance(color, str):
                c = self.cm.color2c(color, size=(2,2))
                texture = np.uint8(c*255)
                texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
                cbargs = None
            else:
                if isinstance(color, (tuple,list)):
                    color = np.array(color)
                assert isinstance(color, np.ndarray), '期望参数color是numpy数组，或类似结构的元组、列表'
                
                if color.ndim == 1:
                    c = self.cm.color2c(color, size=(2,2))
                    texture = np.uint8(c*255)
                    texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
                    cbargs = None
                elif color.ndim == 2 and not cm is None and  not texcoord is None:
                    if drange is None:
                        cbargs = {'cm':cm, 'drange':(np.nanmin(color), np.nanmax(color))}
                    else:
                        cbargs = {'cm':cm, 'drange':drange}
                    
                    c = self.cm.cmap(color, cm, drange=drange)
                    texture = np.uint8(c*255)
                else:
                    raise ValueError("期望参数color是单个颜色或二维数据（此种情况下参数cm和texcoord均不能为None）")
        else:
            cbargs = None
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, '_surface', vs, texture, texcoord, method, **kwds)
        
        # ColorBar参数
        self.cbargs = cbargs
    
    def quad(self, vs, color=None, cm=None, drange=None, texture=None, texcoord=None, **kwds):
        """绘制一个或多个四角面（每个四角面的四个顶点通常在一个平面上）
        
        vs          - 点坐标集，二维元组、列表或numpy数组
        color       - 颜色，或二维数据。texture为None时该参数有效
        cm          - 颜色映射表
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        texture     - 纹理图片文件或numpy数组形式的图像数据。纹理图片左上、左下、右下和右上对应纹理坐标(0,1)、(0,0)、(1,0)和(1,1)
        texcoord    - 顶点的纹理坐标集，元组、列表或numpy数组，shape=(n,2)
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        self._qtf('Q', vs, color, cm, drange, texture, texcoord, **kwds)
    
    def triangle(self, vs, color=None, cm=None, drange=None, texture=None, texcoord=None, **kwds):
        """绘制一个或多个三角面
        
        vs          - 点坐标集，二维元组、列表或numpy数组
        color       - 颜色，或二维数据。texture为None时该参数有效
        cm          - 颜色映射表
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        texture     - 纹理图片文件或numpy数组形式的图像数据。纹理图片左上、左下、右下和右上对应纹理坐标(0,1)、(0,0)、(1,0)和(1,1)
        texcoord    - 顶点的纹理坐标集，元组、列表或numpy数组，shape=(n,2)
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        self._qtf('T', vs, color, cm, drange, texture, texcoord, **kwds)
    
    def fan(self, vs, color=None, cm=None, drange=None, texture=None, texcoord=None, **kwds):
        """绘制绘制扇面
        
        vs          - 点坐标集，二维元组、列表或numpy数组
        color       - 颜色，或二维数据。texture为None时该参数有效
        cm          - 颜色映射表
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        texture     - 纹理图片文件或numpy数组形式的图像数据。纹理图片左上、左下、右下和右上对应纹理坐标(0,1)、(0,0)、(1,0)和(1,1)
        texcoord    - 顶点的纹理坐标集，元组、列表或numpy数组，shape=(n,2)
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        self._qtf('F', vs, color, cm, drange, texture, texcoord, **kwds)
    
    def polygon(self, vs, color=None, **kwds):
        """绘制多边形
        
        vs          - 点坐标集，二维元组、列表或numpy数组
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        # vs参数处理
        if isinstance(vs, (tuple,list)):
            vs = np.array(vs)
        assert isinstance(vs, np.ndarray) and vs.ndim == 2, '期望参数vs是二维的numpy数组，或类似结构的元组、列表'
        
        if vs.shape[-1] == 2:
            self.set_2d_mode()
            kwds.update({'light':0})
            z = np.zeros((vs.shape[0],1))
            vs = np.hstack((vs,z))
        
        if color is None:
            color = self.get_color() # 顺序选择默认的颜色
        
        c = self.cm.color2c(color, size=(2,2))
        texture = np.uint8(c*255)
        texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, '_surface', vs, texture, texcoord, 'P', **kwds)
        
        # ColorBar参数
        self.cbargs = None
    
    def cube(self, center, side, color=None, texture=None, **kwds):
        """绘制六面体
        
        center      - 中心坐标，元组、列表或numpy数组
        side        - 棱长，整型、浮点型，或长度为3的元组、列表、numpy数组
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据，color为None时有效
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        if color is None and texture is None:
            color = self.get_color()
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, 'cube', center, side, color=color, texture=texture, **kwds)
        
        # ColorBar参数
        self.cbargs = None
    
    def circle(self, center, radius, normal, color=None, texture=None, slices=360, **kwds):
        """绘制圆面
        
        center      - 球心坐标，元组、列表或numpy数组
        radius      - 半径，浮点型
        normal      - 圆面法向量
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据，color为None时有效
        slices      - 分片数，整型
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        if color is None and texture is None:
            color = self.get_color()
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, 'circle', center, radius, normal, color=color, texture=texture, slices=slices, **kwds)
        
        # ColorBar参数
        self.cbargs = None
    
    def sphere(self, center, radius, color=None, texture=None, slices=360, **kwds):
        """绘制球面
        
        center      - 球心坐标，元组、列表或numpy数组
        radius      - 半径，浮点型
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据，color为None时有效
        slices      - 分片数，整型，默认360
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        if color is None and texture is None:
            color = self.get_color()
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, 'sphere', center, radius, color=color, texture=texture, slices=slices, **kwds)
        
        # ColorBar参数
        self.cbargs = None
    
    def cone(self, center, spire, radius, color=None, texture=None, base=None, slices=360, **kwds):
        """绘制圆锥面
        
        center      - 锥底圆心坐标，元组、列表或numpy数组
        spire       - 锥尖坐标，元组、列表或numpy数组
        radius      - 锥底半径，浮点型
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据，color为None时有效
        slices      - 分片数，整型，默认360
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
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
        
        if color is None and texture is None:
            color = self.get_color()
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, 'cone', center, spire, radius, color=color, texture=texture, base=base, slices=slices, **kwds)
        
        # ColorBar参数
        self.cbargs = None
    
    def cylinder(self, center, radius, color=None, texture=None, top=None, base=None, slices=360, **kwds):
        """绘制圆柱体
        
        center      - 圆柱上下端面圆心坐标，元组、列表或numpy数组，每个元素表示一个端面的圆心坐标
        radius      - 圆柱上下端面半径，浮点型或元组、列表或numpy数组，每个元素表示一个端面的半径
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据，color为None时有效
        top         - 上端面颜色，None表示无上端面
        base        - 下端面颜色，None表示无下端面
        slices      - 分片数，整型 默认360
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
                        regulate    - 顶点集几何变换，None或者元组、列表，其元素为位移向量三元组，或由旋转角度、旋转向量组成的二元组
                        rotate      - None或者旋转函数，以场景的自增计数器为输入，返回旋转角度和旋转向量组成的元组
                        translate   - None或者位移函数，以场景的自增计数器为输入，返回位移元组
                        order       - 几何变换的顺序
                            None        - 无变换（默认）
                            'R'         - 仅旋转变换
                            'T'         - 仅位移变换
                            'RT'        - 先旋转后位移
                            'TR'        - 先位移后旋转v_top       - 圆柱上端面的圆心坐标，元组、列表或numpy数组
        """
        
        if color is None and texture is None:
            color = self.get_color()
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, 'cylinder', center, radius, color=color, texture=texture, top=None, base=base, slices=slices, **kwds)
        
        # ColorBar参数
        self.cbargs = None
    
    def pipe(self, vs, radius, color=None, cm=None, drange=None, slices=90, **kwds):
        """绘制圆管
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)
        radius      - 圆管半径，浮点型
        color       - 颜色或颜色集，或每个顶点对应的数据（此种情况下cm参数不能为None）
        cm          - 颜色映射表，仅当参数color为每个顶点对应的数据时有效
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        slices      - 圆管面分片数（数值越大越精细）
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
                        regulate    - 顶点集几何变换，None或者元组、列表，其元素为位移向量三元组，或由旋转角度、旋转向量组成的二元组
                        rotate      - None或者旋转函数，以场景的自增计数器为输入，返回旋转角度和旋转向量组成的元组
                        translate   - None或者位移函数，以场景的自增计数器为输入，返回位移元组
                        order       - 几何变换的顺序
                            None        - 无变换（默认）
                            'R'         - 仅旋转变换
                            'T'         - 仅位移变换
                            'RT'        - 先旋转后位移
                            'TR'        - 先位移后旋转v_top       - 圆柱上端面的圆心坐标，元组、列表或numpy数组
        """
        
        if cm is None:
            if color is None: # 如果没有指定颜色，则顺序选择默认的颜色
                color = self.get_color()
            
            color = self.cm.color2c(color)
            cbargs = None
        else:
            if isinstance(color, (tuple,list)):
                color = np.array(color)
            
            if not isinstance(color, np.ndarray) or not color.ndim == 1 or not color.shape[0] == vs.shape[0]:
                raise ValueError('参数cm有效时，期望参数color是和vs等长的一维数组，或类似结构的元组、列表')
            
            if drange is None:
                cbargs = {'cm':cm, 'drange':(np.nanmin(color), np.nanmax(color))}
            else:
                cbargs = {'cm':cm, 'drange':drange}
            
            color = self.cm.cmap(color, cm, drange=drange, drop=True)
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, 'pipe', vs, radius, color, slices=slices, **kwds)
        
        # ColorBar参数
        self.cbargs = cbargs
    
    def flow(self, vs, uvw, color=None, cm=None, drange=None, k=1, width=0.3, fs=10, speed=2, cdeep=16, **kwds):
        """绘制动态矢量图
        
        vs          - 点坐标集，二维numpy数组，或类似结构的元组、列表
        uvw         - 与点坐标集对应的矢量集，二维numpy数组，或类似结构的元组、列表
        color       - 颜色，或与矢量集对应的数据
        cm          - 颜色映射表
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        k           - 矢量缩放因子，浮点型
        width       - 矢量线宽度
        fs          - 动态变化的帧数，整型
        speed       - 动态变化的速度因子，整型。该数值越大，变化速度越慢
        cdeep       - 颜色分段数，默认分为16段
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
        
        if not isinstance(vs, np.ndarray):
            vs = np.array(vs)
        
        if not isinstance(uvw, np.ndarray):
            uvw = np.array(uvw)
        
        assert vs.shape == uvw.shape and vs.ndim == 2, '期望参数vs和uvw是结构相同的二维numpy数组，或类似结构的元组、列表'
        
        if vs.shape[-1] == 2:
            self.set_2d_mode()
            x, y = vs[..., 0], vs[..., 1]
            z = np.zeros(x.shape)
            u, v = uvw[..., 0], uvw[..., 1]
            w = np.zeros(u.shape)
        else:
            x, y, z = vs[..., 0], vs[..., 1], vs[..., 2]
            u, v, w = uvw[..., 0], uvw[..., 1], uvw[..., 2]
        
        u, v, w = u*k, v*k, w*k
        du, dv, dw = u/fs, v/fs, w/fs
        offset = np.random.randint(0, fs , u.shape)
        
        def s_creator(i):
            def slide(n):
                return (n//speed)%fs == i
            return slide
        
        # color参数处理
        if cm is None:
            if color is None: # 如果没有指定颜色，则顺序选择默认的颜色
                color = self.get_color()
            
            cbargs = None
            for i in range(fs):
                j = (offset+i)%fs
                xx = np.stack((x+j*du, x+j*du+u), axis=1).ravel()
                yy = np.stack((y+j*dv, y+j*dv+v), axis=1).ravel()
                zz = np.stack((z+j*dw, z+j*dw+w), axis=1).ravel()
                vs = np.stack((xx,yy,zz), axis=1)
                
                slide = s_creator(i)
                self.line(vs, color=color, width=width, slide=slide, **kwds)
        else:
            if isinstance(color, (tuple,list)):
                color = np.array(color)
            assert color.shape[0] == uvw.shape[0], '期望参数color和uvw的长度相同的一维numpy数组，或类似结构的元组、列表'
            
            if drange is None:
                drange = np.nanmin(color), np.nanmax(color)
            
            cbargs = {'cm':cm, 'drange':drange}
            color = np.uint8((cdeep-1)*(color-drange[0])/(drange[1]-drange[0]))
            
            for c in range(cdeep):
                cc = self.cm.cmap(np.array([c]), cm, drange=(0, cdeep-1), drop=True)
                part = np.where(color==c)
                for i in range(fs):
                    j = (offset+i)%fs
                    xx = np.stack((x[part]+j[part]*du[part], x[part]+j[part]*du[part]+u[part]), axis=1).ravel()
                    yy = np.stack((y[part]+j[part]*dv[part], y[part]+j[part]*dv[part]+v[part]), axis=1).ravel()
                    zz = np.stack((z[part]+j[part]*dw[part], z[part]+j[part]*dw[part]+w[part]), axis=1).ravel()
                    vs = np.stack((xx,yy,zz), axis=1)
                    
                    if vs.shape[0]:
                        slide = s_creator(i)
                        self.line(vs, color=cc[0], width=width, slide=slide, **kwds)
        
        # ColorBar参数
        self.cbargs = cbargs
    
    def volume(self, data, x=None, y=None, z=None, **kwds):
        """绘制体数据
        
        data        - 数据，四维numpy数组，第0轴对应z轴，第1轴对应y轴，第2轴对应x轴，第3轴对应每个点的RGBA通道（单字节无符号整型）
        x/y/z       - 等长的一维元组、列表或数组。若为None，则使用data的索引
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
                        regulate    - 顶点集几何变换，None或者元组、列表，其元素为位移向量三元组，或由旋转角度、旋转向量组成的二元组
                        rotate      - None或者旋转函数，以场景的自增计数器为输入，返回旋转角度和旋转向量组成的元组
                        translate   - None或者位移函数，以场景的自增计数器为输入，返回位移元组
                        order       - 几何变换的顺序
                            None        - 无变换（默认）
                            'R'         - 仅旋转变换
                            'T'         - 仅位移变换
                            'RT'        - 先旋转后位移
                            'TR'        - 先位移后旋转v_top       - 圆柱上端面的圆心坐标，元组、列表或numpy数组
        """
        
        assert isinstance(data, np.ndarray) and data.ndim ==4, '期望参数data是一个numpy.ndarray类型的四维数组'
        assert data.shape[-1] == 4 and data.dtype == np.uint8, '期望参数data表示的颜色包含RGBA四个通道且是8位的无符号整型'
        
        zn, yn, xn = data.shape[:3]
        
        if x is None:
            x = np.arange(data.shape[2])
        elif isinstance(x, (tuple, list)):
            x =  np.array(x)
        assert isinstance(x, np.ndarray) and x.ndim == 1 and x.size == xn, '期望参数x是一个长度为%d一维数组'%xn
        
        if y is None:
            y = np.arange(data.shape[1])
        elif isinstance(y, (tuple, list)):
            y =  np.array(y)
        assert isinstance(y, np.ndarray) and y.ndim == 1 and y.size == yn, '期望参数y是一个长度为%d一维数组'%yn
        
        if z is None:
            z = np.arange(data.shape[0])
        elif isinstance(z, (tuple, list)):
            z =  np.array(z)
        assert isinstance(z, np.ndarray) and z.ndim == 1 and z.size == zn, '期望参数z是一个长度为%d一维数组'%zn
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, 'volume', x, y, z, data, **kwds)
        
        # ColorBar参数
        self.cbargs = None
    
    def capsule(self, data, level, color=None, x=None, y=None, z=None, **kwds):
        """绘制囊性结构
        
        data        - 数据集，三维数组，第0轴对应z轴，第1轴对应y轴，第2轴对应x轴
        level       - 阈值，浮点型。data数据集中小于level的点将被忽略
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        x/y/z       - 等长的一维元组、列表或数组。若为None，则使用data的索引
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            4           - 开启左光源
                            8           - 开启右光源
                            15          - 开启全部光源（默认）
                        regulate    - 顶点集几何变换，None或者元组、列表，其元素为位移向量三元组，或由旋转角度、旋转向量组成的二元组
                        rotate      - None或者旋转函数，以场景的自增计数器为输入，返回旋转角度和旋转向量组成的元组
                        translate   - None或者位移函数，以场景的自增计数器为输入，返回位移元组
                        order       - 几何变换的顺序
                            None        - 无变换（默认）
                            'R'         - 仅旋转变换
                            'T'         - 仅位移变换
                            'RT'        - 先旋转后位移
                            'TR'        - 先位移后旋转v_top       - 圆柱上端面的圆心坐标，元组、列表或numpy数组
        """
        
        if color is None:
            color = self.get_color()
        
        if x is None:
            x = np.arange(data.shape[2], dtype=np.float32)
        else:
            x =  np.array(x)
        
        if y is None:
            y = np.arange(data.shape[1], dtype=np.float32)
        else:
            y =  np.array(y)
        
        if z is None:
            z = np.arange(data.shape[0], dtype=np.float32)
        else:
            z =  np.array(z)
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, 'capsule', x, y, z, data, level, color, **kwds)
        
        # ColorBar参数
        self.cbargs = None
    
    def contour(self, data, xs=None, ys=None, levels=5, cm='jet', fill=True, **kwds):
        """等值线
        
        data        - 数据，二维元组、列表或数组
        xs/ys       - 点的x/y坐标集，None或与data结构相同的二维元组、列表或数组
        levels      - 分级数量，整数，升序的一维元组、列表或数组
        cm          - 颜色映射表
        fill        - 是否填充颜色，默认填充
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
        
        if isinstance(data, (tuple,list)):
            data = np.array(data)
        assert isinstance(data, np.ndarray) and data.ndim == 2, '期望参数data是二维的元组、列表或数组'
        rows, cols = data.shape
        
        if xs is None:
            xs = np.tile(np.arange(cols), (rows, 1))
        elif isinstance(xs, (tuple,list)):
            xs = np.array(xs)
        assert isinstance(xs, np.ndarray) and xs.shape == (rows, cols), '期望参数xs为None或与data结构相同的二维元组、列表或数组'
        
        if ys is None:
            ys = np.repeat(np.arange(rows), cols).reshape(rows, cols)
        elif isinstance(ys, (tuple,list)):
            ys = np.array(ys)
        assert isinstance(ys, np.ndarray) and ys.shape == (rows, cols), '期望参数ys为None或与data结构相同的二维元组、列表或数组'
        
        cvalues, contours = util.get_contour(data, xs, ys, levels)
        color = self.cm.cmap(cvalues, cm, drop=True)
        cbargs = {'cm':cm, 'drange':cvalues.tolist()}
        
        if fill:
            for i in range(1, len(cvalues)):
                data[(data>=cvalues[i-1])&(data<cvalues[i])] = cvalues[i-1]
            self.hot(data, xs=xs, ys=ys, cm=cm, smooth=False, **kwds)
        else:
            for group, c, d in zip(contours, color, cvalues):
                for item in group:
                    self.plot(item[:,0], item[:,1], color=c)
                    self.text('%0.2f'%d, size=32, pos=(*item[0],0.1))
        
        # ColorBar参数
        self.cbargs = cbargs
    
    def hot(self, data, xs=None, ys=None, cm='jet', drange=None, smooth=True, **kwds):
        """热力图
        
        data        - 数据，二维元组、列表或数组
        xs/ys       - 点的x/y坐标集，None或与data结构相同的二维元组、列表或数组
        cm          - 颜色映射表
        drange      - 颜色映射的数据动态范围，二元组，若为None，则使用数据的动态范围
        smooth      - 是否使用3x3的卷积平滑，默认True
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
        
        if isinstance(data, (tuple,list)):
            data = np.array(data)
        assert isinstance(data, np.ndarray) and data.ndim == 2, '期望参数data是二维numpy数组，或类似结构的元组、列表'
        
        self.set_2d_mode()
        rows, cols = data.shape
        
        if xs is None:
            xs = np.tile(np.arange(cols), (rows, 1))
        elif isinstance(xs, (tuple,list)):
            xs = np.array(xs)
        assert isinstance(xs, np.ndarray) and xs.shape == (rows, cols), '期望参数xs为None或与data结构相同的二维numpy数组，或类似结构的元组、列表'
        
        if ys is None:
            ys = np.repeat(np.arange(rows), cols).reshape(rows, cols)
        elif isinstance(ys, (tuple,list)):
            ys = np.array(ys)
        assert isinstance(ys, np.ndarray) and ys.shape == (rows, cols), '期望参数ys为None或与data结构相同的二维numpy数组，或类似结构的元组、列表'
        
        if drange is None:
            drange = np.nanmin(data), np.nanmax(data)
        else:
            dmin, dmax = drange
        
        kwds.update({'light':0})
        zs = np.zeros((rows, cols))
        c = self.cm.cmap(data, cm, drange=drange)
        texture = np.uint8(c*255)
        cbargs = {'cm':cm, 'drange':drange}
        
        if smooth:
            w = np.ones((3,3))
            w /= np.sum(w)
            r = ndimage.convolve(texture[..., 0], w)
            g = ndimage.convolve(texture[..., 1], w)
            b = ndimage.convolve(texture[..., 2], w)
            texture = np.dstack((r,g,b))
        
        # 添加到部件库
        self.fig.add_widget(self.reg_main, '_mesh', xs, ys, zs, texture, **kwds)
        
        # ColorBar参数
        self.cbargs = cbargs
    
    def colors(self):
        """绘制可用的颜色及其对应的中英文名称"""
        
        vs = np.array([[0, 1],[0, -13],[31, -13],[31, 1]])
        self.surface(vs, color='#F0F0F0', method='Q')
        
        cs = self.cm.color_help()
        for i in range(len(cs)):
            row, col = i//6, i%6
            x, y = 2.2+col*5, -row*0.5
            cen, ccn = cs[i]
            c = self.cm.color2c(cen)
            
            vs = np.array([[x-0.1, y+0.1],[x-0.1, y-0.1],[x+0.1, y-0.1],[x+0.1, y+0.1]])
            self.surface(vs, color=c, method='Q')
            
            vs = np.array([[x-0.1, y+0.1],[x-0.1, y-0.1],[x+0.1, y-0.1],[x+0.1, y+0.1],[x-0.1, y+0.1]])
            self.plot(vs[:,0], vs[:,1], color='black', width=0.5)
            
            self.text(ccn, size=28, pos=(x-0.15,y), align='right-middle')
            self.text('(%s)'%cen, size=28, pos=(x+0.15,y), align='left-middle')
        
        self.axis(False)
        
        # ColorBar参数
        self.cbargs = None
    