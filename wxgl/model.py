# -*- coding: utf-8 -*-

import re, uuid
import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo

class Model:
    """模型类"""
    
    def __init__(self, gltype, vshader, fshader, visible=True, opacity=True, inside=True, sprite=False):
        """构造函数
        
        gltype          - GL基本图元
        vshader         - 顶点着色器源码
        fshader         - 片元着色器源码
        visible         - 模型可见性
        opacity         - 模型不透明属性
        inside          - 模型显示在视锥体内
        sprite          - 是否开启点精灵
        """
        
        gltypes = (
            GL_POINTS,	        # 绘制一个或多个顶点
            GL_LINES,	        # 绘制线段
            GL_LINE_STRIP,	    # 绘制连续线段
            GL_LINE_LOOP,	    # 绘制闭合的线段
            GL_POLYGON,	        # 绘制多边形
            GL_TRIANGLES,	    # 绘制一个或多个三角形
            GL_TRIANGLE_STRIP,	# 绘制连续三角形
            GL_TRIANGLE_FAN,    # 绘制多个三角形组成的扇形
            GL_QUADS,	        # 绘制一个或多个四边形
            GL_QUAD_STRIP       # 四边形条带
        )
        
        if gltype not in gltypes:
            raise ValueError('不支持的绘制方法')
        
        self.gltype = gltype                            # GL基本图元
        
        self.visible = visible                          # 模型可见性，默认可见
        self.opacity = opacity                          # 模型不透明属性，默认不透明
        self.inside = inside                            # 模型顶点是否影响模型空间，默认True
        self.slide = None                               # 幻灯片函数
        self.depth = None                               # 深度轴均值
        self.islive = False                             # 模型是否有动画函数
        
        self.program = None                             # 着色器程序
        self.cshaders = list()                          # 编译后的着色器
        self.shaders = list()                           # 着色器源码
        self.other = dict()                             # 着色器中其他变量
        self.attribute = dict()                         # attribute变量
        self.uniform = dict()                           # uniform变量
        
        self.vshape = None                              # 顶点数据的shape
        self.indices = None                             # 顶点索引
        self.r_x = None                                 # 顶点坐标x的动态范围
        self.r_y = None                                 # 顶点坐标y的动态范围
        self.r_z = None                                 # 顶点坐标z的动态范围
        
        self.before = list()                            # 绘制前执行的GL命令
        self.after = list()                             # 绘制后执行的GL命令
        
        self.add_shader(vshader, GL_VERTEX_SHADER)
        self.add_shader(fshader, GL_FRAGMENT_SHADER)
        
        if sprite:
            self.before.append((glPushAttrib, (GL_POINT_BIT,)))
            self.before.append((glEnable, (GL_POINT_SPRITE,)))
            self.before.append((glEnable, (GL_PROGRAM_POINT_SIZE,)))
            self.after.append((glPopAttrib, ()))
    
    def add_shader(self, shader_source, shader_type):
        """添加着色器
        
        shader_source   - 着色器源码
        shader_type     - 着色器类型
        """
        
        shader_types = (
            GL_VERTEX_SHADER,           # 顶点着色器
            GL_TESS_CONTROL_SHADER,     # 细分控制着色器
            GL_TESS_EVALUATION_SHADER,  # 细分估值着色器
            GL_GEOMETRY_SHADER,         # 几何着色器
            GL_FRAGMENT_SHADER,         # 片元着色器
            GL_COMPUTE_SHADER           # 计算着色器
        )
        
        if shader_type not in shader_types:
            raise ValueError('不支持的着色器类型')
        
        self.shaders.append((shader_source, shader_type))
    
    def set_slide(self, slide):
        """设置幻灯片函数"""
        
        self.slide = slide
        if hasattr(slide, '__call__'):
            self.islive = True
    
    def set_vertex(self, var_name, data, indices=None):
        """设置顶点
        
        var_name        - 顶点在着色器中的变量名
        data            - 顶点数据
        indices         - 顶点索引数据
        """
        
        data = np.array(data, dtype=np.float32)
        if data.ndim == 3:
            data = data.reshape(-1, data.shape[-1])
        
        self.attribute.update({var_name: {'tag':'vertex', 'data':data, 'un':data.shape[-1], 'usize':data.itemsize}})
        self.depth = data[:, 2].mean() if data.shape[-1] == 3 else 0
        self.vshape = data.shape
        
        if self.inside:
            self.r_x = (data[:,0].min(), data[:,0].max())
            self.r_y = (data[:,1].min(), data[:,1].max())
            if self.vshape[1] == 3:
                self.r_z = (data[:,2].min(), data[:,2].max())
        
        if not indices is None:
            indices = np.array(indices, dtype=np.int32)
            self.indices = {'data':indices, 'n':indices.size}
    
    def set_normal(self, var_name, data):
        """设置顶点法向量
        
        var_name        - 顶点法向量在着色器中的变量名
        data            - 顶点法向量数据
        """
        
        data = np.array(data, dtype=np.float32)
        self.attribute.update({var_name: {'tag':'normal', 'data':data, 'un':data.shape[-1], 'usize':data.itemsize}})
    
    def set_texcoord(self, var_name, data):
        """设置顶点纹理
        
        var_name        - 顶点纹理在着色器中的变量名
        data            - 顶点纹理数据
        """
        
        data = np.array(data, dtype=np.float32)
        self.attribute.update({var_name: {'tag':'texcoord', 'data':data, 'un':data.shape[-1], 'usize':data.itemsize}})
    
    def set_color(self, var_name, data):
        """设置顶点颜色
        
        var_name        - 顶点颜色在着色器中的变量名
        data            - 顶点颜色数据
        """
        
        data = np.array(data, dtype=np.float32)
        self.attribute.update({var_name: {'tag':'color', 'data':data, 'un':data.shape[-1], 'usize':data.itemsize}})
    
    def set_psize(self, var_name, data):
        """设置顶点大小
        
        var_name        - 顶点大小在着色器中的变量名
        data            - 顶点大小数据
        """
        
        self.attribute.update({var_name: {'tag':'psize', 'data':data, 'un':1}})
        
        self.before.append((glPushAttrib, (GL_POINT_BIT,)))
        self.before.append((glEnable, (GL_PROGRAM_POINT_SIZE,)))
        self.after.append((glPopAttrib, ()))
    
    def add_texture(self, var_name, texture_src, texture_type, **kwds):
        """添加纹理
        
        var_name        - 纹理在着色器中的变量名
        texture_src     - 纹理资源（数据或文件名）
        texture_type    - 纹理类型
        kwds            - 关键字参数（不同的纹理类型，关键字参数可能不尽相同）
            level           - 纹理分级数，默认1
            min_filter      - 纹理缩小滤波器
                                - GL_NEAREST
                                - GL_LINEAR
                                - GL_NEAREST_MIPMAP_NEAREST
                                - GL_LINEAR_MIPMAP_NEAREST
                                - GL_NEAREST_MIPMAP_LINEAR
                                - GL_LINEAR_MIPMAP_LINEAR
            mag_filter      - 纹理放大滤波器
                                - GL_NEAREST
                                - GL_LINEAR
            s_tile          - S方向纹理铺贴方式，GL_REPEAT|GL_MIRRORED_REPEAT|GL_CLAMP_TO_EDGE
            t_tile          - T方向纹理铺贴方式，GL_REPEAT|GL_MIRRORED_REPEAT|GL_CLAMP_TO_EDGE
            r_tile          - R方向纹理铺贴方式，GL_REPEAT|GL_MIRRORED_REPEAT|GL_CLAMP_TO_EDGE
            xflip           - 图像左右翻转
            yflip           - 图像上下翻转
        """
        
        texture_types = (
            GL_TEXTURE_1D,
            GL_TEXTURE_2D,
            GL_TEXTURE_3D,
            GL_TEXTURE_CUBE_MAP,
            GL_TEXTURE_RECTANGLE
        )
        
        if texture_type not in texture_types:
            raise ValueError('不支持的纹理类型')
        
        self.uniform.update({var_name: {'tag':'texture', 'type':texture_type, 'src':texture_src, 'kwds':kwds}})
    
    def set_cam_pos(self, var_name):
        """设置相机位置（用于计算镜面反射）
        
        var_name        - 相机位置在着色器中的变量名
        """
        
        self.uniform.update({var_name: {'tag':'campos'}})
    
    def set_mvp_matrix(self, var_name):
        """设置模型、视点、投影三合一矩阵
        
        var_name        - 三合一矩阵在着色器中的变量名
        """
        
        self.uniform.update({var_name: {'tag':'mvpmat'}})
    
    def set_view_matrix(self, var_name):
        """设置视点矩阵
        
        var_name        - 视点矩阵在着色器中的变量名
        """
        
        self.uniform.update({var_name: {'tag':'vmat'}})
    
    def set_proj_matrix(self, var_name):
        """设置投影矩阵
        
        var_name        - 投影矩阵在着色器中的变量名
        """
        
        self.uniform.update({var_name: {'tag':'pmat'}})
    
    def set_model_matrix(self, var_name, mmatrix=None):
        """设置模型矩阵
        
        var_name        - 模型矩阵在着色器中的变量名
        mmatrix         - 模型矩阵或生成模型矩阵的函数，None表示模型无几何变换
        """
        
        if mmatrix is None:
            self.uniform.update({var_name: {'tag':'mmat'}})
        elif hasattr(mmatrix, '__call__'):
            self.uniform.update({var_name: {'tag':'mmat', 'f':mmatrix}})
            self.islive = True
        else:
            self.uniform.update({var_name: {'tag':'mmat', 'v':mmatrix}})
    
    def set_argument(self, var_name, var_value):
        """设置变量
        
        var_name        - 变量在着色器中的变量名
        var_value       - 变量值或生成变量值的函数
        """
        
        self.other.update({var_name:var_value})
    
    def set_line_style(self, width=None, stipple=None):
        """设置线宽和线型
        
        width           - 线宽
        stipple         - 线型，重复因子（整数）和模式（16位二进制）组成的元组
        """
        
        if not width is None or not stipple is None:
            self.before.append((glPushAttrib, (GL_LINE_BIT,)))
            if not width is None:
                self.before.append((glLineWidth,(width,)))
            if not stipple is None:
                self.before.append((glEnable, (GL_LINE_STIPPLE,)))
                self.before.append((glLineStipple, stipple))
            self.after.append((glPopAttrib, ()))
    
    def set_fill_mode(self, mode):
        """设置填充方式
        
        mode            - 填充模式：布尔型，或FCBC|FLBC|FCBL|FLBL
        """
        
        mode = mode.upper()
        if mode in ('FCBC', 'FLBC', 'FCBL', 'FLBL', True, False):
            self.before.append((glPushAttrib, (GL_ALL_ATTRIB_BITS,)))
            if mode == 'FCBC' or mode ==True:
                self.before.append((glPolygonMode,(GL_FRONT_AND_BACK, GL_FILL)))
            elif mode == 'FLBL' or mode == False:
                self.before.append((glPolygonMode,(GL_FRONT_AND_BACK, GL_LINE)))
            elif mode == 'FCBL':
                self.before.append((glPolygonMode,(GL_FRONT, GL_FILL)))
                self.before.append((glPolygonMode,(GL_BACK, GL_LINE)))
            else:
                self.before.append((glPolygonMode,(GL_FRONT, GL_LINE)))
                self.before.append((glPolygonMode,(GL_BACK, GL_FILL)))
            self.after.append((glPopAttrib, ()))
        else:
            raise ValueError('不支持的填充模式：%s'%mode)
    
    def verify(self):
        """验证并完善模型数据"""
        
        if self.gltype is None:
            raise ValueError('未设置GL基本图元')
        
        if self.vshape is None:
            raise ValueError('未设置模型顶点数据')
        
        p0 = re.compile(r'void\s+main\s*\(\s*\)') # void main()
        p1 = re.compile(r'//') # 匹配注释
        p2 = re.compile(r'(in|attribute|uniform)\s+(\S+)\s+(\S+)\s*;') # in|attribute|uniform vec4 position;
        p3 = re.compile(r'layout\s*\(\s*location\s*=\s*(\d+)\s*\)') # layout (location=0)
        pn = re.compile(r'\[(\d+)\]$') # 匹配数组
        
        for src, genre in self.shaders: # 遍历每一个着色器
            for line in src.split('\n'): # 遍历每一行
                if p0.search(line):
                    break
                
                if p1.match(line.strip()):
                    continue
                
                r2 = p2.search(line)
                if r2:
                    qualifier, var_type, var_name = r2.groups()
                    
                    if qualifier in ('in', 'attribute'):
                        if genre == GL_VERTEX_SHADER:
                            qualifier = 'attribute'
                        else:
                            continue
                    
                    rpn = pn.search(var_name)
                    if rpn:
                        ndim = int(rpn.groups()[0]) # 变量数组的长度（若变量是数组的话）
                        var_name = var_name.split('[')[0].strip()
                    else:
                        ndim = None
                    
                    if var_name in self.other:
                        data = self.other[var_name]
                        
                        if not hasattr(data, '__call__'):
                            if var_type == 'float' or var_type[:3] == 'vec':
                                data = np.float32(data)
                            elif var_type == 'double' or var_type[:4] == 'dvec':
                                data = np.float64(data)
                            elif var_type == 'int' or var_type[:4] == 'ivec':
                                data = np.int32(data)
                            elif var_type == 'uint' or var_type[:4] == 'uvec':
                                data = np.uint8(data)
                        
                        if qualifier == 'attribute':
                            if hasattr(data, '__call__'):
                                raise ValueError('in或attribute限定的着色器变量不能赋值为函数')
                            
                            if data.ndim > 2:
                                data = data.reshape(-1, data.shape[-1])
                            elif data.ndim == 1:
                                data = data.reshape(-1, 1)
                            
                            self.attribute.update({var_name: {'tag':'other', 'data':data, 'un':data.shape[-1], 'usize':data.itemsize}})
                        else:
                            if hasattr(data, '__call__'):
                                self.uniform.update({var_name: {'tag':'other', 'f':data}})
                                self.islive = True
                            else:
                                self.uniform.update({var_name: {'tag':'other', 'v':data}})
                            
                            dtype = {
                                'float': '1f',
                                'double': '1d',
                                'int': '1i',
                                'uint': '1ui',
                                'vec2': '2fv',
                                'vec3': '3fv',
                                'vec4': '4fv',
                                'dvec2': '2dv',
                                'dvec3': '3dv',
                                'dvec4': '4dv',
                                'ivec2': '2iv',
                                'ivec3': '3iv',
                                'ivec4': '4iv',
                                'uvec2': '2uiv',
                                'uvec3': '3uiv',
                                'uvec4': '4uiv'
                            }.get(var_type, None)
                        
                            if not dtype:
                                raise ValueError('着色器变量“%s”的数据类型不被支持'%var_name)
                            
                            if ndim is None:
                                if dtype[-1] == 'v':
                                    ndim = 1
                            else:
                                if dtype[-1] != 'v':
                                    dtype = dtype + 'v'
                            
                            self.uniform[var_name].update({'dtype': dtype})
                            self.uniform[var_name].update({'ndim': ndim})
                    
                    if var_name not in self.__getattribute__(qualifier):
                        raise ValueError('着色器变量“%s”未赋值'%var_name)
                    
                    r3 = p3.match(line.strip())
                    if r3:
                        self.__getattribute__(qualifier)[var_name].update({'loc': int(r3.groups()[0])})
    