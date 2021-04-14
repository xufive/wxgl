# -*- coding: utf-8 -*-
#
# MIT License
# 
# Copyright (c) 2020 天元浪子
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 

"""
WxGL是一个基于pyopengl的三维数据展示库

WxGL以wx为显示后端，以加速渲染为第一追求目标
借助于wxpython，WxGL可以很好的融合matplotlib等其他数据展示技术
"""


from . import wxfigure


fig = wxfigure.Figure()

def figure(*args, **kwds):
    """新建画布
    
    Useage: figure(*args, **kwds)
    ----------------------------------------------------
    size        - 画布分辨率，默认800x600
    kwds        - 关键字参数
                    head        - 定义方向：'x+'|'y+'|'z+'
                    zoom        - 视口缩放因子
                    mode        - 2D/3D模式
                    aim         - 观察焦点
                    dist        - 相机位置与目标点位之间的距离
                    view        - 视景体
                    elevation   - 仰角
                    azimuth     - 方位角
                    interval    - 模型动画帧间隔时间（单位：ms）
                    style       - 配色方案，'black'|'white'|'gray'|'blue'
        """
    
    global fig
    fig = wxfigure.Figure(*args, **kwds)

def show(*args, **kwds):
    """显示画布
    
    Useage: show(rotation=None, **kwds)
    ----------------------------------------------------
    rotation    - 旋转模式
                    None        - 无旋转
                    'h+'        - 水平顺时针旋转（默认方式）
                    'h-'        - 水平逆时针旋转
                    'v+'        - 垂直前翻旋转
                    'v-'        - 垂直后翻旋转
    kwds        - 关键字参数
                    elevation   - 初始仰角，以度（°）为单位，默认值为0
                    azimuth     - 初始方位角以度（°）为单位，默认值为0
                    step        - 帧增量，以度（°）为单位，默认值为5
                    interval    - 帧间隔，以ms为单位，默认值为20
    """
    
    fig.show(*args, **kwds)

def savefig(*args, **kwds):
    """保存画布为文件
    
    Useage: savefig(fn, alpha=False)
    ----------------------------------------------------
    fn          - 文件名
    alpha       - 透明通道开关
    """
    
    fig.savefig(*args, **kwds)

def subplot(*args, **kwds):
    """添加子图
    
    Useage: subplot(pos, padding=(20,20,20,20))
    ----------------------------------------------------
    pos         - 子图在画布上的位置和大小
                    三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                    四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
    padding     - 四元组，上、右、下、左四个方向距离边缘的留白像素
    """
    
    return fig.add_axes(*args, **kwds)

def cmap(*args, **kwds):
    """数值颜色映射
        
    Useage: cmap(data, cm, **kwds)
    ----------------------------------------------------
    data        - 数据
    cm          - 颜色映射表名
    kwds        - 关键字参数
                    invalid     - 无效数据的标识
                    invalid_c   - 无效数据的颜色
                    datamax     - 数据最大值，默认为None
                    datamin     - 数据最小值，默认为None
                    alpha       - 透明度，None表示返回RGB格式
    """
    
    return fig.cmap(*args, **kwds)

def colorbar(*args, **kwds):
    """绘制colorbar
    
    Useage: colorbar(drange, cmap, loc, **kwds)
    ----------------------------------------------------
    drange      - 值域范围，tuple类型
    cmap        - 调色板名称
    loc         - 位置，top|bottom|left|right
    kwds        - 关键字参数
                    length          - ColorBar所在视区的长边长度，默认短边长度为1
                    subject         - 标题
                    subject_size    - 标题字号
                    label_size      - 标注字号
                    label_format    - 标注格式化所用lambda函数
                    tick_line       - 刻度线长度
                    endpoint        - 刻度是否包含值域范围的两个端点值
                    name            - 模型名
                    inside          - 是否更新数据动态范围
                    visible         - 是否显示
    """
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.colorbar(*args, **kwds)

def title(*args, **kwds):
    """绘制标题
    
    Useage: title(text, size=96, color=None, pos=(0,0,0), **kwds)
    ----------------------------------------------------
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
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.title(*args, **kwds)

def text(*args, **kwds):
    """绘制文本
    
    Useage: text(text, size=64, color=None, pos=(0,0,0), **kwds)
    ----------------------------------------------------
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
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.text(*args, **kwds)

