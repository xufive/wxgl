# -*- coding: utf-8 -*-

import re
import numpy as np
from scipy import ndimage

from . import region
from . import util
from . import light as wxLight


class Axes:
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
        self.fig = self.ff.fig
        
        w, h = self.scene.csize
        margin, padding = 0.02, 0.01
        
        if isinstance(pos, (str, int)) and re.compile(r'^[1-9]{3}$').match(str(pos)): 
            rows, cols, cell = [int(ch) for ch in str(pos)]
            i, j = (cell-1)//cols, (cell-1)%cols
            cw, ch = (1-2*margin)/cols, (1-2*margin)/rows
            self.box = (margin+padding+j*cw, margin+padding+(rows-1-i)*ch, cw-2*padding, ch-2*padding)
        elif isinstance(pos, (list,tuple)) and len(pos) == 4:
            self.box = (pos[0]+padding, pos[1]+padding, pos[2]-2*padding, pos[3]-2*padding)
        else:
            raise ValueError("期望参数pos是三个数字组成的整数或字符串，或者长度为4的元组或列表")
        
        self.reg_main = self.scene.add_region(self.box)     # 主视区
        self.reg_title = None                               # 标题视区
        self.reg_cbr = None                                 # 右侧色条视区
        self.reg_cbb = None                                 # 底部色条视区
        
        self.title_dict = dict()                            # 保存标题信息的字典
        self.cbr_list = list()                              # 保存右侧色条信息的列表
        self.cbb_list = list()                              # 保存底部色条信息的列表
        self.cbr_uk = 1.0                                   # 右侧色条基本单位缩放系数
        self.cbb_uk = 1.5                                   # 底部色条基本单位缩放系数
        self.assembly = list()                              # 生成模型的函数及参数列表
        self.ci = 0                                         # 默认颜色选择指针
        
        self.xn = 'X'                                       # x轴名称
        self.yn = 'Y'                                       # y轴名称
        self.zn = 'Z'                                       # z轴名称
        self.xr = None                                      # x轴范围
        self.yr = None                                      # y轴范围
        self.zr = None                                      # z轴范围
        self.xf = str                                       # x轴标注格式化函数
        self.yf = str                                       # y轴标注格式化函数
        self.zf = str                                       # z轴标注格式化函数
        self.xd = 0                                         # x轴标注密度，整型，值域范围[-2,10], 默认0
        self.yd = 0                                         # y轴标注密度，整型，值域范围[-2,10], 默认0
        self.zd = 0                                         # z轴标注密度，整型，值域范围[-2,10], 默认0
    
    def _layout(self):
        """画布显示前设置主视区、标题视区和色条视区的布局关系"""
        
        # 计算右侧色条总宽度
        if self.cbr_list:
            ur = 0.02 * self.cbr_uk # 垂直色条宽度与Axes宽度之比
            tick = 0.6 * ur # 刻度线长度
            w_label = 2.4 * ur # 刻度文字占用空间宽度
            w_cb = (ur + tick + w_label) * len(self.cbr_list)
            
            for cb in self.cbr_list:
                w_cb += (cb['margin_left'] + cb['margin_right']) * ur
        else:
            w_cb = 0
        
        # 计算底部色条总高度
        if self.cbb_list:
            margin_top_list = [cb['margin_top'] for cb in self.cbb_list if not cb['margin_top'] is None]
            margin_bottom_list = [cb['margin_bottom'] for cb in self.cbb_list if not cb['margin_bottom'] is None]
            margin_top = margin_top_list[-1] if any(margin_top_list) else 0.5
            margin_bottom = margin_bottom_list[-1] if any(margin_bottom_list) else 0.5
            
            ub = 0.02 * self.cbb_uk # 水平高度与Axes高度之比
            tick = 0.6 * ub # 刻度线长度
            h_subject = 1.4 * ub if any([cb['subject'] for cb in self.cbb_list]) else 0 # 标题高度
            h_label = 0.7 * ub # 刻度文字高度
            h_cb = ub + tick + h_subject + h_label + margin_top*ub + margin_bottom*ub
        else:
            h_cb = 0
        
        # 计算标题高度
        if self.title_dict:
            h_t = self.title_dict['height'] * (1 + self.title_dict['margin_top'] + self.title_dict['margin_bottom'])
        else:
            h_t = 0
        
        # 重置reg_main视区大小
        x0, y0, w_main, h_main = self.reg_main.box
        y0 += h_cb * self.box[3]
        w_main -= w_cb * self.box[2]
        h_main -= (h_t + h_cb) * self.box[3]
        self.reg_main.update_size((x0, y0, w_main, h_main))
        
        # 标题
        if self.title_dict:
            box = (x0, y0+h_main, self.box[2],  h_t*self.box[3])
            self.reg_title = self.scene.add_region(box, fixed=True, proj='ortho', zoom=1.0) # 创建标题视区
            
            w = self.reg_title.size[0]/self.reg_title.size[1]
            top = 1 - 2 * self.title_dict['height'] * self.title_dict['margin_top'] / h_t
            bottom = -1 + 2 * self.title_dict['height'] * self.title_dict['margin_bottom'] / h_t
            left = -w + 2 * self.title_dict['height'] * self.title_dict['margin_left'] / h_t
            right = w - 2 * self.title_dict['height'] * self.title_dict['margin_right'] / h_t
            box = [[left,top],[left,bottom],[right,top],[right,bottom]]
            color = self.title_dict['color']
            size = self.title_dict['size']
            
            kwds = {
                'family':       self.title_dict['family'], 
                'weight':       self.title_dict['weight'], 
                'align':        'center', 
                'valign':       'fill', 
                'inside':       False,
                'light':        wxLight.BaseLight()
            }
            
            self.add_widget(self.reg_title, 'text3d', self.title_dict['text'], box, color=color, size=size, **kwds)
            
            if self.title_dict['border']:
                box = [[-w,1],[w,1],[-w,-1],[w,-1]]
                self.add_widget(self.reg_title, 'line', box, method='isolate', inside=False)
        
        # 右侧色条
        if self.cbr_list:
            box = (x0+w_main, y0, w_cb*self.box[2], h_main)
            self.reg_cbr = self.scene.add_region(box, fixed=True, proj='ortho', zoom=1.0) # 创建右侧色条视区
            
            h = self.reg_cbr.size[1]/self.reg_cbr.size[0]
            start = -1
            for cb in self.cbr_list:
                w = ur + tick + w_label + cb['margin_left']*ur + cb['margin_right']*ur
                section = 2*w/w_cb
                left = start + section * cb['margin_left']*ur / w
                right = left + section * ur / w
                top = h - 2*cb['margin_top']*ur/w_cb - 2*1.2*ur/w_cb if cb['subject'] else h - 2*cb['margin_top']*ur/w_cb
                bottom = -h + 2*cb['margin_bottom']*ur/w_cb
                start += section
                
                box = np.array([[left,top],[left,bottom],[right,top],[right,bottom]], dtype=np.float32)
                kwds = {
                    'subject':          cb['subject'],
                    'tick_format':      cb['tick_format'],
                    'density':          cb['density'],
                    'endpoint':         cb['endpoint']
                }
                
                self.add_widget(self.reg_cbr, 'colorbar', cb['cm'], cb['drange'], box, mode='V', **kwds)
        
        # 底部色带
        if self.cbb_list:
            box = (x0, self.box[1], w_main,  h_cb*self.box[3])
            self.reg_cbb = self.scene.add_region(box, fixed=True, proj='ortho', zoom=1.0) # 创建底部色条视区
            
            w = self.reg_cbb.size[0]/self.reg_cbb.size[1]
            section = 2*w/len(self.cbb_list)
            top = 1 - 2*margin_top*ub/h_cb - 2*h_subject/h_cb
            bottom = top - 2*ub/h_cb
            for i, cb in enumerate(self.cbb_list):
                start = -w + i*section
                left = start + 2*cb['margin_left']*ub/h_cb
                right = -w + (i+1)*section - 2*cb['margin_right']*ub/h_cb
            
                box = np.array([[left,top],[left,bottom],[right,top],[right,bottom]], dtype=np.float32)
                kwds = {
                    'subject':          cb['subject'],
                    'tick_format':      cb['tick_format'],
                    'density':          cb['density'],
                    'endpoint':         cb['endpoint']
                }
                
                self.add_widget(self.reg_cbb, 'colorbar', cb['cm'], cb['drange'], box, mode='H', **kwds)
    
    def get_color(self):
        """返回下一个可用的默认颜色"""
        
        color = util.CM.default_colors[self.ci]
        self.ci = (self.ci+1)%len(util.CM.default_colors)
        
        return color
    
    def add_widget(self, reg, func, *args, **kwds):
        """添加生成模型的函数及参数"""
        
        self.assembly.append([reg, func, list(args), kwds])
    
    def title(self, text, size=40, color=None, **kwds):
        """Axes顶部区水平居中的标题
        
        text        - 文本字符串：支持LaTex语法
        size        - 字号：整型，默认40
        color       - 文本颜色：支持预定义颜色、十六进制颜色，以及值域范围[0,1]的浮点型元组、列表或numpy数组颜色，默认使用场景的前景颜色
        kwds        - 关键字参数
                        family          - 字体，None表示当前默认的字体
                        weight          - 字体的浓淡：'normal'-正常，'light'-轻，'bold'-重（默认）
                        border          - 显示标题边框，默认True
                        margin_top      - 标题上方留空与标题文字高度之比，默认0.75
                        margin_bottom   - 标题下方留空与标题文字高度之比，默认0.25
                        margin_left     - 标题左侧留空与标题文字高度之比，默认0.0
                        margin_right    - 标题右侧留空与标题文字高度之比，默认0.0
        """
        
        for key in kwds:
            if key not in ['family', 'weight', 'border', 'margin_top', 'margin_bottom', 'margin_left', 'margin_right']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        family = kwds.get('family', None)
        weight = kwds.get('weight', 'bold')
        border = kwds.get('border', True)
        margin_top = kwds.get('margin_top', 0.75)
        margin_bottom = kwds.get('margin_bottom', 0.25)
        margin_left = kwds.get('margin_left', 0.0)
        margin_right = kwds.get('margin_right', 0.0)
        
        height = size/1000 # 标题文字高度与Axes高度之比
        size = int(round(pow(size/64, 0.5) * 64))
        color = util.color2c(color)
        
        self.title_dict.update({
            'text':             text,
            'color':            color,
            'size':             size,
            'family':           family,
            'weight':           weight,
            'border':           border,
            'height':           height,
            'margin_top':       margin_top,
            'margin_bottom':    margin_bottom,
            'margin_left':      margin_left,
            'margin_right':     margin_right
        })
    
    def colorbar(self, cm, drange, loc='right', **kwds):
        """colorbar
        
        cm          - 调色板名称
        drange      - 数据的动态范围：元组、列表或numpy数组
        loc         - 位置
                        right           - 右侧
                        bottom          - 底部
        kwds        - 关键字参数
                        subject         - 标题
                        tick_format     - 刻度标注格式化函数，默认str
                        density         - 刻度密度，最少和最多刻度线组成的元组，默认(3,6)
                        endpoint        - 刻度是否包含值域范围的两个端点值
                        scale           - 色条宽度、文字大小等缩放比例，默认None
                        margin_left     - 色条左侧留空，默认0.5
                        margin_right    - 色条右侧留空，默认0.5
                        margin_top      - 色条上方留空，默认0.5
                        margin_bottom   - 色条下方留空，默认0.5
        """
        
        for key in kwds:
            if key not in ['subject', 'tick_format', 'density', 'endpoint', 'scale', 'margin_left', 'margin_right', 'margin_top', 'margin_bottom']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        drange = np.array(drange)
        drange = (np.nanmin(drange), np.nanmax(drange))
        
        if not loc in ('right', 'bottom'):
            raise ValueError('不支持的选项：%s'%loc)
        
        subject = kwds.get('subject', None)
        tick_format = kwds.get('tick_format', str)
        density = kwds.get('density', (3,6))
        endpoint = kwds.get('endpoint', False)
        scale = kwds.get('scale', None)
        margin_left = kwds.get('margin_left', 0.5)
        margin_right = kwds.get('margin_right', 0.5)
        margin_top = kwds.get('margin_top', 0.5 if loc == 'right' else None)
        margin_bottom = kwds.get('margin_bottom', 0.5 if loc == 'right' else None)
        
        args = {
            'cm':               cm,
            'drange':           drange,
            'subject':          subject,
            'tick_format':      tick_format,
            'density':          density,
            'endpoint':         endpoint,
            'margin_left':      margin_left,
            'margin_right':     margin_right,
            'margin_top':       margin_top,
            'margin_bottom':    margin_bottom
        }
        
        if loc == 'right':
            self.cbr_list.append(args)
            if scale:
                self.cbr_uk = scale
        else:
            self.cbb_list.append(args)
            if scale:
                self.cbb_uk = scale * 1.5
    
    def text(self, text, pos, color=None, size=32, family=None, weight='normal', loc='left_bottom', **kwds):
        """文本
        
        text        - 文本字符串
        pos         - 文本位置：元组、列表或numpy数组，shape=(2|3,)
        color       - 文本颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色，默认使用场景的前景颜色
        size        - 字号：整型，默认32
        family      - 字体：默认None，表示使用当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        loc         - pos对应文本区域的位置，默认left_bottom
                        'left-top'      - 左上
                        'left-middle'   - 左中
                        'left-bottom'   - 左下
                        'center-top'    - 上中
                        'center-middle' - 中
                        'center-bottom' - 下中
                        'right-top'     - 右上
                        'right-middle'  - 右中
                        'right-bottom'  - 右下
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        slide           - 幻灯片函数，默认None
        """
        
        self.add_widget(self.reg_main, 'text', text, pos, 
            color       = util.color2c(color), 
            size        = size, 
            family      = family, 
            weight      = weight, 
            loc         = loc, 
            **kwds
        )
        
    def text3d(self, text, box, color=None, size=64, family=None, weight='normal', align='fill', valign='fill', **kwds):
        """3d文本
        
        text        - 文本字符串
        box         - 文本显式区域：左上、左下、右上、右下4个点组成的元组、列表或numpy数组，shape=(4,2|3)
        color       - 文本颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色，默认使用场景的前景颜色
        size        - 字号：整型，默认64。此参数仅影响文本显示质量，不改变文本大小
        family      - 字体：默认None，表示使用当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        align       - 文本宽度方向对齐方式
                        'fill'          - 填充
                        'left'          - 左对齐
                        'right'         - 右对齐
                        'center'        - 居中对齐
        valign      - 文本高度方向对齐方式
                        'fill'          - 填充
                        'top'           - 上对齐
                        'bottom'        - 下对齐
                        'middle'        - 居中对齐
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        inside          - 模型顶点是否影响模型空间，默认True
                        slide           - 幻灯片函数，默认None
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
                        light           - 光照情景模式，默认太阳光照情景模式
        """
        
        self.add_widget(self.reg_main, 'text3d', text, box, 
            color       = util.color2c(color), 
            size        = size, 
            family      = family, 
            weight      = weight, 
            align       = align, 
            valign      = valign, 
            **kwds
        )
    
    def line(self, vs, color=None, cm=None, width=None, style='solid', method='strip', **kwds):
        """线段
        
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或数据：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色；若为数据，其长度等于顶点数量
        cm          - 颜色映射表：默认None。若该参数有效，color参数被视为与顶点一一对应的数据
        width       - 线宽，0.0~10.0之间，None使用默认设置
        style       - 线型, 默认实线
                        'solid'         - 实线 
                        'dashed'        - 虚线
                        'dotted'        - 点线
                        'dash-dot'      - 虚点线
        method      - 绘制方法
                        'isolate'       - 独立线段
                        'strip'         - 连续线段
                        'loop'          - 闭合线段
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认True（不透明）
                        slide           - 幻灯片函数，默认None
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
                        ambient         - 环境光，默认(1.0,1.0,1.0)
        """
        
        if cm is None:
            if color is None:
                color = self.get_color()
            color = util.color2c(color, outsize=len(vs))
        else:
            if not color is None and isinstance(color, (tuple, list, np.ndarray)) and len(color) == len(vs):
                color = util.cmap(np.array(color), cm)
            else:
                raise ValueError('当参数cm有效时，期望color是和顶点数量匹配的元组、列表或numpy数组')
        
        stipple = {
            'solid':    (1, 0xFFFF),
            'dashed':   (1, 0xFFF0),
            'dotted':   (1, 0xF0F0),
            'dash-dot': (1, 0xFF18)
        }.get(style, 'solid')
            
        self.add_widget(self.reg_main, 'line', vs, color, 
            method      = method, 
            width       = width, 
            stipple     = stipple, 
            **kwds
        )
    
    def point(self, vs, color=None, cm=None, size=1.0, **kwds):
        """散点
        
        vs          - 顶点集，元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或数据：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色；若为数据，其长度等于顶点数量
        cm          - 颜色映射表：默认None。若该参数有效，color参数被视为与顶点一一对应的数据
        size        - 点或每个点的大小：数值，或数值型的元组、列表、numpy数组
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        slide           - 幻灯片函数，默认None
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认True（不透明）
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列
        """
        
        if cm is None:
            if color is None:
                color = self.get_color()
            color = util.color2c(color, outsize=len(vs))
        else:
            if not color is None and isinstance(color, (tuple, list, np.ndarray)) and len(color) == len(vs):
                color = util.cmap(np.array(color), cm)
            else:
                raise ValueError('当参数cm有效时，期望color是和顶点数量匹配的元组、列表或numpy数组')
        
        self.add_widget(self.reg_main, 'point', vs, color, size=size, **kwds)
    
    def surface(self, vs, color=None, cm=None, texture=None, texcoord=None, method='isolate', indices=None, closed=False, **kwds):
        """由三角面描述的曲面
        
        vs          - 顶点集，元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或数据：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色；若为数据，其长度等于顶点数量
        cm          - 颜色映射表：默认None。若该参数有效，color参数被视为与mesh网格匹配的数据
        texture     - 纹理：wxgl.Texture对象
        texcoord    - 顶点的纹理坐标集，元组、列表或numpy数组，shape=(n,2)
        method      - 绘制方法
                        'isolate'       - 独立三角面
                        'strip'         - 带状三角面
                        'fan'           - 扇面
        indices     - 顶点索引集，默认None
        closed      - 带状三角面或扇面两端闭合：布尔型
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认True（不透明）
                        fill            - 填充，默认None（使用当前设置）
                        slide           - 幻灯片函数，默认None
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列
                        light           - 光照情景模式，默认太阳光照情景模式
        """
        
        if cm is None:
            if color is None:
                if texture is None:
                    color = util.color2c(self.get_color())
                elif texcoord is None:
                    raise ValueError('当参数texture有效时，期望texcoord有效')
            else:
                color = util.color2c(color, outsize=len(vs))
        else:
            if not color is None and isinstance(color, (tuple, list, np.ndarray)):
                color = np.array(color)
                if color.shape == (len(vs),):
                    color = util.cmap(color, cm)
                else:
                    raise ValueError('当参数cm有效时，期望color是和顶点数量匹配的元组、列表或numpy数组')
            else:
                raise ValueError('当参数cm有效时，期望color是和顶点数量匹配的元组、列表或numpy数组')
        
        self.add_widget(self.reg_main, 'surface', vs, 
            color       = color, 
            texture     = texture, 
            texcoord    = texcoord, 
            method      = method, 
            indices     = indices, 
            closed      = closed,
            **kwds
        )
    
    def mesh(self, xs, ys, zs, color=None, cm=None, texture=None, utr=(0,1), vtr=(0,1), uclosed=False, vclosed=False, xoy=False, **kwds):
        """网格面
        
        xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)
        color       - 颜色或数据：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色；若为数据，shape=(m,n)
        cm          - 颜色映射表：默认None。若该参数有效，color参数被视为与mesh网格匹配的数据
        texture     - 纹理：wxgl.Texture对象
        utr         - u方向纹理坐标范围
        vtr         - v方向纹理坐标范围
        uclosed     - u方向网格两端闭合：布尔型
        vclosed     - v方向网格两端闭合：布尔型
        xoy         - 网格在xoy平面：布尔型
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认不透明
                        fill            - 填充，默认None（使用当前设置）
                        slide           - 幻灯片函数，默认None
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列
                        light           - 光照情景模式，默认太阳光照情景模式
        """
        
        xs, ys, zs = np.array(xs), np.array(ys), np.array(zs)
        
        if cm is None:
            if color is None:
                if texture is None:
                    color = util.color2c(self.get_color())
            else:
                color = util.color2c(color, outsize=xs.shape)
        else:
            if not color is None and isinstance(color, (tuple, list, np.ndarray)):
                color = np.array(color)
                if color.shape == xs.shape:
                    color = util.cmap(color, cm)
                else:
                    raise ValueError('当参数cm有效时，期望color是和顶点数量匹配的元组、列表或numpy数组')
            else:
                raise ValueError('当参数cm有效时，期望color是和顶点数量匹配的元组、列表或numpy数组')
        
        self.add_widget(self.reg_main, 'mesh', xs, ys, zs, 
            color       = color, 
            texture     = texture,
            utr         = utr,
            vtr         = vtr,
            uclosed     = uclosed,
            vclosed     = vclosed,
            xoy         = xoy,
            **kwds
        )
    
    def cylinder(self, c1, c2, r, color=None, texture=None, arc=(0,360), cell=5, **kwds):
        """圆柱
        
        c1          - 圆柱端面圆心：元组、列表或numpy数组
        c2          - 圆柱端面圆心：元组、列表或numpy数组
        r           - 圆柱半径：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组
        texture     - 纹理：wxgl.Texture对象
        arc         - 弧度角范围：默认0°~360°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认不透明
                        fill            - 填充，默认None（使用当前设置）
                        slide           - 幻灯片函数，默认None
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列
                        light           - 光照情景模式，默认太阳光照情景模式
        """
        
        if color is None and texture is None:
            color = self.get_color()
        color = util.color2c(color)
        
        self.add_widget(self.reg_main, 'cylinder', c1, c2, r, color=color, texture=texture, arc=arc, cell=cell, **kwds)

    def torus(self, center, r1, r2, vec=(0,1,0), color=None, texture=None, u=(0,360), v=(0,360), cell=5, **kwds):
        """球环
        
        center      - 球环中心坐标：元组、列表或numpy数组
        r1          - 球半径：浮点型
        r2          - 环半径：浮点型
        vec         - 环面法向量
        color       - 颜色：浮点型元组、列表或numpy数组
        texture     - 纹理：wxgl.Texture对象
        u           - u方向范围：默认0°~360°
        v           - v方向范围：默认-90°~90°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            fill            - 填充，默认None（使用当前设置）
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        if color is None and texture is None:
            color = self.get_color()
        color = util.color2c(color)
        
        self.add_widget(self.reg_main, 'torus', center, r1, r2, vec=vec, color=color, texture=texture, u=u, v=v, cell=cell, **kwds)
    
    def uvsphere(self, center, r, u=(0,360), v=(-90,90), color=None, texture=None, cell=5, **kwds):
        """使用经纬度网格生成球
        
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        u           - 经度范围：默认0°~360°
        v           - 纬度范围：默认-90°~90°
        color       - 颜色：浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理：wxgl.Texture对象
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认不透明
                        fill            - 填充，默认None（使用当前设置）
                        slide           - 幻灯片函数，默认None
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列
                        light           - 光照情景模式，默认太阳光照情景模式
        """
        
        if color is None and texture is None:
            color = self.get_color()
        color = util.color2c(color)
        
        self.add_widget(self.reg_main, 'uvsphere', center, r, u=u, v=v, color=color, texture=texture, cell=cell, **kwds)
    
    def isosphere(self, center, r, color=None, iterations=5, **kwds):
        """通过对正八面体的迭代细分生成球
        
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组，值域范围[0,1]
        iterations  - 迭代次数：整型
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认不透明
                        fill            - 填充，默认None（使用当前设置）
                        slide           - 幻灯片函数，默认None
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列
                        light           - 光照情景模式，默认太阳光照情景模式
        """
        
        if color is None:
            color = self.get_color()
        color = util.color2c(color)
        
        self.add_widget(self.reg_main, 'isosphere', center, r, color=color, iterations=iterations, **kwds)

    def circle(self, center, r, vec=(0,1,0), color=None, arc=(0,360), cell=5, **kwds):
        """圆
        
        center      - 锥底圆心：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        vec         - 圆面法向量
        color       - 颜色：浮点型元组、列表或numpy数组
        arc         - 弧度角范围：默认0°~360°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            fill            - 填充，默认None（使用当前设置）
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        if color is None:
            color = self.get_color()
        color = util.color2c(color)
        
        self.add_widget(self.reg_main, 'circle', center, r, vec=vec, color=color, arc=arc, cell=cell, **kwds)
    
    def cone(self, spire, center, r, color=None, arc=(0,360), cell=5, **kwds):
        """圆、锥、扇
        
        spire       - 锥尖：元组、列表或numpy数组
        center      - 锥底圆心：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组，值域范围[0,1]
        arc         - 弧度角范围：默认0°~360°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认不透明
                        fill            - 填充，默认None（使用当前设置）
                        slide           - 幻灯片函数，默认None
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列
                        light           - 光照情景模式，默认太阳光照情景模式
        """
        
        if color is None:
            color = self.get_color()
        color = util.color2c(color)
        
        self.add_widget(self.reg_main, 'cone', spire, center, r, color=color, arc=arc, cell=cell, **kwds)
    
    def cube(self, center, side, vec=(0,1,0), color=None, **kwds):
        """绘制六面体
        
        center      - 中心坐标，元组、列表或numpy数组
        side        - 棱长：数值或长度为3的元组、列表、numpy数组
        vec         - 六面体上表面法向量
        color       - 颜色：浮点型元组、列表或numpy数组
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认不透明
                        fill            - 填充，默认None（使用当前设置）
                        slide           - 幻灯片函数，默认None
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列
                        light           - 光照情景模式，默认太阳光照情景模式
        """
        
        if color is None:
            color = self.get_color()
        color = util.color2c(color)
        
        self.add_widget(self.reg_main, 'cube', center, side, vec=vec, color=color, **kwds)
    
    def isosurface(self, data, level, color=None, x=None, y=None, z=None, **kwds):
        """三维等值面
        
        data        - 数据集：三维numpy数组，第0轴对应y轴，第1轴对应z轴，第2轴对应x轴
        level       - 阈值：浮点型。data数据集中小于level的数据将被忽略
        color       - 颜色：浮点型元组、列表或numpy数组，值域范围[0,1]
        x/y/z       - 数据集对应的点的x/y/z轴的动态范围
        kwds        - 关键字参数
                        name            - 模型名
                        visible         - 是否可见，默认True
                        slide           - 幻灯片函数，默认None
                        inside          - 模型顶点是否影响模型空间，默认True
                        opacity         - 模型不透明属性，默认不透明
                        transform       - 由旋转、平移和缩放组成的模型几何变换序列
                        fill            - 填充，默认True
                        ambient         - 环境亮度，开启灯光时默认(0.5, 0.5, 0.5)，关闭灯光时默认(1.0, 1.0, 1.0)
                        light           - 平行光源的方向，默认(-0.5, -0.1, -0.5)，None表示关闭灯光
                        light_color     - 平行光源的颜色，默认(1.0, 1.0, 1.0)
                        shininess       - 高光系数，值域范围[0,1]，默认0.0（无镜面反射）
        """
        
        if color is None:
            color = self.get_color()
        color = util.color2c(color)
        
        self.add_widget(self.reg_main, 'isosurface', data, level, color, x=x, y=y, z=z, **kwds)
    
    def model(self, m):
        
        self.add_widget(self.reg_main, 'add_model', m)
    
    def xlabel(self, xlabel):
        """设置x轴名称"""
        
        self.xn = xlabel
    
    def ylabel(self, ylabel):
        """设置y轴名称"""
        
        self.yn = ylabel
    
    def zlabel(self, zlabel):
        """设置z轴名称"""
        
        self.zn = zlabel
    
    def xrange(self, xrange):
        """设置x轴范围"""
        
        self.xr = xrange
    
    def yrange(self, yrange):
        """设置y轴范围"""
        
        self.yr = yrange
    
    def zrange(self, zrange):
        """设置z轴范围"""
        
        self.zr = zrange
    
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
    
    