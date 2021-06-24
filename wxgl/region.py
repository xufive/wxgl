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
        self.fm = self.scene.fm                                 # 字体管理对象
        self.cm = self.scene.cm                                 # 颜色管理对象
        
        self.buffers = dict()                                   # 缓冲区字典
        self.models = dict()                                    # 模型指令集
        self.grid = dict()                                      # 网格模型
        self.zoom = 1.0                                         # 视口缩放因子，仅当fixed有效时有效
        self.r_x = [1e10, -1e10]                                # 数据在x轴上的动态范围
        self.r_y = [1e10, -1e10]                                # 数据在y轴上的动态范围
        self.r_z = [1e10, -1e10]                                # 数据在z轴上的动态范围
        self.scale = 1.0                                        # 模型缩放比例
        self.translate = np.array([0.0,0.0,0.0])                # 模型位移量
    
    def reset_box(self, box):
        """重置视区大小"""
        
        self.box = box
    
    def reset(self):
        """视区复位"""
        
        for id in self.buffers:
            self.buffers[id].delete()
        
        self.buffers.clear()
        self.models.clear()
        self.grid.clear()
        self.zoom = 1.0
        self.r_x = [1e10, -1e10]
        self.r_y = [1e10, -1e10]
        self.r_z = [1e10, -1e10]
        self.scale = 1.0
        self.translate = np.array([0.0,0.0,0.0])
    
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
    
    def _get_tick_label(self, v_min, v_max, ks=(1, 2, 2.5, 3, 4, 5), s_min=4, s_max=8):
        """返回合适的Colorbar标注值
        
        v_min       - 数据最小值
        v_max       - 数据最大值
        ks          - 分段选项
        s_min       - 分段数最小值
        s_max       - 分段数最大值
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
        
        if result[0] > v_min:
            result.insert(0, v_min)
        if result[-1] < v_max:
            result.append(v_max)
        
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
    
    def reset_scale_translate(self):
        """重新计算scale和translate"""
        
        dist_max = max(self.r_x[1]-self.r_x[0], self.r_y[1]-self.r_y[0], self.r_z[1]-self.r_z[0])
        if dist_max > 0:
            self.scale = 2/dist_max
        self.translate = (-sum(self.r_x)/2, -sum(self.r_y)/2, -sum(self.r_z)/2)
    
    def _add_model(self, name, visible, slide, genre, vars, **kwds):
        """增加模型"""
        
        if name not in self.models:
            self.models.update({name:{'display':visible, 'slide':slide, 'component':list()}})
        else:
            self.models[name]['display'] = visible
            self.models[name]['slide'] = slide
        
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
        
        self.reset_scale_translate()
        
        if not self.models[name]['slide'] is None or 'order' in kwds and kwds['order']:
            self.scene.start_sys_timer()
        
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
                        slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
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
            if key not in ['name', 'visible', 'slide', 'inside', 'fill', 'light', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        slide = kwds.get('slide', None)
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
        
        self._add_model(name, visible, slide, 'surface', [vid, eid, v_type, gl_type, texture], **kwds)
    
    def _mesh(self, xs, ys, zs, texture, **kwds):
        """绘制网格
        
        xs          - 顶点集的x坐标集，numpy.ndarray类型，shape=(rows,cols)
        ys          - 顶点集的y坐标集，numpy.ndarray类型，shape=(rows,cols)
        zs          - 顶点集的z坐标集，numpy.ndarray类型，shape=(rows,cols)
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
            if key not in ['name', 'visible', 'slide', 'inside', 'fill', 'light', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        slide = kwds.get('slide', None)
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
            r_x = (np.nanmin(xs),np.nanmax(xs))
            r_y = (np.nanmin(ys),np.nanmax(ys))
            r_z = (np.nanmin(zs),np.nanmax(zs))
            self.set_data_range(r_x, r_y, r_z)
        
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
        
        self._add_model(name, visible, slide, 'mesh', [vid, eid, v_type, gl_type, texture], **kwds)
    
    def normalize2d(self, vs):
        """二维数组正则化（基于L2范数）
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)
        """
        
        k = np.linalg.norm(vs, axis=1)
        k[k==0] = 1e-300
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
        
        wx.CallAfter(self.scene._update_grid)
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
    
    def drop_model(self, name):
        """删除模型"""
        
        if name in self.models:
            for item in self.models[name]['component']:
                self.buffers[item['args'][0]].delete()
                if item['genre'] in ['line', 'point', 'surface', 'mesh']:
                    self.buffers[item['args'][1]].delete()
                if item['genre'] == 'surface' or item['genre'] == 'mesh':
                    self.delete_texture(item['args'][4])
            del self.models[name]
    
    def text(self, text, pos, size=32, color=None, family=None, weight='normal', align=None, **kwds):
        """绘制2D文字
        
        text        - 文本字符串
        pos         - 文本位置，元组、列表或numpy数组
        size        - 文字大小，整型
        color       - 文本颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
        family      - （系统支持的）字体，None表示当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        align       - 对齐方式
                        None            - 横排文字，（默认）
                        'VL'            - 竖排文字，自下而上
                        'VR'            - 竖排文字，自上而下
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
        
        for key in kwds:
            if key not in ['name', 'visible', 'slide', 'inside', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        slide = kwds.get('slide', None)
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
        
        pixels = self.fm.text2alpha(text, size, family=family, weight=weight)
        
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
        
        kwds = {'rotate':rotate, 'translate':translate, 'order':order}
        self._add_model(name, visible, slide, 'text', [pid, rows, cols, pos])
    
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
                        inside      - 是否更新数据动态范围
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
            if key not in ['name', 'inside', 'visible', 'slide', 'light', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        kwds.update({'light':0})
        
        if isinstance(box, (tuple, list)) and len(box) == 4:
            box = np.array(box, dtype=np.float64)
        if not isinstance(box, np.ndarray) or box.shape != (4,3):
            raise ValueError('期望参数vs是4个点的坐标组成的元组、列表或numpy数组')
        
        if color is None:
            color = np.array(self.scene.style[1])
        else:
            color = self.cm.color2c(color)
        
        texcoord =  np.array([[0,1],[0,0],[1,0],[1,1]])
        texture = self.fm.text2img(text, size, color, family, weight)
        
        cw0, ch0 = self.scene.osize[0]*self.box[2], self.scene.osize[1]*self.box[3]
        cw, ch = self.scene.size[0]*self.box[2], self.scene.size[1]*self.box[3]
        
        if cw0 > ch0:
            k = pow(self.scene.tscale[1], 1/2)
        else:
            k = pow(self.scene.tscale[0], 1/2)
        
        k *= pow(max(self.box[2], self.box[3]), 1/3)
        k *= size/pow(self.scale, 1/2)
        k = 28*pow(k/40, 2)
        
        iw, ih = k*texture.shape[1]/texture.shape[0], k
        if cw > ch:
            w, h = iw/ch, ih/ch
        else:
            w, h = iw/cw, ih/cw
        
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
        
        self._surface(box, texture, texcoord, 'Q', **kwds)
        
    def point(self, vs, color, size=None, **kwds):
        """绘制点
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)
        color       - 顶点或顶点集颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        size        - 点的大小，整数，None表示使用当前设置
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
        
        for key in kwds:
            if key not in ['name', 'visible', 'slide', 'inside', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        slide = kwds.get('slide', None)
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
        
        c = self.cm.color2c(color, size=vs.shape[0], drop=True)
        vid = self._create_vbo(np.hstack((c,vs)).astype(np.float32))
        eid = self._create_ebo(np.array(list(range(vs.shape[0])), dtype=np.int32))
        
        v_type = GL_C3F_V3F
        gl_type = GL_POINTS
        kwds = {'rotate':rotate, 'translate':translate, 'order':order}
        
        self._add_model(name, visible, slide, 'point', [vid, eid, v_type, gl_type, size], **kwds)
        
    def line(self, vs, color, method='SINGLE', width=None, stipple=None, **kwds):
        """绘制线段
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)
        color       - 顶点或顶点集颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
        method      - 绘制方法
                        'MULTI'     - 线段
                        'SINGLE'    - 连续线段
                        'LOOP'      - 闭合线段
        width       - 线宽，0.0~10.0之间，None表示使用当前设置
        stipple     - 线型，整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None表示使用当前设置
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
        
        for key in kwds:
            if key not in ['name', 'visible', 'slide', 'inside', 'regulate', 'rotate', 'translate', 'order']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        visible = kwds.get('visible', True)
        slide = kwds.get('slide', None)
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
        
        c = self.cm.color2c(color, size=vs.shape[0], drop=True)
        vid = self._create_vbo(np.hstack((c,vs)).astype(np.float32))
        eid = self._create_ebo(np.array(list(range(vs.shape[0])), dtype=np.int32))
        
        v_type = GL_C3F_V3F
        gl_type = {'MULTI':GL_LINES, 'SINGLE':GL_LINE_STRIP, 'LOOP':GL_LINE_LOOP}[method]
        kwds = {'rotate':rotate, 'translate':translate, 'order':order}
        
        self._add_model(name, visible, slide, 'line', [vid, eid, v_type, gl_type, width, stipple], **kwds)
    
    def quad(self, vs, color=None, texture=None, texcoord=None, **kwds):
        """绘制一个或多个四角面（每个四角面的四个顶点通常在一个平面上）
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)，n为4的整数倍。四角面的四个顶点按逆时针顺序排列
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
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
            c = self.cm.color2c(color, size=(2,2))
            texture = np.uint8(c*255)
            texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        elif texture is None or texcoord is None:
            raise ValueError('参数color为None时，参数texcoord和texture必须同时有效')
        
        self._surface(vs, texture, texcoord, 'Q', **kwds)
    
    def triangle(self, vs, color=None, texture=None, texcoord=None, **kwds):
        """绘制一个或多个三角面
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)，n为3的整数倍。三角面的三个顶点按逆时针顺序排列
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
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
            c = self.cm.color2c(color, size=(2,2))
            texture = np.uint8(c*255)
            texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        elif texture is None or texcoord is None:
            raise ValueError('参数color为None时，参数texcoord和texture必须同时有效')
        
        self._surface(vs, texture, texcoord, 'T', **kwds)
    
    def fan(self, vs, color=None, texture=None, texcoord=None, **kwds):
        """绘制扇面
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)，首元素为中心点，其余元素为圆弧上顺序排列的点
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
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
            c = self.cm.color2c(color, size=(2,2))
            texture = np.uint8(c*255)
            texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        elif texture is None or texcoord is None:
            raise ValueError('参数color为None时，参数texcoord和texture必须同时有效')
        
        self._surface(vs, texture, texcoord, 'F', **kwds)
    
    def polygon(self, vs, color, **kwds):
        """绘制多边形
        
        vs          - 顶点坐标集，numpy数组，shape=(n,3)，多边形顺序列出的顶点
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
        
        c = self.cm.color2c(color, size=(2,2))
        texture = np.uint8(c*255)
        texcoord = np.tile(np.zeros(2), (vs.shape[0],1))
        
        self._surface(vs, texture, texcoord, 'P', **kwds)
    
    def surface(self, vs, color=None, texture=None, texcoord=None, method='Q', **kwds):
        """绘制表面
        
        vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
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
            c = self.cm.color2c(color, size=(2,2))
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
            c = self.cm.color2c(color, size=(2,2))
            texture = np.uint8(c*255)
        elif texture is None:
            raise ValueError('参数color和texture不能同时为None')
        
        self._mesh(xs, ys, zs, texture, **kwds)
    
    def sphere(self, center, radius, color=None, texture=None, slices=90, **kwds):
        """绘制球体
        
        center      - 球心坐标，元组、列表或numpy数组
        radius      - 半径，浮点型
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
            c = self.cm.color2c(color, size=(2,2))
            texture = np.uint8(c*255)
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
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
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
        
        c = self.cm.color2c(color, size=(2,2))
        texture = np.uint8(c*255)
        texcoord_cone = np.tile(np.zeros(2), (vs_cone.shape[0],1))
        texcoord_ground = np.tile(np.zeros(2), (vs_ground.shape[0],1))
        
        self._surface(vs_cone, texture, texcoord_cone, 'F', **kwds)
        self._surface(vs_ground, texture, texcoord_ground, 'P', **kwds)
    
    def cube(self, center, side, color, **kwds):
        """绘制六面体
        
        center      - 中心坐标，元组、列表或numpy数组
        side        - 棱长，整型、浮点型，或长度为3的元组、列表、numpy数组
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
        c = self.cm.color2c(color, size=(2,2))
        texture = np.uint8(c*255)
        texcoord = np.tile(np.zeros(2), (24,1))
        
        self._surface(vs, texture, texcoord, 'Q', **kwds)
    
    def cylinder(self, center, radius, color, slices=90, **kwds):
        """绘制圆柱体
        
        center      - 圆柱上下端面圆心坐标，元组、列表或numpy数组，每个元素表示一个端面的圆心坐标
        radius      - 圆柱半径，浮点型
        color       - 颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]
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
        
        c = self.cm.color2c(color, size=(2,2))
        texture = np.uint8(c*255)
        
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
                        subject         - 标题
                        subject_size    - 标题字号，默认44
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
            if key not in ['subject', 'subject_size', 'tick_size', 'tick_format', 'density', 'endpoint']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        subject = kwds.get('subject', None)
        subject_size = kwds.get('subject_size', 44)
        tick_size = kwds.get('tick_size', 40)
        tick_format = kwds.get('tick_format', str)
        s_min, s_max = kwds.get('density', (3,6))
        endpoint = kwds.get('endpoint', True)
        
        dmin, dmax = drange[0], drange[-1]
        if len(drange) > 2:
            ticks = drange
        else:
            ticks = self._get_tick_label(dmin, dmax, s_min=s_min, s_max=s_max)
        
        if endpoint:
            if (ticks[1]-ticks[0])/(ticks[2]-ticks[1]) < 0.2:
                ticks.remove(ticks[1])
            if (ticks[-1]-ticks[-2])/(ticks[-2]-ticks[-3]) < 0.2:
                ticks.remove(ticks[-2])
        else:
            ticks = ticks[1:-1]
        
        texcoord = ((0,1),(0,0),(1,0),(1,1))
        colors = self.cm.cmap(np.linspace(dmin, dmax, 256), cm)
        if mode.upper() == 'H':
            texture = np.uint8(np.tile(255*colors, (2,1)).reshape(2,256,3))
        else:
            texture = np.uint8(np.tile(255*colors[::-1], 2).reshape(256,2,3))
        
        cw, ch = self.scene.size[0]*self.box[2], self.scene.size[1]*self.box[3]
        side = max(cw, ch)/min(cw, ch)
        
        if mode == 'H':
            w, h = 1.0*side, 1.2
        else:
            w, h = 1, 1.4*side
        
        if mode.upper() == 'VR':
            if subject is None:
                vs = np.array([[-0.5*w,0.5*h,0],[-0.5*w,-0.5*h,0],[-0.2*w,-0.5*h,0],[-0.2*w,0.5*h,0]])
            else:
                vs = np.array([[-0.5*w,0.42*h,0],[-0.5*w,-0.5*h,0],[-0.2*w,-0.5*h,0],[-0.2*w,0.42*h,0]])
                box = np.array([[-0.5*w,0.5*h,0],[-0.5*w,0.42*h,0],[-0.2*w,0.42*h,0],[-0.2*w,0.5*h,0]])
                self.text3d(subject, box, size=subject_size, align='center-middle', light=0, inside=False)
            
            tk = (np.max(vs[:,1])-np.min(vs[:,1]))/(dmax-dmin)
            for t in ticks:
                y = (t-dmin)*tk - 0.5*h
                box = np.array([[-0.08*w,y+0.1,0],[-0.08*w,y-0.1,0],[0.5*w,y-0.1,0],[0.5*w,y+0.1,0]])
                self.text3d(tick_format(t), box, size=tick_size, align='left-middle', light=0, inside=False)
                self.line(np.array([[-0.2*w,y,0],[-0.13*w,y,0]]), self.scene.style[1], width=0.5, inside=False)
        elif mode.upper() == 'VL':
            if subject is None:
                vs = np.array([[0.2*w,0.5*h,0],[0.2*w,-0.5*h,0],[0.5*w,-0.5*h,0],[0.5*w,0.5*h,0]])
            else:
                vs = np.array([[0.2*w,0.42*h,0],[0.2*w,-0.5*h,0],[0.5*w,-0.5*h,0],[0.5*w,0.42*h,0]])
                box = np.array([[0.2*w,0.5*h,0],[0.2*w,0.42*h,0],[0.5*w,0.42*h,0],[0.5*w,0.5*h,0]])
                self.text3d(subject, box, size=subject_size, align='center-middle', light=0, inside=False)
            
            tk = (np.max(vs[:,1])-np.min(vs[:,1]))/(dmax-dmin)
            for t in ticks:
                y = (t-dmin)*tk - 0.5*h
                box = np.array([[-0.5*w,y+0.1,0],[-0.5*w,y-0.1,0],[0.08*w,y-0.1,0],[0.08*w,y+0.1,0]])
                self.text3d(tick_format(t), box, size=tick_size, align='right-middle', light=0, inside=False)
                self.line(np.array([[0.13*w,y,0],[0.2*w,y,0]]), self.scene.style[1], width=0.5, inside=False)
        else:
            if subject is None:
                vs = np.array([[-0.5*w,0.2*h,0],[-0.5*w,-0.1*h,0],[0.5*w,-0.1*h,0],[0.5*w,0.2*h,0]])
            else:
                vs = np.array([[-0.5*w,0.2*h,0],[-0.5*w,-0.1*h,0],[0.5*w,-0.1*h,0],[0.5*w,0.2*h,0]])
                box = np.array([[-0.5*w,0.5*h,0],[-0.5*w,0.3*h,0],[0.5*w,0.3*h,0],[0.5*w,0.5*h,0]])
                self.text3d(subject, box, size=subject_size, align='center-bottom', light=0, inside=False)
            
            tk = (np.max(vs[:,0])-np.min(vs[:,0]))/(dmax-dmin)
            for t in ticks:
                x = (t-dmin)*tk - 0.5*w
                box = np.array([[x-0.1,-0.25*h,0],[x-0.1,-0.5*h,0],[x+0.1,-0.5*h,0],[x+0.1,-0.25*h,0]])
                self.text3d(tick_format(t), box, size=tick_size, align='center-top', light=0, inside=False)
                self.line(np.array([[x,-0.1*h,0],[x,-0.18*h,0]]), self.scene.style[1], width=0.5, inside=False)
        
        self._surface(vs, texture=texture, texcoord=texcoord, method='Q', light=0, inside=False)
        
    def ticks3d(self, **kwds):
        """绘制3D网格和刻度
        
        kwds        - 关键字参数
                        xlabel          - x轴名称，默认'X'
                        ylabel          - y轴名称，默认'Y'
                        zlabel          - z轴名称，默认'Z'
                        xr              - x轴范围，元组，默None，表示使用数据的动态范围
                        yr              - y轴范围，元组，默None，表示使用数据的动态范围
                        zr              - z轴范围，元组，默None，表示使用数据的动态范围
                        xf              - x轴刻度标注格式化函数，默认str
                        yf              - y轴刻度标注格式化函数，默认str
                        zf              - z轴刻度标注格式化函数，默认str
                        font            - 字体，默None，表示使用默认字体
                        labelsize       - 坐标轴标注字号，默认36
                        ticksize        - 刻度标注字号，默认32
                        xd              - x轴刻度密度调整，整型，值域范围[-2,10], 默认0
                        yd              - y轴刻度密度调整，整型，值域范围[-2,10], 默认0
                        zd              - z轴刻度密度调整，整型，值域范围[-2,10], 默认0
                        lc              - 网格线颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
                        lw              - 网格线宽度，默认0.5
                        bg              - 网格背景色，接受元组、列表或numpy数组形式的RGBA颜色，None表示无背景色
                        
        """
        
        if self.r_x[0] >= self.r_x[1] or self.r_y[0] >= self.r_y[1] or self.r_z[0] >= self.r_z[1]: # '当前没有模型，无法显示网格和刻度'
            return
        
        for key in kwds:
            if key not in ['xlabel','ylabel','zlabel','xr','yr','zr','xf','yf','zf','font','labelsize','ticksize','xd','yd','zd','lc','lw','bg']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        for key in self.grid:
            self.drop_model(self.grid[key])
        self.grid.clear()
        
        xlabel = kwds.get('xlabel', 'X')
        ylabel = kwds.get('ylabel', 'Y')
        zlabel = kwds.get('zlabel', 'Z')
        xr = kwds.get('xr', None)
        yr = kwds.get('yr', None)
        zr = kwds.get('zr', None)
        xf = kwds.get('xf', str)
        yf = kwds.get('yf', str)
        zf = kwds.get('zf', str)
        font = kwds.get('font', None)
        labelsize = kwds.get('labelsize', 36)
        ticksize = kwds.get('ticksize', 32)
        xd = kwds.get('xd', 0)
        yd = kwds.get('yd', 0)
        zd = kwds.get('zd', 0)
        lc = kwds.get('lc', np.array(self.scene.style[1]))
        lw = kwds.get('lw', 0.5)
        bg = kwds.get('bg', None)
        
        if xd < -2:
            xd = -2
        
        if yd < -2:
            yd = -2
        
        if zd < -2:
            zd = -2
        
        dx, dy, dz = (self.r_x[1]-self.r_x[0])*0.1, (self.r_y[1]-self.r_y[0])*0.1, (self.r_z[1]-self.r_z[0])*0.1
        x_min, x_max = (self.r_x[0]-dx, self.r_x[1]+dx) if xr is None else xr
        y_min, y_max = (self.r_y[0]-dy, self.r_y[1]+dy) if yr is None else yr
        z_min, z_max = (self.r_z[0]-dz, self.r_z[1]+dz) if zr is None else zr
        
        xx = self._get_tick_label(x_min, x_max, s_min=3+xd, s_max=6+xd)
        yy = self._get_tick_label(y_min, y_max, s_min=3+yd, s_max=6+yd)
        zz = self._get_tick_label(z_min, z_max, s_min=3+zd, s_max=6+zd)
        
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
        
        self.grid.update({'top': grid_top})
        self.grid.update({'bottom': grid_bottom})
        self.grid.update({'left': grid_left})
        self.grid.update({'right': grid_right})
        self.grid.update({'front': grid_front})
        self.grid.update({'back': grid_back})
        
        self.grid.update({'x_ymin_zmin': x_ymin_zmin})
        self.grid.update({'x_ymin_zmax': x_ymin_zmax})
        self.grid.update({'x_ymax_zmin': x_ymax_zmin})
        self.grid.update({'x_ymax_zmax': x_ymax_zmax})
        self.grid.update({'y_xmin_zmin': y_xmin_zmin})
        self.grid.update({'y_xmin_zmax': y_xmin_zmax})
        self.grid.update({'y_xmax_zmin': y_xmax_zmin})
        self.grid.update({'y_xmax_zmax': y_xmax_zmax})
        self.grid.update({'z_xmin_ymin': z_xmin_ymin})
        self.grid.update({'z_xmin_ymax': z_xmin_ymax})
        self.grid.update({'z_xmax_ymin': z_xmax_ymin})
        self.grid.update({'z_xmax_ymax': z_xmax_ymax})
        
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
        
        self.line(np.array(vs_zmax), lc, width=lw, method='MULTI', inside=False, name=grid_top)
        self.line(np.array(vs_zmin), lc, width=lw, method='MULTI', inside=False, name=grid_bottom)
        self.line(np.array(vs_xmax), lc, width=lw, method='MULTI', inside=False, name=grid_right)
        self.line(np.array(vs_xmin), lc, width=lw, method='MULTI', inside=False, name=grid_left)
        self.line(np.array(vs_ymax), lc, width=lw, method='MULTI', inside=False, name=grid_back)
        self.line(np.array(vs_ymin), lc, width=lw, method='MULTI', inside=False, name=grid_front)
        
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
        if xlabel:
            self.text(xlabel, pos=((xx[i]+x_max)/2, y_min-gap, z_max+gap), size=labelsize, inside=False, name=x_ymin_zmax)
            self.text(xlabel, pos=((xx[i]+x_max)/2, y_min-gap, z_min-down), size=labelsize, inside=False, name=x_ymin_zmin)
            self.text(xlabel, pos=((xx[i]+x_max)/2, y_max+gap, z_max+gap), size=labelsize, inside=False, name=x_ymax_zmax)
            self.text(xlabel, pos=((xx[i]+x_max)/2, y_max+gap, z_min-down), size=labelsize, inside=False, name=x_ymax_zmin)
        if ylabel:
            self.text(ylabel, pos=(x_min-gap, (yy[j]+y_max)/2, z_max+gap), size=labelsize, inside=False, name=y_xmin_zmax)
            self.text(ylabel, pos=(x_min-gap, (yy[j]+y_max)/2, z_min-down), size=labelsize, inside=False, name=y_xmin_zmin)
            self.text(ylabel, pos=(x_max+gap, (yy[j]+y_max)/2, z_max+gap), size=labelsize, inside=False, name=y_xmax_zmax)
            self.text(ylabel, pos=(x_max+gap, (yy[j]+y_max)/2, z_min-down), size=labelsize, inside=False, name=y_xmax_zmin)
        if zlabel:
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
        
    def ticks2d(self, **kwds):
        """绘制2D网格和刻度
        
        kwds        - 关键字参数
                        xlabel          - x轴名称，默认'X'
                        ylabel          - y轴名称，默认'Y'
                        xr              - x轴范围，元组，默None，表示使用数据的动态范围
                        yr              - y轴范围，元组，默None，表示使用数据的动态范围
                        xf              - x轴刻度标注格式化函数，默认str
                        yf              - y轴刻度标注格式化函数，默认str
                        font            - 字体，默None，表示使用默认字体
                        labelsize       - 坐标轴标注字号，默认48
                        ticksize        - 刻度标注字号，默认40
                        xrotate         - 是否旋转x轴刻度，默认不旋转
                        yreverse        - 是否反转y轴刻度，默认不反转
                        xd              - x轴刻度密度调整，整型，值域范围[-2,10], 默认0
                        yd              - y轴刻度密度调整，整型，值域范围[-2,10], 默认0
                        lc              - 网格线颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
                        lw              - 网格线宽度，默认0.5
                        bg              - 网格背景色，接受元组、列表或numpy数组形式的RGBA颜色，None表示无背景色
                        
        """
        
        if self.r_x[0] >= self.r_x[1] and self.r_y[0] >= self.r_y[1] and self.r_z[0] >= self.r_z[1]: # '当前没有模型，无法显示网格和刻度'
            return
        
        for key in kwds:
            if key not in ['xlabel','ylabel','xr','yr','xf','yf','font','labelsize','ticksize','xrotate','yreverse','xd','yd','lc','lw','bg']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        xlabel = kwds.get('xlabel', 'X')
        ylabel = kwds.get('ylabel', 'Y')
        xr = kwds.get('xr', None)
        yr = kwds.get('yr', None)
        xf = kwds.get('xf', str)
        yf = kwds.get('yf', str)
        font = kwds.get('font', None)
        labelsize = kwds.get('labelsize', 48)
        ticksize = kwds.get('ticksize', 40)
        xrotate = kwds.get('xrotate', False)
        yreverse = kwds.get('yreverse', False)
        xd = kwds.get('xd', 0)
        yd = kwds.get('yd', 0)
        lc = kwds.get('lc', np.array(self.scene.style[1]))
        lw = kwds.get('lw', 1)
        bg = kwds.get('bg', False)
        
        if xd < -2:
            xd = -2
        
        if yd < -2:
            yd = -2
        
        dx, dy = (self.r_x[1]-self.r_x[0])*0.03, (self.r_y[1]-self.r_y[0])*0.03
        da = max(dx,dy)
        
        x_min, x_max = (self.r_x[0]-dx, self.r_x[1]+dx) if xr is None else xr
        y_min, y_max = (self.r_y[0]-dy, self.r_y[1]+dy) if yr is None else yr
        
        xx = self._get_tick_label(x_min, x_max, s_min=3+xd, s_max=6+xd)
        yy = self._get_tick_label(y_min, y_max, s_min=3+yd, s_max=6+yd)
        
        self.line(np.array([[x_min,y_min,0],[x_max,y_min,0]]), lc, width=lw, inside=False)
        self.line(np.array([[x_min,y_min,0],[x_min,y_max,0]]), lc, width=lw, inside=False)
        
        self.surface(np.array([[x_min,y_max+da,0],[x_min-da/4,y_max,0],[x_min+da/4,y_max,0]]), lc, method='T', inside=False, light=False)
        self.surface(np.array([[x_max+da,y_min,0],[x_max,y_min+da/4,0],[x_max,y_min-da/4,0]]), lc, method='T', inside=False, light=False)
        
        if xrotate:
            rx = sstr.from_euler('xyz', [0, 0, 30], degrees=True)
        
        for x in xx[1:-1]:
            self.line(np.array([[x,y_min,0],[x,y_min-da/2,0]]), lc, width=0.5*lw, inside=False)
            if xrotate:
                box = np.array([[x-da,y_min-da,0],[x-da,y_min-2*da,0],[x+da/2,y_min-2*da,0],[x+da/2,y_min-da,0]])
                ro = np.array([x+da/2,y_min-da,0])
                box = rx.apply(box-ro) + ro
                self.text3d(xf(x), box, size=ticksize, align='right-top', inside=False, light=False)
            else:
                box = np.array([[x-da,y_min-da,0],[x-da,y_min-2*da,0],[x+da,y_min-2*da,0],[x+da,y_min-da,0]])
                self.text3d(xf(x), box, size=ticksize, align='center-top', inside=False, light=False)
        
        if yreverse:
            tt = yy[::-1]
            dy = max(tt) + min(tt)
            
            for t in tt[1:-1]:
                y = dy-t
                self.line(np.array([[x_min,y,0],[x_min-da/2,y,0]]), lc, width=0.5*lw, inside=False)
                box = np.array([[x_min-2*da,y+da,0],[x_min-2*da,y-da,0],[x_min-da,y-da,0],[x_min-da,y+da,0]])
                self.text3d(yf(t), box, size=ticksize, align='right-middle', inside=False, light=False)
        else:
            for y in yy[1:-1]:
                self.line(np.array([[x_min,y,0],[x_min-da/2,y,0]]), lc, width=0.5*lw, inside=False)
                box = np.array([[x_min-2*da,y+da,0],[x_min-2*da,y-da,0],[x_min-da,y-da,0],[x_min-da,y+da,0]])
                self.text3d(yf(y), box, size=ticksize, align='right-middle', inside=False, light=False)
        
        if xlabel:
            if len(xlabel) > 3:
                m = (x_min+x_max)/2
                box = np.array([[m-da,y_min-2.5*da,0],[m-da,y_min-3*da,0],[m+da,y_min-3*da,0],[m+da,y_min-2.5*da,0]])
                self.text3d(xlabel, box, size=labelsize, align='center-top', inside=False, light=False)
            else:
                box = np.array([[x_max,y_min-da,0],[x_max,y_min-2*da,0],[x_max+da,y_min-2*da,0],[x_max+da,y_min-da,0]])
                self.text3d(xlabel, box, size=labelsize, align='left-top', inside=False, light=False)
        
        if ylabel:
            if len(ylabel) > 3:
                m = (y_min+y_max)/2
                k = max(map(len, map(yf, yy[1:-1])))//3
                box = np.array([[x_min-(5+k)*da,m+da,0],[x_min-(5+k)*da,m-da,0],[x_min-(3+k)*da,m-da,0],[x_min-(3+k)*da,m+da,0]])
                regulate = (((4+k)*da-x_min, -m, 0), (90, (0,0,1)), (x_min-(4+k)*da, m, 0))
                self.text3d(ylabel, box, size=labelsize, align='center-middle', regulate=regulate, inside=False, light=False)
            else:
                box = np.array([[x_min-2*da,y_max+da,0],[x_min-2*da,y_max,0],[x_min-da,y_max,0],[x_min-da,y_max+da,0]])
                self.text3d(ylabel, box, size=labelsize, align='right-top', inside=False, light=False)
        
        for key in self.grid:
            self.drop_model(self.grid[key])
        
        name = uuid.uuid1().hex
        self.grid.clear()
        self.grid.update({'grid':name})
        
        vs = list()
        for x in xx[1:]:
            vs.append((x, y_min, 0))
            vs.append((x, y_max, 0))
        for y in yy[1:]:
            vs.append((x_min, y, 0))
            vs.append((x_max, y, 0))
        
        self.line(np.array(vs), lc, width=0.3*lw, method='MULTI', stipple=(1,0xF0F0), inside=False, name=name)