# -*- coding: utf-8 -*-

import os
import numpy as np
from PIL import Image
from OpenGL.GL import *


class Texture:
    """纹理对象"""
    
    def __init__(self, tsrc, ttype=GL_TEXTURE_2D, **kwds):
        """构造函数
    
        tsrc            - 图像全路径或者np.array数组
        ttype           - 纹理类型，默认2D纹理
        kwds            - 关键字参数
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
        
        if ttype not in (GL_TEXTURE_1D, GL_TEXTURE_2D, GL_TEXTURE_2D_ARRAY, GL_TEXTURE_3D):
            raise ValueError('不支持的纹理类型')
        
        self.ttype = ttype
        self.tsrc = tsrc
        self.tid = None
        
        self.level = kwds.get('level', 1)
        self.min_filter = kwds.get('min_filter', GL_LINEAR_MIPMAP_NEAREST)
        self.mag_filter = kwds.get('mag_filter', GL_LINEAR)
        self.s_tile = kwds.get('s_tile', GL_REPEAT)
        self.t_tile = kwds.get('t_tile', GL_REPEAT)
        self.r_tile = kwds.get('r_tile', GL_REPEAT)
        self.xflip = kwds.get('xflip', False)
        self.yflip = kwds.get('yflip', False)
    
    def create_texture(self):
        """创建纹理对象"""
        
        if self.ttype == GL_TEXTURE_1D:
            self.tid = self._create_texture_1d()
        elif self.ttype == GL_TEXTURE_2D:
            self.tid = self._create_texture_2d()
        elif self.ttype == GL_TEXTURE_2D_ARRAY:
            self.tid = self._create_texture_2d_array()
        elif self.ttype == GL_TEXTURE_3D:
            self.tid = self._create_texture_3d()
    
    def _create_texture_1d(self):
        """创建1D纹理对象"""
        
        if isinstance(self.tsrc, np.ndarray) and self.tsrc.dtype == np.uint8 and self.tsrc.ndim in (1, 2):
            im = self.tsrc
        else:
            raise ValueError('不支持的纹理资源类型')
        
        im_w = im.shape[0]
        im_mode = GL_LUMINANCE if im.ndim == 1 else (GL_RGB, GL_RGBA)[im.shape[-1]-3]
        
        tid = glGenTextures(1)
        glBindTexture(self.ttype, tid)
        
        if im_w%4 == 0:
            glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
        else:
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        
        for i in range(self.level):
            glTexImage1D(self.ttype, i, GL_RGBA, im_w, 0, im_mode, GL_UNSIGNED_BYTE, im)
        
        glTexParameterf(self.ttype, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameterf(self.ttype, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glTexParameterf(self.ttype, GL_TEXTURE_WRAP_S, self.s_tile)
        
        glGenerateMipmap(self.ttype)
        glBindTexture(self.ttype, 0)
        
        return tid
    
    def _create_texture_2d(self):
        """创建2D纹理对象"""
        
        if isinstance(self.tsrc, str):
            if os.path.isfile(self.tsrc):
                im = np.array(Image.open(self.tsrc))
            else:
                raise ValueError('纹理资源文件不存在：%s'%self.tsrc)
        elif isinstance(self.tsrc, np.ndarray) and self.tsrc.dtype == np.uint8 and self.tsrc.ndim in (2, 3):
            im = self.tsrc
        else:
            raise ValueError('不支持的纹理资源类型')
        
        im_h, im_w = im.shape[:2]
        im_mode = GL_LUMINANCE if im.ndim == 2 else (GL_RGB, GL_RGBA)[im.shape[-1]-3]
        
        if self.xflip:
            im = np.fliplr(im)
        if self.yflip:
            im = np.flipud(im)
        
        tid = glGenTextures(1)
        glBindTexture(self.ttype, tid)
        
        if (im.size/im_h)%4 == 0:
            glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
        else:
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        
        for i in range(self.level):
            glTexImage2D(self.ttype, i, GL_RGBA, im_w, im_h, 0, im_mode, GL_UNSIGNED_BYTE, im)
        
        glTexParameterf(self.ttype, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameterf(self.ttype, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glTexParameterf(self.ttype, GL_TEXTURE_WRAP_S, self.s_tile)
        glTexParameterf(self.ttype, GL_TEXTURE_WRAP_T, self.t_tile)
        
        glGenerateMipmap(self.ttype)
        glBindTexture(self.ttype, 0)
        
        return tid
    
    def _create_texture_2d_array(self):
        """创建2D纹理数组对象"""
        
        if isinstance(self.tsrc, list):
            im = list()
            for path in self.tsrc:
                if os.path.isfile(path):
                    im.append(np.array(Image.open(path)))
                raise ValueError('纹理资源文件不存在：%s'%path)
            
            im = np.stack(im)
        elif isinstance(self.tsrc, np.ndarray) and self.tsrc.dtype == np.uint8 and self.tsrc.ndim in (3, 4):
            im = self.tsrc
        else:
            raise ValueError('不支持的纹理资源类型')
            
        im_layer, im_h, im_w = im.shape[:-1]
        im_mode = GL_LUMINANCE if im.ndim == 3 else (GL_RGB, GL_RGBA)[im.shape[-1]-3]
        
        tid = glGenTextures(1)
        glBindTexture(self.ttype, tid)
        
        if (im.size/(im_layer*im_h))%4 == 0:
            glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
        else:
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        
        for i in range(self.level):
            glTexImage3D(self.ttype, i, GL_RGBA, im_w, im_h, im_layer, 0, im_mode, GL_UNSIGNED_BYTE, im)

        glTexParameterf(self.ttype, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameterf(self.ttype, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glTexParameterf(self.ttype, GL_TEXTURE_WRAP_S, self.s_tile)
        glTexParameterf(self.ttype, GL_TEXTURE_WRAP_T, self.t_tile)
        glTexParameterf(self.ttype, GL_TEXTURE_WRAP_R, self.r_tile)
        
        glGenerateMipmap(self.ttype)
        glBindTexture(self.ttype, 0)
        
        return tid
    
    def _create_texture_3d(self):
        """创建3D纹理对象"""
        
        if isinstance(self.tsrc, list):
            im = list()
            for path in self.tsrc:
                if os.path.isfile(path):
                    im.append(np.array(Image.open(path)))
                raise ValueError('纹理资源文件不存在：%s'%path)
            
            im = np.stack(im)
        elif isinstance(self.tsrc, np.ndarray) and self.tsrc.dtype == np.uint8 and self.tsrc.ndim in (3, 4):
            im = self.tsrc
        else:
            raise ValueError('不支持的纹理资源类型')
            
        im_layer, im_h, im_w = im.shape[:-1]
        im_mode = GL_LUMINANCE if im.ndim == 3 else (GL_RGB, GL_RGBA)[im.shape[-1]-3]
        
        tid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_3D, tid)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glMatrixMode(GL_MODELVIEW)
        
        for i in range(self.level):
            glTexImage3D(GL_TEXTURE_3D, i, GL_RGBA, im_w, im_h, im_layer, 0, im_mode, GL_UNSIGNED_BYTE, im)

        glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, self.min_filter)
        glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, self.s_tile)
        glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, self.t_tile)
        glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, self.r_tile)
        
        glGenerateMipmap(GL_TEXTURE_3D)
        glEnable(GL_TEXTURE_3D)
        glBindTexture(GL_TEXTURE_3D, 0)
        
        return tid

    