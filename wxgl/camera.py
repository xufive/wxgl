# -*- coding: utf-8 -*-


class Camera:
    """相机基类"""
    
    def __init__(self, proj, **kwds):
        """构造函数
        
        proj    - 投影模式
                    'O' - 正射投影（Orthographic）
                    'P' - 透视投影（Perspective）
        """
        
        if proj.upper()[0] == 'O':
            pass
        else:
            kwds.get('fov', 5.0)
        
        self.oecs = kwds.get('oecs', [0.0, 0.0, 0.0])                       # 视点坐标系ECS原点
        self.dist = kwds.get('dist', 5.0)                                   # 相机与ECS原点的距离
        self.azim = 0                                                       # 方位角
        self.elev = 0                                                       # 高度角
        self.cam = [0.0, 0.0, 5.0]                                          # 相机位置
        self.up = [0.0, 1.0, 0.0]                                           # 指向相机上方的单位向量

class OrthographicCamera:
    """正射投影相机类"""
    
    def __init__(self, fov, aspect, near, far):
        """构造函数
        
        fov     - 水平方向视野夹角
        aspect  - 视口宽高比
        near    - 视锥体前面距离相机的距离
        far     - 视锥体后面距离相机的距离
        """
        
        pass
        

class PerspectiveCamera:
    """透视投影相机类"""
    
    def __init__(self, left, right, bottom, top, near, far):
        """构造函数
        
        fov     - 水平方向视野夹角
        aspect  - 视口宽高比
        near    - 视锥体前面距离相机的距离
        far     - 视锥体后面距离相机的距离
        """
        
        pass