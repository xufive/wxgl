#!/usr/bin/env python3

import numpy as np
np.seterr(invalid='ignore')

from . color import ColorManager
from . text import FontManager

CM = ColorManager()
FM = FontManager()

def format_color(color, repeat=None):
    """检查颜色参数，将字符串、元组、列表等类型的颜色转为浮点型的numpy数组

    color       - 预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组
    repeat      - 若color为单个颜色，repeat表示重复次数或重复行列数
    """

    return CM.format_color(color, repeat=repeat)

def colormap(data, cm, drange=None, alpha=None, invalid=np.nan, invalid_c=(0,0,0,0)):
    """数值映射到颜色
 
    data        - 数据
    cm          - 调色板
    drange      - 数据动态范围，None表示使用data的动态范围
    alpha       - 透明度，None表示不改变当前透明度
    invalid     - 无效数据的标识
    invalid_c   - 无效数据的颜色
    """

    return CM.colormap(data, cm, drange=drange, alpha=alpha, invalid=invalid, invalid_c=invalid_c)

def get_cmap_colors(cm):
    """返回调色板的颜色列表"""

    return CM.get_cmap_colors(cm)

def text2img(text, size, color, bg=None, family=None, weight='normal'):
    """文本转图像，返回图像数据和size元组
    
    text        - 文本字符串
    size        - 文字大小，整型
    color       - 文本颜色，numpy数组，值域范围[0,1]
    bg          - 背景色，None表示背景透明
    family      - （系统支持的）字体
    weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
    """

    return FM.text2img(text, size, color, bg=bg, family=family, weight=weight)

def y2v(v):
    """返回y轴正方向到向量v的旋转矩阵"""
 
    # *** 右手坐标系旋转矩阵 ***
    # r_x = np.array([[1, 0, 0], [0, np.cos(), np.sin()], [0, -np.sin(), np.cos()]])
    # r_y = np.array([[np.cos(), 0, -np.sin()], [0, 1, 0], [np.sin(), 0, np.cos()]])
    # r_z = np.array([[np.cos(), np.sin(), 0], [-np.sin(), np.cos, 0], [0, 0, 1]])
 
    h =  np.linalg.norm(v)
    a_z = -np.arccos(v[1]/h)
 
    if v[0] == 0:
        if v[2] == 0:
            a_y = 0
        elif v[2] > 0:
            a_y = -np.pi/2
        else:
            a_y = np.pi/2
    else:
        a_y = np.arctan(-v[2]/v[0]) + (np.pi if v[0] < 0 else 0)
 
    r_y_0 = np.array([[np.cos(-a_y), 0, -np.sin(-a_y)], [0, 1, 0], [np.sin(-a_y), 0, np.cos(-a_y)]])
    r_z = np.array([[np.cos(a_z), np.sin(a_z), 0], [-np.sin(a_z), np.cos(a_z), 0], [0, 0, 1]])
    r_y = np.array([[np.cos(a_y), 0, -np.sin(a_y)], [0, 1, 0], [np.sin(a_y), 0, np.cos(a_y)]])
 
    return np.dot(r_y_0, np.dot(r_z, r_y))

def rotate(axis_angle):
    """返回旋转矩阵
 
    axis_angle  - 轴角，由旋转向量和旋转角度组成的元组、列表或numpy数组。旋转方向使用右手定则
    """
 
    v, a = np.array(axis_angle[:3]), np.radians(-axis_angle[3]), 
    v = v/np.linalg.norm(v)
    x, y, z = v
 
    # 轴角转旋转矩阵
    m = np.array([
		[np.cos(a)+x*x*(1-np.cos(a)), -z*np.sin(a)+x*y*(1-np.cos(a)), y*np.sin(a)+x*z*(1-np.cos(a))],
		[z*np.sin(a)+x*y*(1-np.cos(a)), np.cos(a)+y*y*(1-np.cos(a)), -x*np.sin(a)+y*z*(1-np.cos(a))],
		[-y*np.sin(a)+x*z*(1-np.cos(a)), x*np.sin(a)+y*z*(1-np.cos(a)), np.cos(a)+z*z*(1-np.cos(a))]
    ])
 
    m = np.hstack((m, np.array([[0.0], [0.0], [0.0]])))
    m = np.vstack((m, np.array([0.0, 0.0, 0.0, 1.0])))
 
    return np.float32(m)
 
def translate(shift):
    """返回平移矩阵
 
    shift       - 由xyz轴偏移量组成的元组、列表或numpy数组
    """
 
    v = np.array(shift).reshape(3,1)
    m = np.eye(4)
    m[3] += np.sum((m[:3] * v), axis=0)
 
    return np.float32(m)
 
def scale(k):
    """返回缩放矩阵
 
    k           - 缩放系数
    """
 
    v = np.array([k, k, k]).reshape(3,1)
    m = np.eye(4)
    m[:3] *= v
 
    return np.float32(m)

