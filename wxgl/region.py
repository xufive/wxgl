# -*- coding: utf-8 -*-

import os
import wx
import numpy as np
from scipy.spatial.transform import Rotation as sstr
from PIL import Image
import uuid
from OpenGL.GL import *
from OpenGL.arrays import vbo


class WxGLRegion:
    """GL视区类"""
    
    def __init__(self, scene, box, fixed, proj):
        """构造函数
        
        scene       - 所属场景对象
        box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
        fixed       - 布尔型，是否锁定旋转缩放
        proj        - 字符串，投影模式
        """
        
        self.scene = scene                                      # 父级场景对象
        self.box = box                                          # 视区四元组
        self.fixed = fixed                                      # 是否锁定旋转缩放
        self.proj = proj                                        # 投影模式
        self.zoom = 1.0 if proj=='cone' else 1.0                # 视口缩放因子，仅当fixed有效时有效
        
        self.fm = self.scene.fm                                 # 字体管理对象
        self.cm = self.scene.cm                                 # 颜色管理对象
        self.models = dict()                                    # 模型指令集
        self.buffers = dict()                                   # 缓冲区字典
        
        self.r_x = [1e10, -1e10]                                # 数据在x轴上的动态范围
        self.r_y = [1e10, -1e10]                                # 数据在y轴上的动态范围
        self.r_z = [1e10, -1e10]                                # 数据在z轴上的动态范围
        self.scale = 1.0                                        # 模型缩放比例
        self.translate = np.array([0,0,0], dtype=np.float)      # 模型位移量
    
    def _create_vbo(self, vertices):
        """创建顶点缓冲区对象"""
        
        buff = vbo.VBO(vertices)
        id = uuid.uuid1().hex
        self.buffers.update({id: buff})
        
        return id
        
    def _create_ebo(self, indices):
        """创建索引缓冲区对象"""
        
        buff = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
        id = uuid.uuid1().hex
        self.buffers.update({id: buff})
        
        return id
        
    def _create_pbo(self, pixels):
        """创建像素缓冲区对象"""
        
        buff = vbo.VBO(pixels, target=GL_PIXEL_UNPACK_BUFFER)
        id = uuid.uuid1().hex
        self.buffers.update({id: buff})
        
        return id
    
    def _create_texture(self, img):
        """创建纹理对象
        
        img         - 纹理图片文件名或图像数据（UByte）
        """
        
        if isinstance(img, str):
            assert os.path.exists(img), '%s指向的纹理图片文件不存在'%img
            im = Image.open(img)
        elif isinstance(img, np.ndarray) and img.dtype is np.dtype('uint8'):
            im = Image.fromarray(img)
        else:
            raise ValueError('参数img既不是纹理图片文件，也不是以numpy数组表示的图像数据')
        
        ix, iy, image = im.size[0], im.size[1], im.tobytes('raw', im.mode, 0, -1)
        mode = GL_RGBA if im.mode=='RGBA' else GL_RGB
        
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, mode, ix, iy, 0, mode, GL_UNSIGNED_BYTE, image)
        
        return texture
    
    def _get_tick_label(self, v_min, v_max, ks=(1, 2, 2.5, 3, 4, 5), s_min=4, s_max=8, endpoint=True):
        """返回合适的Colorbar标注值
        
        v_min       - 数据最小值
        v_max       - 数据最大值
        ks          - 分段选项
        s_min       - 分段数最小值
        s_max       - 分段数最大值
        endpoint    - 是否包含v_min和v_max
        """
        
        r = v_max - v_min
        tmp = np.array([[abs(float(('%E'%(r/i)).split('E')[0])-k) for i in range(s_min,s_max+1)] for k in ks])
        i, j = divmod(tmp.argmin(), tmp.shape[1])
        step, steps = ks[i], j+s_min
        step *= pow(10, int(('%E'%(r/steps)).split('E')[1]))
        
        result = list()
        v = int(v_min/step)*step
        while v <= v_max:
            if v >= v_min:
                result.append(round(v, 6))
            v += step
        
        if endpoint:
            if result[0] > v_min:
                result.insert(0, v_min)
            if result[-1] < v_max:
                result.append(v_max)
            
            if result[1]-result[0] < (result[2]-result[1])*0.25:
                result.remove(result[1])
            if result[-1]-result[-2] < (result[-2]-result[-3])*0.25:
                result.remove(result[-2])
        
        return result
    
    def set_data_range(self, r_x=None, r_y=None, r_z=None):
        """设置坐标轴范围
        
        r_x         - 二元组，x坐标轴范围
        r_y         - 二元组，y坐标轴范围
        r_z         - 二元组，z坐标轴范围
        """
        
        if r_x and r_x[0] < self.r_x[0]:
            self.r_x[0] = r_x[0]
        if r_x and r_x[1] > self.r_x[1]:
            self.r_x[1] = r_x[1]
        
        if r_y and r_y[0] < self.r_y[0]:
            self.r_y[0] = r_y[0]
        if r_y and r_y[1] > self.r_y[1]:
            self.r_y[1] = r_y[1]
        
        if r_z and r_z[0] < self.r_z[0]:
            self.r_z[0] = r_z[0]
        if r_z and r_z[1] > self.r_z[1]:
            self.r_z[1] = r_z[1]
    
    def _add_model(self, name, visible, genre, vars, **kwds):
        """增加模型"""
        
        if name not in self.models:
            self.models.update({name:{'display':visible, 'component':list()}})
        
        self.models[name]['component'].append({
            'genre': genre,
            'vars': vars
        })
        
        if 'light' in kwds and kwds['light']:
            self.models[name]['component'][-1].update({'light':kwds['light']})
        if 'fill' in kwds and not kwds['fill']:
            self.models[name]['component'][-1].update({'fill':False})
        if 'order' in kwds and kwds['order']:
            self.models[name]['component'][-1].update({'order':kwds['order']})
            self.models[name]['component'][-1].update({'rotate':kwds['rotate']})
            self.models[name]['component'][-1].update({'translate':kwds['translate']})
            self.scene.start_sys_timer()
        
        dist_max = max(self.r_x[1]-self.r_x[0], self.r_y[1]-self.r_y[0], self.r_z[1]-self.r_z[0])
        if dist_max > 0:
            self.scale = 2/dist_max
        self.translate = (-sum(self.r_x)/2, -sum(self.r_y)/2, -sum(self.r_z)/2)
        
        self.refresh()
    
    def _surface(self, vs, texture, texcoord, method, **kwds):
        """绘制面
        
        vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
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
                        'F'         - 扇形
                        'P'         - 多边形
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        assert method in ('Q','T','F','P'), '期望参数method是以下选项至一："Q"、"T"、"F"、"P"'
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'fill', 'light', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        fill = kwds.get('fill', True)
        light = kwds.get('light', 3)
        regulate = kwds.get('regulate', None)
        rotate = kwds.get('rotate', None)
        translate = kwds.get('translate', None)
        order = kwds.get('order', None)
        
        if not isinstance(texcoord, np.ndarray):
            texcoord = np.array(texcoord, dtype=np.float64)
        
        if method == 'F':
            vs = np.array(list(zip(np.tile(vs[0], (vs.shape[0]-2,1)), vs[1:-1], vs[2:]))).reshape(-1,3)
            texcoord = np.stack((np.tile(texcoord[0], (texcoord.shape[0]-2,1)), texcoord[1:-1], texcoord[2:]), axis=1).reshape(-1,2)
            method = 'T'
        
        if regulate:
            vs = self.transform(vs, *regulate)
        
        if inside:
            r_x = (np.nanmin(vs[:,0]),np.nanmax(vs[:,0]))
            r_y = (np.nanmin(vs[:,1]),np.nanmax(vs[:,1]))
            r_z = (np.nanmin(vs[:,2]),np.nanmax(vs[:,2]))
            self.set_data_range(r_x, r_y, r_z)
        
        if method == 'Q':
            normal = np.cross(vs[1::4]-vs[::4], vs[3::4]-vs[::4])
            normal = np.tile(normal, (1,4)).reshape(-1,3)
            normal = self.normalize2d(normal)
        elif method == 'T':
            normal = np.cross(vs[1::3]-vs[::3], vs[2::3]-vs[::3])
            normal = np.tile(normal, (1,3)).reshape(-1,3)
            normal = self.normalize2d(normal)
        else:
            normal = np.cross(vs[0]-vs[2:], vs[1:-1]-vs[2:])
            normal = np.vstack((normal[:1], normal[:1], normal))
            normal = self.normalize2d(normal)
        
        vertices = np.hstack((texcoord, normal, vs)).astype(np.float32)
        vid = self._create_vbo(vertices)
        
        indices = np.array(list(range(vs.shape[0])), dtype=np.int32)
        eid = self._create_ebo(indices)
        
        v_type = GL_T2F_N3F_V3F
        gl_type = {'Q':GL_QUADS, 'T':GL_TRIANGLES, 'P':GL_POLYGON}[method]
        texture = self._create_texture(texture)
        kwds = {'light':light, 'fill':fill, 'rotate':rotate, 'translate':translate, 'order':order}
        
        self._add_model(name, visible, 'surface', [vid, eid, v_type, gl_type, texture], **kwds)
    
    def _mesh(self, xs, ys, zs, texture, **kwds):
        """绘制网格
        
        xs          - 顶点集的x坐标集，numpy.ndarray类型，shape=(rows,cols)
        ys          - 顶点集的y坐标集，numpy.ndarray类型，shape=(rows,cols)
        zs          - 顶点集的z坐标集，numpy.ndarray类型，shape=(rows,cols)
        texture     - 纹理图片文件或numpy数组形式的图像数据
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'fill', 'light', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        fill = kwds.get('fill', True)
        light = kwds.get('light', 3)
        regulate = kwds.get('regulate', None)
        rotate = kwds.get('rotate', None)
        translate = kwds.get('translate', None)
        order = kwds.get('order', None)
        
        rows, cols = zs.shape
        vs = np.dstack((xs,ys,zs))
        
        if regulate:
            vs = self.transform(vs.reshape(-1,3), *regulate)
            vs = vs.reshape(rows,cols,3)
            
            if inside:
                r_x = (np.nanmin(vs[:,0]),np.nanmax(vs[:,0]))
                r_y = (np.nanmin(vs[:,1]),np.nanmax(vs[:,1]))
                r_z = (np.nanmin(vs[:,2]),np.nanmax(vs[:,2]))
                self.set_data_range(r_x, r_y, r_z)
        elif inside:
            self.set_data_range((np.nanmin(xs),np.nanmax(xs)), (np.nanmin(ys),np.nanmax(ys)), (np.nanmin(zs),np.nanmax(zs)))
        
        lat, lon = np.mgrid[1:0:complex(0,rows), 0:1:complex(0,cols)]
        texcoord = np.dstack((lon, lat)).reshape(-1,2)
        texture = self._create_texture(texture)
        
        normal = np.cross(vs[1:,:-1]-vs[:-1,:-1], vs[:-1,1:]-vs[:-1,:-1])
        normal = np.hstack((normal, normal[:,-1:]))
        normal = np.vstack((normal, normal[-1:]))
        normal = self.normalize2d(normal.reshape(-1,3))
            
        vertices = np.hstack((texcoord, normal, vs.reshape(-1,3))).astype(np.float32)
        vid = self._create_vbo(vertices)
        
        idx = np.arange(rows*cols).reshape(rows,cols)
        idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[1:,1:], idx[:-1, 1:]
        indices = np.dstack((idx_a, idx_b, idx_c, idx_d)).ravel()
        eid = self._create_ebo(indices)
        
        v_type = GL_T2F_N3F_V3F
        gl_type = GL_QUADS
        kwds = {'light':light, 'fill':fill, 'rotate':rotate, 'translate':translate, 'order':order}
        
        self._add_model(name, visible, 'mesh', [vid, eid, v_type, gl_type, texture], **kwds)
    
    def normalize2d(self, vs):
        """二维数组正则化（基于L2范数）
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)
        """
        
        k = np.linalg.norm(vs, axis=1)
        vs = vs.T/k
        
        return vs.T
    
    def transform(self, vs, *args):
        """对顶点集实施几何变换
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)
        args        - 可变参数，参数类型为列表或元组
                      若参数长度为2，声明旋转变换，首元素（浮点型）为旋转角度（逆时针为正，右手定则），尾元素（列表或元组）为旋转向量
                      若参数长度为3，声明位移变换，3个元素（浮点型）分别对应xyz轴方向的位移量
        """
        
        for item in args:
            if len(item) == 2: # 旋转
                vec = np.array(item[1])
                rotvec = np.radians(item[0])*vec/np.linalg.norm(vec)
                r = sstr.from_rotvec(rotvec)
                vs = r.apply(vs)
            elif len(item) == 3: # 位移
                vs = vs + np.array(item)
        
        return vs
    
    def rotate_merge(self, av1, av2):
        """将两个轴角旋转合并为一个
        
        av1         - 元组，首元素（浮点型）为旋转角度（逆时针为正，右手定则），尾元素（列表或元组）为旋转向量
        av2         - 元组，首元素（浮点型）为旋转角度（逆时针为正，右手定则），尾元素（列表或元组）为旋转向量
        """
        
        a1, v1 = av1
        a2, v2 = av2
        v1, v2 = np.array(v1), np.array(v2)
        
        r1 = sstr.from_rotvec(np.radians(a1)*v1/np.linalg.norm(v1))
        r2 = sstr.from_rotvec(np.radians(a2)*v2/np.linalg.norm(v2))
        
        m = np.dot(r1.as_matrix(), r2.as_matrix())
        r = sstr.from_matrix(m)
        vec = r.as_rotvec()
        phi = np.degrees(np.linalg.norm(vec))
        
        return phi, vec

    def z2v(self, v):
        """返回z轴正方向到向量v的空间旋转器"""
        
        h =  np.linalg.norm(v)
        a_y = np.arccos(v[2]/h)
        
        if v[0] == 0:
            a_z = np.pi/2 if v[1] > 0 else -np.pi/2
        else:
            a_z = np.arctan(v[1]/v[0]) + (np.pi if v[0] < 0 else 0)
        
        return sstr.from_euler('xyz', [0, a_y, a_z], degrees=False)
    
    def refresh(self):
        """更新视区显示"""
        
        wx.CallAfter(self.scene.update_grid)
        wx.CallAfter(self.scene.Refresh, False)
    
    def show_model(self, name):
        """显示模型
        
        name        - 模型名
        """
        
        if name in self.models:
            self.models[name]['display'] = True
    
    def hide_model(self, name):
        """隐藏模型
        
        name        - 模型名
        """
        
        if name in self.models:
            self.models[name]['display'] = False
    
    def text(self, text, pos, size=32, color=None, family=None, weight='normal', align=None, **kwds):
        """绘制2D文字
        
        text        - 文本字符串
        pos         - 文本位置，元组、列表或numpy数组
        size        - 文字大小，整型
        color       - 文本颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
        family      - （系统支持的）字体，None表示当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        align       - 对齐方式
                        None            - 横排文字，（默认）
                        'VL'            - 竖排文字，自下而上
                        'VR'            - 竖排文字，自上而下
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
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
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        regulate = kwds.get('regulate', None)
        rotate = kwds.get('rotate', None)
        translate = kwds.get('translate', None)
        order = kwds.get('order', None)
        
        if isinstance(pos, (tuple, list)) and len(pos) == 3:
            pos = np.array(pos, dtype=np.float64)
        if not isinstance(pos, np.ndarray) or pos.shape != (3,):
            raise ValueError('期望参数pos是一个长度为3的元组、列表或numpy数组')
        
        if color is None:
            color = np.array(self.scene.style[1])
        else:
            color = self.cm.color2c(color)
        
        if regulate:
            pos = self.transform(pos.reshape(1,-1), *regulate)[0]
        
        if inside:
            self.set_data_range((pos[0],pos[0]), (pos[1],pos[1]), (pos[2],pos[2]))
        
        font_file = self.fm.get_font_file(family=family, weight=weight)
        pixels = self.fm.get_text_pixels(text, size, font_file)
        
        if align == 'VL':
            pixels = np.fliplr(pixels).T
        elif align == 'VR':
            pixels = np.flipud(pixels).T
        
        rows, cols = pixels.shape
        color = np.tile(color*255, (rows*cols, 1)).astype(np.uint8)
        pixels = pixels.reshape(-1, 1)
        pixels = np.hstack((color, pixels)).reshape(rows, cols, 4)
        pixels = pixels[::-1].ravel()
        pid = self._create_pbo(pixels)
        
        self._add_model(name,  visible, 'text', [pid, rows, cols, pos])
    
    def text3d(self, text, box, size=32, color=None, family=None, weight='normal', align=None, k=8, **kwds):
        """绘制3D文字
        
        text        - 文本字符串
        box         - 文本显式区域的左上、左下、右下、右上4个点的坐标，浮点型元组、列表或numpy数组
        size        - 文字大小，整型
        color       - 文本颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
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
        k           - 文本大小的调节因子，取值范围[1,15]，默认8
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        for key in kwds:
            if key not in ['name', 'inside', 'visible', 'light', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        light = kwds.get('light', 0)
        regulate = kwds.get('regulate', None)
        rotate = kwds.get('rotate', None)
        translate = kwds.get('translate', None)
        order = kwds.get('order', None)
        
        if isinstance(box, (tuple, list)) and len(box) == 4:
            box = np.array(box, dtype=np.float64)
        if not isinstance(box, np.ndarray) or box.shape != (4,3):
            raise ValueError('期望参数vs是4个点的坐标组成的元组、列表或numpy数组')
        
        if color is None:
            color = np.array(self.scene.style[1])
        else:
            color = self.cm.color2c(color)
        
        texture = self.fm.text2img(text, size, color, family, weight)
        texcoord =  np.array([[0,1],[0,0],[1,0],[1,1]])
        
        w, h = k*size*(texture.shape[1]/texture.shape[0])/2000, k*size/2000
        vhl, vhr = box[1]-box[0], box[2]-box[3]
        vwt, vwb = box[3]-box[0], box[2]-box[1]
        vhli, vhri = h*(vhl)/np.linalg.norm(vhl), h*(vhr)/np.linalg.norm(vhr)
        vwti, vwbi = w*(vwt)/np.linalg.norm(vwt), w*(vwb)/np.linalg.norm(vwb)
        
        if align == 'left-top':
            box[3] = box[0] + vwti
            box[2] = box[1] + vwbi
            box[1] = box[0] + vhli
            box[2] = box[3] + vhri
        elif align == 'left-bottom':
            box[3] = box[0] + vwti
            box[2] = box[1] + vwbi
            box[0] = box[1] - vhli
            box[3] = box[2] - vhri
        elif align == 'left-middle':
            box[3] = box[0] + vwti
            box[2] = box[1] + vwbi
            box[0] = box[0] - (vhli-vhl)/2
            box[3] = box[3] - (vhri-vhr)/2
            box[1] = box[0] + vhli
            box[2] = box[3] + vhri
        elif align == 'right-top':
            box[0] = box[3] - vwti
            box[1] = box[2] - vwbi
            box[1] = box[0] + vhli
            box[2] = box[3] + vhri
        elif align == 'right-bottom':
            box[0] = box[3] - vwti
            box[1] = box[2] - vwbi
            box[0] = box[1] - vhli
            box[3] = box[2] - vhri
        elif align == 'right-middle':
            box[0] = box[3] - vwti
            box[1] = box[2] - vwbi
            box[0] = box[0] - (vhli-vhl)/2
            box[3] = box[3] - (vhri-vhr)/2
            box[1] = box[0] + vhli
            box[2] = box[3] + vhri
        elif align == 'center-top':
            box[0] = box[0] - (vwti-vwt)/2
            box[1] = box[1] - (vwbi-vwb)/2
            box[3] = box[0] + vwti
            box[2] = box[1] + vwbi
            box[1] = box[0] + vhli
            box[2] = box[3] + vhri
        elif align == 'center-bottom':
            box[0] = box[0] - (vwti-vwt)/2
            box[1] = box[1] - (vwbi-vwb)/2
            box[3] = box[0] + vwti
            box[2] = box[1] + vwbi
            box[0] = box[1] - vhli
            box[3] = box[2] - vhri
        elif align == 'center-middle':
            box[0] = box[0] - (vwti-vwt)/2
            box[1] = box[1] - (vwbi-vwb)/2
            box[3] = box[0] + vwti
            box[2] = box[1] + vwbi
            box[0] = box[0] - (vhli-vhl)/2
            box[3] = box[3] - (vhri-vhr)/2
            box[1] = box[0] + vhli
            box[2] = box[3] + vhri
        
        if regulate:
            box = self.transform(box, *regulate)
        
        if inside:
            r_x = (np.nanmin(box[:,0]),np.nanmax(box[:,0]))
            r_y = (np.nanmin(box[:,1]),np.nanmax(box[:,1]))
            r_z = (np.nanmin(box[:,2]),np.nanmax(box[:,2]))
            self.set_data_range(r_x, r_y, r_z)
        
        self._surface(box, texture, texcoord, 'Q', **kwds)
        
    def point(self, vs, color, size=None, **kwds):
        """绘制点
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)
        color       - 顶点或顶点集颜色，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        size        - 点的大小，整数，None表示使用当前设置
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
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
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        regulate = kwds.get('regulate', None)
        rotate = kwds.get('rotate', None)
        translate = kwds.get('translate', None)
        order = kwds.get('order', None)
        
        if regulate:
            vs = self.transform(vs, *regulate)
        
        if inside:
            r_x = (np.nanmin(vs[:,0]),np.nanmax(vs[:,0]))
            r_y = (np.nanmin(vs[:,1]),np.nanmax(vs[:,1]))
            r_z = (np.nanmin(vs[:,2]),np.nanmax(vs[:,2]))
            self.set_data_range(r_x, r_y, r_z)
        
        c = self.cm.color2c(color)
        if c.ndim == 1:
            c = np.tile(c, (vs.shape[0],1))
        
        if c.shape[-1] == 4:
            c = c[:, :-1]
        
        vid = self._create_vbo(np.hstack((c,vs)).astype(np.float32))
        eid = self._create_ebo(np.array(list(range(vs.shape[0])), dtype=np.int32))
        
        v_type = GL_C3F_V3F
        gl_type = GL_POINTS
        kwds = {'rotate':rotate, 'translate':translate, 'order':order}
        
        self._add_model(name, visible, 'point', [vid, eid, v_type, gl_type, size], **kwds)
        
    def line(self, vs, color, method='SINGLE', width=None, stipple=None, **kwds):
        """绘制线段
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)
        color       - 顶点或顶点集颜色，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        method      - 绘制方法
                        'MULTI'     - 线段
                        'SINGLE'    - 连续线段
                        'LOOP'      - 闭合线段
        width       - 线宽，0.0~10.0之间，None表示使用当前设置
        stipple     - 线型，整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None表示使用当前设置
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
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
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        regulate = kwds.get('regulate', None)
        rotate = kwds.get('rotate', None)
        translate = kwds.get('translate', None)
        order = kwds.get('order', None)
        
        if regulate:
            vs = self.transform(vs, *regulate)
        
        if inside:
            r_x = (np.nanmin(vs[:,0]),np.nanmax(vs[:,0]))
            r_y = (np.nanmin(vs[:,1]),np.nanmax(vs[:,1]))
            r_z = (np.nanmin(vs[:,2]),np.nanmax(vs[:,2]))
            self.set_data_range(r_x, r_y, r_z)
        
        c = self.cm.color2c(color)
        if c.ndim == 1:
            c = np.tile(c, (vs.shape[0],1))
        
        if c.shape[-1] == 4:
            c = c[:, :-1]
        
        vid = self._create_vbo(np.hstack((c,vs)).astype(np.float32))
        eid = self._create_ebo(np.array(list(range(vs.shape[0])), dtype=np.int32))
        
        v_type = GL_C3F_V3F
        gl_type = {'MULTI':GL_LINES, 'SINGLE':GL_LINE_STRIP, 'LOOP':GL_LINE_LOOP}[method]
        kwds = {'rotate':rotate, 'translate':translate, 'order':order}
        
        self._add_model(name, visible, 'line', [vid, eid, v_type, gl_type, width, stipple], **kwds)
    
    def quad(self, vs, color=None, texture=None, texcoord=None, **kwds):
        """绘制一个或多个四角面（每个四角面的四个顶点通常在一个平面上）
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)，n为4的整数倍。四角面的四个顶点按逆时针顺序排列
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据。纹理图片左上、左下、右下和右上对应纹理坐标(0,1)、(0,0)、(1,0)和(1,1)
        texcoord    - 顶点的纹理坐标集，元组、列表或numpy数组，shape=(n,2)
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        assert isinstance(vs, np.ndarray) and vs.ndim == 2 and vs.shape[-1] == 3, '期望参数vs是n个顶点坐标组成的numpy数组，n为4的整数倍'
        
        if not color is None:
            c = np.tile(self.cm.color2c(color), (2,2,1))
            texture = np.uint8(c*255)
            texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        elif texture is None or texcoord is None:
            raise ValueError('参数color为None时，参数texcoord和texture必须同时有效')
        
        self._surface(vs, texture, texcoord, 'Q', **kwds)
    
    def triangle(self, vs, color=None, texture=None, texcoord=None, **kwds):
        """绘制一个或多个三角面
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)，n为3的整数倍。三角面的三个顶点按逆时针顺序排列
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据。纹理图片左上、左下、右下和右上对应纹理坐标(0,1)、(0,0)、(1,0)和(1,1)
        texcoord    - 顶点的纹理坐标集，元组、列表或numpy数组，shape=(n,2)
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        if not color is None:
            c = np.tile(self.cm.color2c(color), (2,2,1))
            texture = np.uint8(c*255)
            texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        elif texture is None or texcoord is None:
            raise ValueError('参数color为None时，参数texcoord和texture必须同时有效')
        
        self._surface(vs, texture, texcoord, 'T', **kwds)
    
    def fan(self, vs, color=None, texture=None, texcoord=None, **kwds):
        """绘制扇面
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)，首元素为中心点，其余元素为圆弧上顺序排列的点
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据。纹理图片左上、左下、右下和右上对应纹理坐标(0,1)、(0,0)、(1,0)和(1,1)
        texcoord    - 顶点的纹理坐标集，元组、列表或numpy数组，shape=(n,2)
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        if not color is None:
            c = np.tile(self.cm.color2c(color), (2,2,1))
            texture = np.uint8(c*255)
            texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        elif texture is None or texcoord is None:
            raise ValueError('参数color为None时，参数texcoord和texture必须同时有效')
        
        self._surface(vs, texture, texcoord, 'F', **kwds)
    
    def polygon(self, vs, color, **kwds):
        """绘制多边形
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)，多边形顺序列出的顶点
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        c = np.tile(self.cm.color2c(color), (2,2,1))
        texture = np.uint8(c*255)
        texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        
        self._surface(vs, texture, texcoord, 'P', **kwds)
    
    def surface(self, vs, color=None, texture=None, texcoord=None, method='Q', **kwds):
        """绘制表面
        
        vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
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
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        if method == 'P':
            assert not color is None, '绘制多边形必须要指定颜色'
        
        if not color is None:
            c = np.tile(self.cm.color2c(color), (2,2,1))
            texture = np.uint8(c*255)
            texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        elif texture is None or texcoord is None:
            raise ValueError('参数color为None时，参数texcoord和texture必须同时有效')
        
        self._surface(vs, texture, texcoord, method, **kwds)
    
    def mesh(self, xs, ys, zs, color=None, texture=None, **kwds):
        """绘制网格
        
        xs          - 顶点集的x坐标集，numpy.ndarray类型，shape=(rows,cols)
        ys          - 顶点集的y坐标集，numpy.ndarray类型，shape=(rows,cols)
        zs          - 顶点集的z坐标集，numpy.ndarray类型，shape=(rows,cols)
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据，color为None时有效
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        if not color is None:
            color = np.tile(self.cm.color2c(color), (2,2,1))
            texture = np.uint8(color*255)
        elif texture is None:
            raise ValueError('参数color和texture不能同时为None')
        
        self._mesh(xs, ys, zs, texture, **kwds)
    
    def sphere(self, center, radius, color=None, texture=None, slices=90, **kwds):
        """绘制球体
        
        center      - 球心坐标，元组、列表或numpy数组
        radius      - 半径，浮点型
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理图片文件或numpy数组形式的图像数据，color为None时有效
        slices      - 分片数，整型
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        if not color is None:
            color = np.tile(self.cm.color2c(color), (2,2,1))
            texture = np.uint8(color*255)
        elif texture is None:
            raise ValueError('参数color和texture不能同时为None')
        
        lats, lons = np.mgrid[np.pi/2:-np.pi/2:complex(0,slices), 0:2*np.pi:complex(0,2*slices)]
        xs = radius * np.cos(lats)*np.cos(lons) + center[0]
        ys = radius * np.cos(lats)*np.sin(lons) + center[1]
        zs = radius * np.sin(lats) + center[2]
        
        self._mesh(xs, ys, zs, texture, **kwds)
    
    def cone(self, center, spire, radius, color, slices=90, **kwds):
        """绘制圆锥体
        
        center      - 锥底圆心坐标，元组、列表或numpy数组
        spire       - 锥尖坐标，元组、列表或numpy数组
        radius      - 锥底半径，浮点型
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        slices      - 分片数，整型
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        if not isinstance(center, np.ndarray):
            center = np.array(center)
        
        if not isinstance(spire, np.ndarray):
            spire = np.array(spire)
        
        theta = np.linspace(0, 2*np.pi, slices+1)
        xs = radius * np.cos(theta)
        ys = radius * np.sin(theta)
        zs = np.zeros_like(theta)
        vs = np.stack((xs,ys,zs), axis=1)
        
        vh = spire - center
        h = np.linalg.norm(vh)
        rotator = self.z2v(vh)
        
        vs_cone = rotator.apply(np.vstack((np.array([[0,0,h]]), vs))) + center
        vs_ground = rotator.apply(vs[:-1]) + center
        
        color = np.tile(self.cm.color2c(color), (2,2,1))
        texture = np.uint8(color*255)
        texcoord_cone = np.tile(np.zeros(2), (vs_cone.shape[0],1))
        texcoord_ground = np.tile(np.zeros(2), (vs_ground.shape[0],1))
        
        self._surface(vs_cone, texture, texcoord_cone, 'F', **kwds)
        self._surface(vs_ground, texture, texcoord_ground, 'P', **kwds)
    
    def cube(self, center, side, color, **kwds):
        """绘制六面体
        
        center      - 中心坐标，元组、列表或numpy数组
        side        - 棱长，整型、浮点型，或长度为3的元组、列表、numpy数组
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        if not isinstance(center, np.ndarray):
            center = np.array(center)
        
        if isinstance(side, (tuple, list, np.ndarray)):
            x, y, z = side
        else:
            x, y, z = side, side, side
        
        vs_front = np.array(((x/2,-y/2,-z/2),(x/2,-y/2,z/2),(x/2,y/2,z/2),(x/2,y/2,-z/2))) + center
        vs_back = np.array(((-x/2,y/2,-z/2),(-x/2,y/2,z/2),(-x/2,-y/2,z/2),(-x/2,-y/2,-z/2))) + center
        vs_top = np.array(((-x/2,y/2,z/2),(x/2,y/2,z/2),(x/2,-y/2,z/2),(-x/2,-y/2,z/2))) + center
        vs_bottom = np.array(((-x/2,-y/2,-z/2),(x/2,-y/2,-z/2),(x/2,y/2,-z/2),(-x/2,y/2,-z/2))) + center
        vs_left = np.array(((x/2,-y/2,z/2),(x/2,-y/2,-z/2),(-x/2,-y/2,-z/2),(-x/2,-y/2,z/2))) + center
        vs_right = np.array(((-x/2,y/2,z/2),(-x/2,y/2,-z/2),(x/2,y/2,-z/2),(x/2,y/2,z/2))) + center
        
        vs = np.vstack((vs_front, vs_back, vs_top, vs_bottom, vs_left, vs_right))
        color = np.tile(self.cm.color2c(color), (2,2,1))
        texture = np.uint8(color*255)
        texcoord = np.tile(np.zeros(2), (24,1))
        
        self._surface(vs, texture, texcoord, 'Q', **kwds)
    
    def cylinder(self, center, radius, color, slices=90, **kwds):
        """绘制圆柱体
        
        center      - 圆柱上下端面圆心坐标，元组、列表或numpy数组，每个元素表示一个端面的圆心坐标
        radius      - 圆柱半径，浮点型
        color       - 颜色，支持形如'#FF0000'形式，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        slices      - 分片数，整型
        kwds        - 关键字参数
                        name        - 模型名
                        visible     - 是否可见，默认可见
                        inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                        fill        - 是否填充颜色，默认填充
                        light       - 光照效果
                            0           - 仅使用环境光
                            1           - 开启前光源
                            2           - 开启后光源
                            3           - 开启前后光源（默认）
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
        
        if not isinstance(center, np.ndarray):
            center = np.array(center)
        
        color = np.tile(self.cm.color2c(color), (2,2,1))
        texture = np.uint8(color*255)
        
        vh = center[1] - center[0]
        h = np.linalg.norm(vh)
        rotator = self.z2v(vh)
        
        theta = np.linspace(0, 2*np.pi, slices, endpoint=False)
        xs = radius * np.cos(theta)
        ys = radius * np.sin(theta)
        zs_b = np.zeros_like(theta)
        zs_t = np.ones_like(theta) * h
        vs_b = np.stack((xs,ys,zs_b), axis=1)
        vs_t = np.stack((xs,ys,zs_t), axis=1)
        
        vs_b = rotator.apply(vs_b) + center[0]
        vs_t = rotator.apply(vs_t) + center[0]
        texcoord_end = np.tile(np.zeros(2), (slices,1))
        
        vs = np.stack((vs_t, vs_b, np.vstack((vs_b[1:],vs_b[:1])), np.vstack((vs_t[1:],vs_t[:1]))), axis=1).reshape(-1,3)
        texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        
        self._surface(vs_b, texture, texcoord_end, 'P', **kwds)
        self._surface(vs_t, texture, texcoord_end, 'P', **kwds)
        self._surface(vs, texture, texcoord, 'Q', **kwds)
    
    def colorbar(self, drange, cm, mode, **kwds):
        """绘制colorBar 
        
        drange      - 值域范围或刻度序列，长度大于1的元组或列表
        cm          - 调色板名称
        mode        - 水平或垂直模式，可选项：'H'|'VR'|'VL'
        kwds        - 关键字参数
                        size            - 显示区域长短边之比，'H'模式默认8，'VR'和'VL'模式默认5
                        subject         - 标题
                        subject_size    - 标题字号，默认56
                        tick_size       - 刻度字号，默认40
                        tick_format     - 刻度标注格式化函数，默认str
                        density         - 刻度密度，最少和最多刻度线组成的元组，默认(3,6)
                        endpoint        - 刻度是否包含值域范围的两个端点值
        """
        
        assert isinstance(drange, (tuple, list)) and len(drange) > 1, '期望参数drange是长度大于1的元组或列表'
        assert mode in ('H','h','VR','vr','VL','vl','V','v'), '期望参数mode为"H"、"VR"或"VL"的一个'
        
        if mode.upper() == 'V':
            mode = 'VR'
        
        for key in kwds:
            if key not in ['size', 'subject', 'subject_size', 'tick_size', 'tick_format', 'density', 'endpoint']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        subject = kwds.get('subject', None)
        subject_size = kwds.get('subject_size', 32) * 3
        size = kwds.get('size', 8 if mode == 'H' else 5)
        tick_size = kwds.get('tick_size', 24) * 3
        tick_format = kwds.get('tick_format', str)
        s_min, s_max = kwds.get('density', (3,6))
        endpoint = kwds.get('endpoint', True)
        kv, kh = 3, 5
        
        dmin, dmax = drange[0], drange[-1]
        if len(drange) > 2:
            ticks = drange if endpoint else drange[1:-1]
        else:
            ticks = self._get_tick_label(dmin, dmax, s_min=s_min, s_max=s_max, endpoint=endpoint)
        
        texcoord = ((0,1),(0,0),(1,0),(1,1))
        colors = self.cm.cmap(np.linspace(dmin, dmax, 256), cm)
        if mode.upper() == 'H':
            texture = np.uint8(np.tile(255*colors, (2,1)).reshape(2,256,3))
        else:
            texture = np.uint8(np.tile(255*colors[::-1], 2).reshape(256,2,3))
        
        if mode == 'H':
            w, h = size, 1
        else:
            w, h = 1, size
        
        if mode.upper() == 'VR':
            if subject is None:
                vs = np.array([[-0.5*w,0,0.5*h],[-0.5*w,0,-0.5*h],[-0.2*w,0,-0.5*h],[-0.2*w,0,0.5*h]])
            else:
                vs = np.array([[-0.5*w,0,0.42*h],[-0.5*w,0,-0.5*h],[-0.2*w,0,-0.5*h],[-0.2*w,0,0.42*h]])
                box = np.array([[-0.5*w,0,0.5*h],[-0.5*w,0,0.42*h],[-0.2*w,0,0.42*h],[-0.2*w,0,0.5*h]])
                self.text3d(subject, box, size=subject_size, k=kv, align='center-middle', light=0, inside=False)
            
            tk = (np.max(vs[:,2])-np.min(vs[:,2]))/(dmax-dmin)
            if not endpoint:
                ticks = ticks[1:-1]
            
            for t in ticks:
                z = (t-dmin)*tk - 0.5*h
                box = np.array([[-0.08*w,0,z+0.1],[-0.08*w,0,z-0.1],[0.5*w,0,z-0.1],[0.5*w,0,z+0.1]])
                self.text3d(tick_format(t), box, size=tick_size, k=kv, align='left-middle', light=0, inside=False)
                self.line(np.array([[-0.2*w,0,z],[-0.13*w,0,z]]), self.scene.style[1], width=0.5, inside=False)
        elif mode.upper() == 'VL':
            if subject is None:
                vs = np.array([[0.2*w,0,0.5*h],[0.2*w,0,-0.5*h],[0.5*w,0,-0.5*h],[0.5*w,0,0.5*h]])
            else:
                vs = np.array([[0.2*w,0,0.42*h],[0.2*w,0,-0.5*h],[0.5*w,0,-0.5*h],[0.5*w,0,0.42*h]])
                box = np.array([[0.2*w,0,0.5*h],[0.2*w,0,0.42*h],[0.5*w,0,0.42*h],[0.5*w,0,0.5*h]])
                self.text3d(subject, box, size=subject_size, k=kv, align='center-middle', light=0, inside=False)
            
            tk = (np.max(vs[:,2])-np.min(vs[:,2]))/(dmax-dmin)
            if not endpoint:
                ticks = ticks[1:-1]
            
            for t in ticks:
                z = (t-dmin)*tk - 0.5*h
                box = np.array([[-0.5*w,0,z+0.1],[-0.5*w,0,z-0.1],[0.08*w,0,z-0.1],[0.08*w,0,z+0.1]])
                self.text3d(tick_format(t), box, size=tick_size, k=kv, align='right-middle', light=0, inside=False)
                self.line(np.array([[0.13*w,0,z],[0.2*w,0,z]]), self.scene.style[1], width=0.5, inside=False)
        else:
            if subject is None:
                vs = np.array([[-0.5*w,0,0.2*h],[-0.5*w,0,-0.1*h],[0.5*w,0,-0.1*h],[0.5*w,0,0.2*h]])
            else:
                vs = np.array([[-0.5*w,0,0.2*h],[-0.5*w,0,-0.1*h],[0.5*w,0,-0.1*h],[0.5*w,0,0.2*h]])
                box = np.array([[-0.5*w,0,0.5*h],[-0.5*w,0,0.3*h],[0.5*w,0,0.3*h],[0.5*w,0,0.5*h]])
                self.text3d(subject, box, size=subject_size, k=kh, align='center-bottom', light=0, inside=False)
            
            tk = (np.max(vs[:,0])-np.min(vs[:,0]))/(dmax-dmin)
            if not endpoint:
                ticks = ticks[1:-1]
            
            for t in ticks:
                x = (t-dmin)*tk - 0.5*w
                box = np.array([[x-0.1,0,-0.25*h],[x-0.1,0,-0.5*h],[x+0.1,0,-0.5*h],[x+0.1,0,-0.25*h]])
                self.text3d(tick_format(t), box, size=tick_size, k=kh, align='center-top', light=0, inside=False)
                self.line(np.array([[x,0,-0.1*h],[x,0,-0.18*h]]), self.scene.style[1], width=0.5, inside=False)
        
        self._surface(vs, texture=texture, texcoord=texcoord, method='Q', light=0, inside=False)
        
    def ticks(self, **kwds):
        """绘制网格和刻度
        
        kwds        - 关键字参数
                        xlabel          - x轴名称，默认'X'
                        ylabel          - y轴名称，默认'Y'
                        zlabel          - z轴名称，默认'Z'
                        xrange          - x轴范围，元组，默None，表示使用数据的动态范围
                        yrange          - y轴范围，元组，默None，表示使用数据的动态范围
                        zrange          - z轴范围，元组，默None，表示使用数据的动态范围
                        xf              - x轴刻度标注格式化函数，默认str
                        yf              - y轴刻度标注格式化函数，默认str
                        zf              - z轴刻度标注格式化函数，默认str
                        font            - 字体，默None，表示使用默认字体
                        labelsize       - 坐标轴标注字号，默认40
                        ticksize        - 刻度标注字号，默认32
                        density         - 刻度密度，最少和最多刻度线组成的元组，默认(3,6)
                        lc              - 网格线颜色，支持形如'#FF0000'形式，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
                        lw              - 网格线宽度，默认0.5
                        bg              - 网格背景色，接受元组、列表或numpy数组形式的RGBA颜色，None表示无背景色
                        
        """
        
        if self.r_x[0] >= self.r_x[1] or self.r_y[0] >= self.r_y[1] or self.r_z[0] >= self.r_z[1]: # '当前没有模型，无法显示网格和刻度'
            return
        
        for key in kwds:
            if key not in ['xlabel', 'ylabel', 'zlabel', 'xrange', 'yrange', 'zrange', 'xf', 'yf', 'zf', 'font', 'labelsize', 'ticksize', 'density', 'lc', 'lw', 'bg']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        xlabel = kwds.get('xlabel', 'X')
        ylabel = kwds.get('ylabel', 'Y')
        zlabel = kwds.get('zlabel', 'Z')
        xrange = kwds.get('xrange', None)
        yrange = kwds.get('yrange', None)
        zrange = kwds.get('zrange', None)
        xf = kwds.get('xf', str)
        yf = kwds.get('yf', str)
        zf = kwds.get('zf', str)
        font = kwds.get('font', None)
        labelsize = kwds.get('labelsize', 40)
        ticksize = kwds.get('ticksize', 32)
        s_min, s_max = kwds.get('density', (3,6))
        lc = kwds.get('lc', np.array(self.scene.style[1]))
        lw = kwds.get('lw', 0.5)
        bg = kwds.get('bg', False)
        
        dx, dy, dz = (self.r_x[1]-self.r_x[0])*0.1, (self.r_y[1]-self.r_y[0])*0.1, (self.r_z[1]-self.r_z[0])*0.1
        x_min, x_max = (self.r_x[0]-dx, self.r_x[1]+dx) if xrange is None else xrange
        y_min, y_max = (self.r_y[0]-dy, self.r_y[1]+dy) if yrange is None else yrange
        z_min, z_max = (self.r_z[0]-dz, self.r_z[1]+dz) if zrange is None else zrange
        
        xx = self._get_tick_label(x_min, x_max, s_min=s_min, s_max=s_max, endpoint=True)
        yy = self._get_tick_label(y_min, y_max, s_min=s_min, s_max=s_max, endpoint=True)
        zz = self._get_tick_label(z_min, z_max, s_min=s_min, s_max=s_max, endpoint=True)
        
        grid_top = uuid.uuid1().hex
        grid_bottom = uuid.uuid1().hex
        grid_left = uuid.uuid1().hex
        grid_right = uuid.uuid1().hex
        grid_front = uuid.uuid1().hex
        grid_back = uuid.uuid1().hex
        
        x_ymin_zmin = uuid.uuid1().hex
        x_ymin_zmax = uuid.uuid1().hex
        x_ymax_zmin = uuid.uuid1().hex
        x_ymax_zmax = uuid.uuid1().hex
        y_xmin_zmin = uuid.uuid1().hex
        y_xmin_zmax = uuid.uuid1().hex
        y_xmax_zmin = uuid.uuid1().hex
        y_xmax_zmax = uuid.uuid1().hex
        z_xmin_ymin = uuid.uuid1().hex
        z_xmin_ymax = uuid.uuid1().hex
        z_xmax_ymin = uuid.uuid1().hex
        z_xmax_ymax = uuid.uuid1().hex
        
        self.scene.grid['top'].append((self, grid_top))
        self.scene.grid['bottom'].append((self, grid_bottom))
        self.scene.grid['left'].append((self, grid_left))
        self.scene.grid['right'].append((self, grid_right))
        self.scene.grid['front'].append((self, grid_front))
        self.scene.grid['back'].append((self, grid_back))
        
        self.scene.grid['x_ymin_zmin'].append((self, x_ymin_zmin))
        self.scene.grid['x_ymin_zmax'].append((self, x_ymin_zmax))
        self.scene.grid['x_ymax_zmin'].append((self, x_ymax_zmin))
        self.scene.grid['x_ymax_zmax'].append((self, x_ymax_zmax))
        self.scene.grid['y_xmin_zmin'].append((self, y_xmin_zmin))
        self.scene.grid['y_xmin_zmax'].append((self, y_xmin_zmax))
        self.scene.grid['y_xmax_zmin'].append((self, y_xmax_zmin))
        self.scene.grid['y_xmax_zmax'].append((self, y_xmax_zmax))
        self.scene.grid['z_xmin_ymin'].append((self, z_xmin_ymin))
        self.scene.grid['z_xmin_ymax'].append((self, z_xmin_ymax))
        self.scene.grid['z_xmax_ymin'].append((self, z_xmax_ymin))
        self.scene.grid['z_xmax_ymax'].append((self, z_xmax_ymax))
        
        vs_zmin, vs_zmax = list(), list()
        for x in xx:
            vs_zmin.append((x, yy[0], z_min))
            vs_zmin.append((x, yy[-1], z_min))
            vs_zmax.append((x, yy[0], z_max))
            vs_zmax.append((x, yy[-1], z_max))
        for y in yy:
            vs_zmin.append((xx[0], y, z_min))
            vs_zmin.append((xx[-1], y, z_min))
            vs_zmax.append((xx[0], y, z_max))
            vs_zmax.append((xx[-1], y, z_max))
        
        vs_xmin, vs_xmax = list(), list()
        for y in yy:
            vs_xmin.append((x_min, y, zz[0]))
            vs_xmin.append((x_min, y, zz[-1]))
            vs_xmax.append((x_max, y, zz[0]))
            vs_xmax.append((x_max, y, zz[-1]))
        for z in zz:
            vs_xmin.append((x_min, yy[0], z))
            vs_xmin.append((x_min, yy[-1], z))
            vs_xmax.append((x_max, yy[0], z))
            vs_xmax.append((x_max, yy[-1], z))
        
        vs_ymin, vs_ymax = list(), list()
        for x in xx:
            vs_ymin.append((x, y_min, zz[0]))
            vs_ymin.append((x, y_min, zz[-1]))
            vs_ymax.append((x, y_max, zz[0]))
            vs_ymax.append((x, y_max, zz[-1]))
        for z in zz:
            vs_ymin.append((xx[0], y_min, z))
            vs_ymin.append((xx[-1], y_min, z))
            vs_ymax.append((xx[0], y_max, z))
            vs_ymax.append((xx[-1], y_max, z))
        
        self.line(np.array(vs_zmax), lc, method='MULTI', width=lw, inside=False, name=grid_top)
        self.line(np.array(vs_zmin), lc, method='MULTI', width=lw, inside=False, name=grid_bottom)
        self.line(np.array(vs_xmax), lc, method='MULTI', width=lw, inside=False, name=grid_right)
        self.line(np.array(vs_xmin), lc, method='MULTI', width=lw, inside=False, name=grid_left)
        self.line(np.array(vs_ymax), lc, method='MULTI', width=lw, inside=False, name=grid_back)
        self.line(np.array(vs_ymin), lc, method='MULTI', width=lw, inside=False, name=grid_front)
        
        if not bg is None:
            xy_x, xy_y = np.meshgrid(xx, yy)
            xy_zmin = np.ones_like(xy_x) * z_min
            xy_zmax = np.ones_like(xy_x) * z_max
            
            zx_x, zx_z = np.meshgrid(xx, zz)
            zx_ymin = np.ones_like(zx_x) * y_min
            zx_ymax = np.ones_like(zx_x) * y_max
            
            yz_y, yz_z = np.meshgrid(yy, zz)
            yz_xmin = np.ones_like(yz_y) * x_min
            yz_xmax = np.ones_like(yz_y) * x_max
            
            self.mesh(xy_x, xy_y, xy_zmin, color=bg, inside=False, light=0, name=grid_bottom)
            self.mesh(xy_x, xy_y, xy_zmax, color=bg, inside=False, light=0, name=grid_top)
            self.mesh(zx_x, zx_ymin, zx_z, color=bg, inside=False, light=0, name=grid_front)
            self.mesh(zx_x, zx_ymax, zx_z, color=bg, inside=False, light=0, name=grid_back)
            self.mesh(yz_xmin, yz_y, yz_z, color=bg, inside=False, light=0, name=grid_left)
            self.mesh(yz_xmax, yz_y, yz_z, color=bg, inside=False, light=0, name=grid_right)
        
        gap, down, i, j, k = 0.2*labelsize/(40*self.scale), 0.03*ticksize/32+0.12*labelsize/(40*self.scale), len(xx)%2, len(yy)%2, len(zz)%2
        self.text(xlabel, pos=((xx[i]+x_max)/2, y_min-gap, z_max+gap), size=labelsize, inside=False, name=x_ymin_zmax)
        self.text(xlabel, pos=((xx[i]+x_max)/2, y_min-gap, z_min-down), size=labelsize, inside=False, name=x_ymin_zmin)
        self.text(xlabel, pos=((xx[i]+x_max)/2, y_max+gap, z_max+gap), size=labelsize, inside=False, name=x_ymax_zmax)
        self.text(xlabel, pos=((xx[i]+x_max)/2, y_max+gap, z_min-down), size=labelsize, inside=False, name=x_ymax_zmin)
        self.text(ylabel, pos=(x_min-gap, (yy[j]+y_max)/2, z_max+gap), size=labelsize, inside=False, name=y_xmin_zmax)
        self.text(ylabel, pos=(x_min-gap, (yy[j]+y_max)/2, z_min-down), size=labelsize, inside=False, name=y_xmin_zmin)
        self.text(ylabel, pos=(x_max+gap, (yy[j]+y_max)/2, z_max+gap), size=labelsize, inside=False, name=y_xmax_zmax)
        self.text(ylabel, pos=(x_max+gap, (yy[j]+y_max)/2, z_min-down), size=labelsize, inside=False, name=y_xmax_zmin)
        self.text(zlabel, pos=(x_max+gap, y_max+gap, (zz[k]+z_max)/2), size=labelsize, inside=False, name=z_xmax_ymax)
        self.text(zlabel, pos=(x_min-gap, y_max+gap, (zz[k]+z_max)/2), size=labelsize, inside=False, name=z_xmin_ymax)
        self.text(zlabel, pos=(x_min-gap, y_min-gap, (zz[k]+z_max)/2), size=labelsize, inside=False, name=z_xmin_ymin)
        self.text(zlabel, pos=(x_max+gap, y_min-gap, (zz[k]+z_max)/2), size=labelsize, inside=False, name=z_xmax_ymin)
        
        gap, down = 0.05*ticksize/(32*self.scale), 0.1*ticksize/(32*self.scale)
        for x in xx[1:-1]:
            self.text(xf(x), pos=(x-gap, y_min-gap, z_max+gap), size=ticksize, inside=False, name=x_ymin_zmax)
            self.text(xf(x), pos=(x-gap, y_min-gap, z_min-down), size=ticksize, inside=False, name=x_ymin_zmin)
            self.text(xf(x), pos=(x+gap, y_max+gap, z_max+gap), size=ticksize, inside=False, name=x_ymax_zmax)
            self.text(xf(x), pos=(x+gap, y_max+gap, z_min-down), size=ticksize, inside=False, name=x_ymax_zmin)
        for y in yy[1:-1]:
            self.text(yf(y), pos=(x_max+gap, y-gap, z_max+gap), size=ticksize, inside=False, name=y_xmax_zmax)
            self.text(yf(y), pos=(x_max+gap, y-gap, z_min-down), size=ticksize, inside=False, name=y_xmax_zmin)
            self.text(yf(y), pos=(x_min-gap, y+gap, z_max+gap), size=ticksize, inside=False, name=y_xmin_zmax)
            self.text(yf(y), pos=(x_min-gap, y+gap, z_min-down), size=ticksize, inside=False, name=y_xmin_zmin)
        for z in zz[1:-1]:
            self.text(zf(z), pos=(x_max+gap, y_max+gap, z-gap), size=ticksize, inside=False, name=z_xmax_ymax)
            self.text(zf(z), pos=(x_min-gap, y_max+gap, z-gap), size=ticksize, inside=False, name=z_xmin_ymax)
            self.text(zf(z), pos=(x_min-gap, y_min-gap, z-gap), size=ticksize, inside=False, name=z_xmin_ymin)
            self.text(zf(z), pos=(x_max+gap, y_min-gap, z-gap), size=ticksize, inside=False, name=z_xmax_ymin)
        
        