def plot(*args, **kwds):
    """绘制点和线
        
    Useage: plot(xs, ys, zs=None, color=None, size=0.0, width=1.0, style='solid', cmap='hsv', caxis='z', **kwds)
    ----------------------------------------------------
    xs/ys/zs    - 顶点的x/y/z坐标集，元组、列表或一维数组类型，长度相等。若zs为None，则自动补为全0的数组
    color       - 全部或每一个顶点的颜色。None表示使用cmap参数映射颜色
    size        - 顶点的大小，整型或浮点型。若为0，则表示不绘制点，只绘制线
    width       - 线宽，0.0~10.0之间的浮点数。若为0，则表示不绘制线，只绘制点
    style       - 线型
                    'solid'     - 实线
                    'dashed'    - 虚线
                    'dotted'    - 点线
                    'dash-dot'  - 虚点线
    cmap        - 颜色映射表，color为None时有效
    caxis       - 用于颜色映射的坐标轴数据，2D模式下自动转为'y'
    kwds        - 关键字参数
                    slide       - 是否作为动画播放的帧
                    name        - 模型名
    """
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.plot(*args, **kwds)

def scatter(*args, **kwds):
    """绘制散点图
        
    Useage: scatter(vs, color=None, size=1.0, cmap='hsv', caxis='z')
    ----------------------------------------------------
    vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
    color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
    size        - 顶点的大小，整型或浮点型
    cmap        - 颜色映射表，color为None时有效。使用vs的z坐标映射颜色
    caxis       - 用于颜色映射的坐标轴数据，2D模式下自动转为'y'
    """
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.scatter(*args, **kwds)

def mesh(*args, **kwds):
    """绘制mesh
        
    Useage: mesh(xs, ys, zs, color=None, mode='FCBC', cmap='hsv', caxis='z', **kwds)
    ----------------------------------------------------
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
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.mesh(*args, **kwds)

def surface(*args, **kwds):
    """绘制surface
    
    Useage: surface(vs, color=None, method='Q', mode='FCBC', texture=None, alpha=True, **kwds)
    ----------------------------------------------------
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
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.surface(*args, **kwds)

def pipe(*args, **kwds):
    """绘制圆管
    
    Useage: pipe(vs, radius, color=None, slices=36, mode='FCBC', cmap='hsv', caxis='z')
    ----------------------------------------------------
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
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.pipe(*args, **kwds)

def sphere(*args, **kwds):
    """绘制球体
    
    Useage: sphere(center, radius, color, slices=90, mode='FLBL')
    ----------------------------------------------------
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
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.sphere(*args, **kwds)

def cube(*args, **kwds):
    """绘制六面体
    
    Useage: cube(center, side, color, mode='FLBL')
    ----------------------------------------------------
    center      - 中心坐标，元组、列表或数组
    side        - 棱长，整型、浮点型，或长度为3的元组、列表数组
    color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
    mode        - 显示模式
                    'FCBC'      - 前后面填充颜色FCBC
                    'FLBL'      - 前后面显示线条FLBL
                    'FCBL'      - 前面填充颜色，后面显示线条FCBL
                    'FLBC'      - 前面显示线条，后面填充颜色FLBC
    """
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.cube(*args, **kwds)

def cylinder(*args, **kwds):
    """绘制圆柱体
    
    Useage: cylinder(v_top, v_bottom, radius, color, slices=60, mode='FCBC')
    ----------------------------------------------------
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
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.cylinder(*args, **kwds)

def cone(*args, **kwds):
    """绘制圆锥体
    
    Useage: cone(center, spire, radius, color, slices=60, mode='FCBC')
    ----------------------------------------------------
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
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.cone(*args, **kwds)

def capsule(*args, **kwds):
    """绘制囊（三维等值面）
    
    Useage: capsule(data, threshold, color, r_x=None, r_y=None, r_z=None, mode='FCBC', **kwds)
    ----------------------------------------------------
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
    """
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.capsule(*args, **kwds)

def flow(*args, **kwds):
    """绘制流体
    
    Useage: flow(ps, us, vs, ws, **kwds)
    ----------------------------------------------------
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
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.flow(*args, **kwds)

def ticks(*args, **kwds):
    """显示网格和刻度
    
    Useage: subplot(**kwds)
    ----------------------------------------------------
    kwds        - 关键字参数
                    segment_min     - 标注最少分段数量
                    segment_max     - 标注最多分段数量
                    label_2D3D      - 标注试用2D或3D文字
                    label_size      - 标注字号
                    xlabel_format   - x轴标注格式化所用lambda函数
                    ylabel_format   - y轴标注格式化所用lambda函数
                    zlabel_format   - z轴标注格式化所用lambda函数
                    
    """
    
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.ticks(*args, **kwds)
