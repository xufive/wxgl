# -*- coding: utf-8 -*-

import re
from io import BytesIO
import freetype
from PIL import Image
import numpy as np
import matplotlib.font_manager as mfm
from matplotlib import mathtext

class FontManager:
    """字体管理"""
 
    def __init__(self):
        self.fonts = dict()
        for item in mfm.fontManager.ttflist:
            if item.name in self.fonts:
                self.fonts[item.name].append(item)
            else:
                self.fonts.update({item.name: [item]})
 
        # 设置默认字体
        for item in ('Microsoft YaHei', 'STSong', 'FangSong', 'Songti SC', 'DejaVu Sans'):
            if item in self.fonts:
                self.default_font = item
 
    def get_font_list(self):
        """返回当前系统可用字体列表"""
 
        return list(self.fonts.keys())
 
    def get_default_font(self):
        """返回默认字体"""
 
        return self.default_font
 
    def set_default_font(self, font_name):
        """设置默认字体"""
 
        if font_name in self.fonts:
            self.default_font = font_name
        else:
            raise ValueError('字体%s不在当前系统可用字体列表中'%font_name)
 
    def get_font_file(self, family=None, weight='normal'):
        """返回字体文件"""
 
        if weight not in ['light', 'bold', 'normal']:
            weight = 'normal'
 
        if family not in self.fonts:
            family = self.default_font
 
        if len(self.fonts[family]) > 1:
            for item in self.fonts[family]:
                if item.weight == weight or item.weight == 400 and weight == 'normal':
                    return item.fname
 
        return self.fonts[family][0].fname
 
    def get_text_pixels(self, text, size, font_file):
        """生成文本像素数据"""
 
        face = freetype.Face(font_file)
        face.set_char_size(size*size)
 
        over, under = -1, -1
        pixels = None
 
        for ch in text:
            face.load_char(ch)
            btm_obj = face.glyph.bitmap
            w, h = btm_obj.width, btm_obj.rows
            data = np.array(btm_obj.buffer, dtype=np.uint8).reshape(h,w)
 
            bx, by = int(face.glyph.metrics.horiBearingX/64), int(face.glyph.metrics.horiBearingY/64)
            ha = int(face.glyph.metrics.horiAdvance/64)
            sapre = ha - bx - w
            bottom = h-by
 
            if bottom < 0:
                patch = np.zeros((-bottom, data.shape[1]), dtype=np.uint8)
                data = np.vstack((data, patch))
                bottom = 0
 
            if bx > 0:
                patch = np.zeros((data.shape[0], bx), dtype=np.uint8)
                data = np.hstack((patch, data))
            if sapre > 0:
                patch = np.zeros((data.shape[0], sapre), dtype=np.uint8)
                data = np.hstack((data, patch))
 
            if not isinstance(pixels, np.ndarray):
                pixels = data
                over, under = by, bottom
            else:
                if over > by:
                    patch = np.zeros((over-by, data.shape[1]), dtype=np.uint8)
                    data = np.vstack((patch, data))
                elif over < by:
                    patch = np.zeros((by-over, pixels.shape[1]), dtype=np.uint8)
                    pixels = np.vstack((patch, pixels))
 
                if under > bottom:
                    patch = np.zeros((under-bottom, data.shape[1]), dtype=np.uint8)
                    data = np.vstack((data, patch))
                elif under < bottom:
                    patch = np.zeros((bottom-under, pixels.shape[1]), dtype=np.uint8)
                    pixels = np.vstack((pixels, patch ))
 
                pixels = np.hstack((pixels, data))
                over = max(over, by)
                under = max(under, bottom)
 
        return pixels
 
    def text2alpha(self, text, size, family=None, weight='normal'):
        """文本转透明通道
 
        text        - 文本字符串
        size        - 文字大小，整型
        family      - （系统支持的）字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        """
 
        p = re.compile(r'\$.+\$')
        if p.search(text):
            if family not in self.fonts:
                family = self.default_font
 
            bfo = BytesIO()
            prop = mfm.FontProperties(family=family, size=size, weight=weight)
            mathtext.math_to_image(text, bfo, prop=prop, dpi=72)
 
            im = Image.open(bfo)
            r, g, b, a = im.split()
            r, g, b = 255-np.array(r), 255-np.array(g), 255-np.array(b)
            pixels = np.uint8(r/3 + g/3 + b/3)
        else:
            font_file = self.get_font_file(family=family, weight=weight)
            pixels = self.get_text_pixels(text, size, font_file)
 
        return pixels
 
    def text2img(self, text, size, color, bg=None, padding=0, family=None, weight='normal'):
        """文本转图像，返回图像数据和size元组
 
        text        - 文本字符串
        size        - 文字大小，整型
        color       - 文本颜色，numpy数组
        bg          - 背景色，None表示背景透明
        padding     - 留白
        family      - （系统支持的）字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        """
 
        p = re.compile(r'\$.+\$')
        if p.search(text):
            if family not in self.fonts:
                family = self.default_font
 
            bfo = BytesIO()
            prop = mfm.FontProperties(family=family, size=size, weight=weight)
            mathtext.math_to_image(text, bfo, prop=prop, dpi=72)
 
            im = Image.open(bfo)
            r, g, b, a = im.split()
            r, g, b = 255-np.array(r), 255-np.array(g), 255-np.array(b)
            a = r/3 + g/3 + b/3
 
            r, g, b = r*color[0], g*color[1], b*color[2]
            im = np.dstack((r,g,b,a)).astype(np.uint8)
        else:
            font_file = self.get_font_file(family=family, weight=weight)
            pixels = self.get_text_pixels(text, size, font_file)
            rows, cols = pixels.shape
 
            if rows == 0:
                pixels = np.zeros((1, cols))
 
            r = np.ones(pixels.shape)*color[0]*255
            g = np.ones(pixels.shape)*color[1]*255
            b = np.ones(pixels.shape)*color[2]*255
            im = np.dstack((r,g,b,pixels)).astype(np.uint8)

        if bg is None:
            bg = np.array([0, 0, 0, 0], dtype=np.uint8)
        else:
            bg = np.array([int(255*bg[0]), int(255*bg[1]), int(255*bg[2]), 255], dtype=np.uint8)
            im[im[...,3] == 0] = bg

        if padding > 0:
            ext = np.tile(bg, (im.shape[0], padding, 1))
            im = np.hstack((ext, im, ext))
            ext = np.tile(bg, (padding, im.shape[1], 1))
            im = np.vstack((ext, im, ext))
 
        return im
