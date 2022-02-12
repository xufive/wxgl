# -*- coding: utf-8 -*-

import os
import numpy as np
from PIL import Image
from OpenGL.GL import *


def create_texture(src, texture_type=GL_TEXTURE_2D, **kwds):
    """创建纹理对象
    
    src             - 图像全路径或者np.array数组
    texture_type    - 纹理类型，默认2D纹理
    kwds            - 关键字参数
    """
    
    if texture_type == GL_TEXTURE_2D:
        return create_texture_2d(src, **kwds)
    elif texture_type == GL_TEXTURE_3D:
        return create_texture_3d(src, **kwds)
    else:
        pass

def create_texture_2d(src, **kwds):
    """创建2D纹理对象
    
    src             - 图像全路径或者PIL.Image对象或者np.array数组(m,n,3|4)
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
        xflip           - 图像左右翻转
        yflip           - 图像上下翻转
    """ 
    
    for key in kwds:
        if key not in ['level', 'min_filter', 'mag_filter', 's_tile', 't_tile', 'xflip', 'yflip']:
            raise KeyError('不支持的关键字参数：%s'%key)
    
    level = kwds.get('level', 1)
    min_filter = kwds.get('min_filter', GL_LINEAR_MIPMAP_NEAREST)
    mag_filter = kwds.get('mag_filter', GL_LINEAR)
    s_tile = kwds.get('s_tile', GL_CLAMP_TO_EDGE)
    t_tile = kwds.get('t_tile', GL_CLAMP_TO_EDGE)
    xflip = kwds.get('xflip', False)
    yflip = kwds.get('yflip', True)
    
    if isinstance(src, str):
        if os.path.isfile(src):
            im = np.array(Image.open(src))
        else:
            raise ValueError('纹理资源文件不存在：%s'%src)
    elif isinstance(src, np.ndarray) and src.dtype == np.uint8 and src.ndim in (2, 3):
        im = src
    else:
        raise ValueError('不支持的纹理资源类型')
    
    im_h, im_w = im.shape[:2]
    im_mode = GL_LUMINANCE if im.ndim == 2 else (GL_RGB, GL_RGBA)[im.shape[-1]-3]
    
    if xflip:
        im = np.fliplr(im)
    if yflip:
        im = np.flipud(im)
    
    tid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tid)
    
    if (im.size/im_h)%4 == 0:
        glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
    else:
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    
    for i in range(level):
        glTexImage2D(GL_TEXTURE_2D, i, GL_RGBA, im_w, im_h, 0, im_mode, GL_UNSIGNED_BYTE, im)
    
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, min_filter)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, mag_filter)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, s_tile)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, t_tile)
    glGenerateMipmap(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, 0)
    
    return tid

def create_texture_3d(src, **kwds):
    """创建3D纹理对象
    
    src             - 图像全路径列表或者np.array数组(m,n,3|4)
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
    """
    
    for key in kwds:
        if key not in ['level', 'min_filter', 'mag_filter', 's_tile', 't_tile', 'r_tile']:
            raise KeyError('不支持的关键字参数：%s'%key)
    
    level = kwds.get('level', 1)
    min_filter = kwds.get('min_filter', GL_LINEAR_MIPMAP_NEAREST)
    mag_filter = kwds.get('mag_filter', GL_LINEAR)
    s_tile = kwds.get('s_tile', GL_CLAMP_TO_EDGE)
    t_tile = kwds.get('t_tile', GL_CLAMP_TO_EDGE)
    r_tile = kwds.get('r_tile', GL_CLAMP_TO_EDGE)
    
    yflip = kwds.get('yflip', True)
    
    if isinstance(src, list):
        im = list()
        for path in src:
            im.append(np.array(Image.open(path)))
        
        im = np.stack(im)
    elif isinstance(src, np.ndarray) and src.dtype == np.uint8 and src.ndim in (3, 4):
        im = src
    else:
        raise ValueError('不支持的纹理资源类型')
        
    im_layer , im_h, im_w = im.shape[:-1]
    im_mode = GL_LUMINANCE if im.ndim == 3 else (GL_RGB, GL_RGBA)[im.shape[-1]-3]
    
    tid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_3D, tid)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glMatrixMode(GL_MODELVIEW)
    for i in range(level):
        glTexImage3D(GL_TEXTURE_3D, i, GL_RGBA, im_w, im_h, im_layer, 0, im_mode, GL_UNSIGNED_BYTE, im)

    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, min_filter)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, mag_filter)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, s_tile)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, t_tile)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, r_tile)
    
    glGenerateMipmap(GL_TEXTURE_3D)
    glEnable(GL_TEXTURE_3D)
    glBindTexture(GL_TEXTURE_3D, 0)
    
    return tid
    