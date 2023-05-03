#!/usr/bin/env python3

import os
import struct
import binascii
import numpy as np
import wxgl

lzf_is_available = True
try:
    import lzf
except:
    lzf_is_available = False

class PointCloudData:
    """读取点云数据文件"""
    
    def __init__(self, pcfile):
        """构造函数，pcfile为点云数据文件名"""

        self.ok = True                  # 数据是否可用
        self.info = '正常：数据可用'    # 数据可用性说明
        self.raw = dict()               # 解读出来的原始数据

        ext = os.path.splitext(pcfile)[1].lower()
        if ext == '.ply':
            self.open_ply(pcfile)
        elif ext == '.pcd':
            self.open_pcd(pcfile)
        else:
            self.ok = False
            self.info = '错误：不支持的点云数据文件格式：%s'%ext

    @property
    def fields(self):
        """数据字段（项）名"""

        return list(self.raw.keys())

    @property
    def xyz(self):
        """坐标数据"""

        if 'x' in self.raw and 'y' in self.raw and 'z' in self.raw:
            xyz = np.stack((self.raw['x'], self.raw['y'], self.raw['z']), axis=1)
        elif 'X' in self.raw and 'Y' in self.raw and 'Z' in self.raw:
            xyz = np.stack((self.raw['X'], self.raw['Y'], self.raw['Z']), axis=1)
        else:
            xyz = None 

        return xyz

    @property
    def rgb(self):
        """颜色数据，浮点型，值域范围[0,1]"""

        if 'r' in self.raw and 'g' in self.raw and 'b' in self.raw:
            rgb = np.stack((self.raw['r'], self.raw['g'], self.raw['b']), axis=1)
            if rgb.dtype == np.uint8:
                rgb = np.float64(self.rgb) / 255
        elif 'R' in self.raw and 'G' in self.raw and 'B' in self.raw:
            rgb = np.stack((self.raw['R'], self.raw['G'], self.raw['B']), axis=1)
            if rgb.dtype == np.uint8:
                rgb = np.float64(self.rgb) / 255
        elif 'rgb' in self.raw and self.raw['rgb'].dtype == np.float32:
            rgb = list()
            cs = binascii.hexlify(self.raw['rgb'].tobytes()).decode()
            for i in range(0, len(cs), 8):
                rgb.append([int(cs[i+2:i+4], base=16)/255, int(cs[i+4:i+6], base=16)/255, int(cs[i+6:i+8], base=16)/255])
            rgb = np.array(rgb, dtype=np.float32)
        elif 'RGB' in self.raw and self.raw['RGB'].dtype == np.float32:
            rgb = list()
            cs = binascii.hexlify(self.raw['RGB'].tobytes()).decode()
            for i in range(0, len(cs), 8):
                rgb.append([int(cs[i+2:i+4], base=16)/255, int(cs[i+4:i+6], base=16)/255, int(cs[i+6:i+8], base=16)/255])
            rgb = np.array(rgb, dtype=np.float32)
        else:
            rgb = None

        return rgb

    @property
    def intensity(self):
        """强度数据"""

        if 'intensity' in self.raw:
            return self.raw['intensity']
        elif 'Intensity' in self.raw:
            return self.raw['Intensity']
        elif 'i' in self.raw:
            return self.raw['i']
        else:
            return None

    def lzf_decompress(self, content, olen):
        """LZF解压缩算法，content为压缩内容，olen为解压后的期望长度"""

        iidx, out = 0, list()
        while iidx < len(content):
            c = content[iidx]
            iidx += 1

            if c < 32:
                c += 1
                if len(out) + c > olen:
                    break 
                
                for i in range(c):
                    out.append(content[iidx:iidx+1])
                    iidx += 1
            else:
                k = c >> 5
                if k == 7:
                    k += content[iidx]
                    iidx += 1
                
                if (len(out) + k + 2 > olen):
                    break
                
                rf = len(out) - ((c & 0x1f) << 8) - 1 - content[iidx]
                iidx += 1

                if rf < 0:
                    break
                
                out.append(out[rf])
                rf += 1
                out.append(out[rf])
                rf += 1

                for i in range(k):
                    out.append(out[rf])
                    rf += 1

        return b''.join(out)

    def open_ply(self, pcfile):
        """读ply格式的点云文件"""

        with open(pcfile, 'rb') as fp:
            line = fp.readline().decode().strip()
            if line != 'ply':
                self.ok = False
                self.info = '错误：不合规范的PLY文件'
                return

            bin_type = {
                'float32':  ('f', 4, np.float32),       'float':    ('f', 4, np.float32),
                'float64':  ('d', 8, np.float64),       'double':   ('d', 8, np.float64),
                'int8':     ('b', 1, np.int8),          'char':     ('b', 1, np.int8),
                'int16':    ('h', 2, np.int16),         'short':    ('h', 2, np.int16),
                'int32':    ('i', 4, np.int32),         'int':      ('i', 4, np.int32),
                'uint8':    ('B', 1, np.uint8),         'uchar':    ('B', 1, np.uint8),
                'uint16':   ('H', 2, np.uint16),        'ushort':   ('H', 2, np.uint16),
                'uint32':   ('I', 4, np.uint32),        'uint':     ('I', 4, np.uint32)
            }

            is_vertex, total, encoding, fields, otypes, nb = False, None, None, list(), list(), 0
            while True:
                pieces = fp.readline().decode().strip().split()
                if pieces[0] == 'format':
                    encoding = pieces[1]
                    if encoding != 'ascii':
                        sbin = '<' if encoding=='binary_little_endian' else '>'
                elif pieces[0] == 'element':
                    if pieces[1] == 'vertex':
                        is_vertex = True
                        total = int(pieces[2])
                    else:
                        is_vertex = False
                elif pieces[0] == 'property':
                    if is_vertex:
                        fields.append(pieces[2])
                        dtype = pieces[1].lower()
                        if dtype in bin_type:
                            otypes.append(bin_type[dtype][2])
                            if encoding != 'ascii':
                                nb +=  bin_type[dtype][1]
                                sbin += bin_type[dtype][0]
                        else:
                            self.ok = False
                            self.info = '错误：未识别的数据类型或长度'
                            return
                elif pieces[0] == 'end_header':
                    break
                elif pieces[0] == 'comment':
                    continue
                else:
                    self.ok = False
                    self.info = '错误：文件头包含未识别的信息'
                    return

            if len(fields) == 0 or len(otypes) != len(fields) or total is None or encoding is None:
                self.ok = False
                self.info = '错误：文件头缺项'
                return

            if encoding == 'ascii':
                v = np.array([list(map(float, line.decode().strip().split())) for line in fp.readlines()[:total]], dtype=np.float64)
            else:
                try:
                    v = np.array(list(struct.iter_unpack(sbin, fp.read(total*nb))), dtype=np.float64)
                except:
                    self.ok = False
                    self.info = '错误：解析二进制数据出现意外'
                    return
 
        for i in range(len(fields)):
            key, otype = fields[i], otypes[i]
            self.raw.update({key: otype(v[:,i])})

    def open_pcd(self, pcfile):
        """读pcd格式的点云文件"""

        with open(pcfile, 'rb') as fp:
            line = fp.readline().decode().strip()
            if not line.startswith('# .PCD'):
                self.ok = False
                self.info = '错误：不合规范的PCD文件'
                return

            fields, sizes, types, total, encoding = None, None, None, None, None
            while True:
                pieces = fp.readline().decode().strip().split()
                if pieces[0] == 'VERSION':
                    self.raw.update({'version': pieces[1]})
                elif pieces[0] == 'FIELDS':
                    fields = pieces[1:]
                elif pieces[0] == 'SIZE':
                    sizes = pieces[1:]
                elif pieces[0] == 'TYPE':
                    types = pieces[1:]
                elif pieces[0] == 'POINTS':
                    total = int(pieces[1])
                elif pieces[0] == 'DATA':
                    encoding = pieces[1]
                    break
                elif pieces[0] in ('COUNT', 'WIDTH', 'HEIGHT', 'VIEWPOINT'):
                    continue
                else:
                    self.ok = False
                    self.info = '错误：文件头包含未识别的信息'
                    return
                
            if fields is None or sizes is None or types is None or total is None or encoding is None:
                self.ok = False
                self.info = '错误：文件头缺项'
                return

            bin_type = {
                '4F':   ('f', np.float32),
                '8F':   ('d', np.float64),
                '1I':   ('b', np.int8),
                '2I':   ('h', np.int16),
                '4I':   ('i', np.int32),
                '1U':   ('B', np.uint8),
                '2U':   ('H', np.uint16),
                '4U':   ('I', np.uint32)
            }

            sbin, nb, otypes = '', list(), list()
            for s, t in zip(sizes, types):
                nb.append(int(s))
                st = s + t
                if st in bin_type:
                    sbin += bin_type[st][0]
                    otypes.append(bin_type[st][1])
                else:
                    self.ok = False
                    self.info = '错误：未识别的数据类型或长度'
                    return

            if encoding == 'ascii':
                v = np.array([list(map(float, line.decode().strip().split())) for line in fp.readlines()[:total]], dtype=np.float64)
            elif encoding == 'binary_compressed':
                try:
                    len_0, len_1 = struct.unpack('II', fp.read(8))
                    if lzf_is_available:
                        content = lzf.decompress(fp.read()[:len_0], len_1)
                    else:
                        content = self.lzf_decompress(fp.read()[:len_0], len_1)
                    
                    start, v = 0, list()
                    for s, n in zip(sbin, nb):
                        end = start + total*n
                        v.append(np.array(list(struct.iter_unpack(s, content[start:end])), dtype=np.float64))
                        start = end
                    v = np.stack(v, axis=0).transpose()[0]
                except:
                    self.ok = False
                    self.info = '错误：解析二进制数据出现意外'
                    return
            else:
                try:
                    v = np.array(list(struct.iter_unpack(sbin, fp.read(total*sum(nb)))), dtype=np.float64)
                except:
                    self.ok = False
                    self.info = '错误：解析二进制数据出现意外'
                    return
            
        for i in range(len(fields)):
            key, otype = fields[i], otypes[i]
            self.raw.update({key: otype(v[:,i])})

