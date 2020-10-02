# -*- coding: utf-8 -*-

import freetype
import numpy as np
import matplotlib.font_manager as mfm


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
        if 'Microsoft YaHei' in self.fonts:
            self.default_font = 'Microsoft YaHei' # 微软雅黑
        elif 'FangSong' in self.fonts:
            self.default_font = 'FangSong' # 仿宋
        elif 'STSong' in self.fonts:
            self.default_font = 'STSong' # 宋体
        else:
            self.default_font = mfm.ttfFontProperty(mfm.get_font(mfm.findfont(''))).name # matplotlib默认字体
    
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