def model_matrix(*args):
    """返回模型矩阵
    
    args        - 旋转（4元组）、平移（3元组）、缩放（数值型）参数
    """
 
    m = np.eye(4)
    for item in args:
        if isinstance(item, (int, float)):
            m = np.dot(m, scale(item))
        elif len(item) == 3:
            m = np.dot(m, translate(item))
        else:
            m = np.dot(m, rotate(item))
 
    return np.float32(m)
 
def view_matrix(cam, up, oecs):
    """返回视点矩阵
 
    cam         - 相机位置
    up          - 指向相机上方的单位向量
    oecs        - 视点坐标系ECS原点
    """
 
    camX, camY, camZ = cam
    oecsX, oecsY, oecsZ = oecs
    upX, upY, upZ = up
 
    f = np.array([oecsX-camX, oecsY-camY, oecsZ-camZ], dtype=np.float64)
    f /= np.linalg.norm(f)
    s = np.array([f[1]*upZ - f[2]*upY, f[2]*upX - f[0]*upZ, f[0]*upY - f[1]*upX], dtype=np.float64)
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
 
    m = np.array([
        [s[0], u[0], -f[0], 0],
        [s[1], u[1], -f[1], 0],
        [s[2], u[2], -f[2], 0],
        [- s[0]*camX - s[1]*camY - s[2]*camZ, 
        - u[0]*camX - u[1]*camY - u[2]*camZ, 
        f[0]*camX + f[1]*camY + f[2]*camZ, 1]
    ], dtype=np.float32)
 
    return m
 
def proj_matrix(fovy, aspect, near, far):
    """返回投影矩阵
 
    fovy        - 相机水平视野角度
    aspect      - 画布宽高比
    near        - 相机与视椎体前端面的距离
    far         - 相机与视椎体后端面的距离
    """
 
    right = np.tan(np.radians(fovy/2)) * near
    left = -right
    top = right/aspect
    bottom = left/aspect
    rw, rh, rd = 1/(right-left), 1/(top-bottom), 1/(far-near)
 
    m = np.array([
        [2 * near * rw, 0, 0, 0],
        [0, 2 * near * rh, 0, 0],
        [(right+left) * rw, (top+bottom) * rh, -(far+near) * rd, -1],
        [0, 0, -2 * near * far * rd, 0]
    ], dtype=np.float32)
 
    return m

def get_normal(gltype, vs, indices=None):
    """返回法线集"""
 
    if gltype not in (4, 5, 6, 7, 8):
        raise KeyError('%s不支持法线计算'%(str(gltype)))
 
    if not indices is None and gltype != 4 and gltype != 7:
        raise KeyError('%s不支持indices参数'%(str(gltype)))
 
    n = vs.shape[0]
    if indices is None:
        if gltype == 6:
            a = np.zeros(n-2, dtype=np.int32)
            b = np.arange(1, n-1, dtype=np.int32)
            c = np.arange(2, n, dtype=np.int32)
            idx = np.stack((a, b, c), axis=1).ravel()
        elif gltype == 5:
            a = np.repeat(np.arange(0, n-1, 2, dtype=np.int32), 2)[1:n-1]
            b = np.repeat(np.arange(1, n-1, 2, dtype=np.int32), 2)[:n-2]
            c = np.arange(2, n, dtype=np.int32)
            idx = np.stack((a, b, c), axis=1).ravel()
        elif gltype == 8:
            a = np.arange(0, n-2, 2, dtype=np.int32)
            b = np.arange(1, n-2, 2, dtype=np.int32)
            c = np.arange(3, n, 2, dtype=np.int32)
            d = np.arange(2, n, 2, dtype=np.int32)
            idx = np.stack((a, b, c, d), axis=1).ravel()
        else:
            idx = np.arange(n, dtype=np.int32)
    else:
        idx = np.array(indices, dtype=np.int32)
 
    primitive = vs[idx]
    if gltype == 7 or gltype == 8:
        a = primitive[::4]
        b = primitive[1::4]
        c = primitive[2::4]
        d = primitive[3::4]
        normal = np.repeat(np.cross(c-a, b-d), 4, axis=0)
    else:
        a = primitive[::3]
        b = primitive[1::3]
        c = primitive[2::3]
        normal = np.repeat(np.cross(b-a, a-c), 3, axis=0)
 
    if indices is None and (gltype == 4 or gltype == 7):
        return normal
 
    result = np.zeros((n,3), dtype=np.float32)
    idx_arg = np.argsort(idx)
    rise = np.where(np.diff(idx[idx_arg])==1)[0]+1
    rise = np.hstack((0,rise,len(idx)))
 
    for i in range(n):
        result[i] = np.sum(normal[idx_arg[rise[i]:rise[i+1]]], axis=0)
    return result

