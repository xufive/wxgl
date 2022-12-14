#!/usr/bin/env python3

import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

import wxgl
import wxgl.qtscene

class MyWindow(QWidget):
    """从QWidget类派生的桌面应用程序窗口类"""
    
    def __init__(self):
        """构造函数"""
        
        super().__init__()
        
        self.setWindowTitle('多场景测试')
        self.setGeometry(0, 0, 1200, 800) # 设置窗位置和大小
        
        self.canvas_1 = wxgl.qtscene.QtScene(self, self.draw_scatter())
        self.canvas_2 = wxgl.qtscene.QtScene(self, self.draw_line(), menu=False)
        self.canvas_3 = wxgl.qtscene.QtScene(self, self.draw_mesh())
        self.canvas_4 = wxgl.qtscene.QtScene(self, self.draw_surface())

        hbox_1 = QHBoxLayout()
        hbox_1.addSpacing(10)
        hbox_1.addWidget(self.canvas_1)
        hbox_1.addWidget(self.canvas_2)
        hbox_1.addSpacing(10)
        
        hbox_2 = QHBoxLayout()
        hbox_2.addSpacing(10)
        hbox_2.addWidget(self.canvas_3)
        hbox_2.addWidget(self.canvas_4)
        hbox_2.addSpacing(10)

        vbox = QVBoxLayout() 
        vbox.addSpacing(10)
        vbox.addLayout(hbox_1)
        vbox.addSpacing(5)
        vbox.addLayout(hbox_2)
        vbox.addSpacing(10)

        # 将垂直布局管理器应用到窗口
        self.setLayout(vbox)

        self.show() # 显示窗口

    def closeEvent(self, evt):
        self.canvas_1.clear_buffer()
        self.canvas_2.clear_buffer()
        self.canvas_3.clear_buffer()
        self.canvas_4.clear_buffer()

    def draw_scatter(self):
        vs = np.random.random((30, 3))*2-1
        data = np.arange(30)

        sch = wxgl.Scheme()
        sch.scatter(vs, data=data, size=50, alpha=0.8)
        
        return sch

    def draw_surface(self):
        vs = np.array([
            [-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5],
            [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5]
        ], dtype=np.float32)

        indices = np.array([
            0, 3, 1, 1, 3, 2, 4, 0, 5, 5, 0, 1, 3, 7, 2, 2, 7, 6, 
            7, 4, 6, 6, 4, 5, 1, 2, 5, 5, 2, 6, 4, 7, 0, 0, 7, 3  
        ], dtype=np.int32)

        texcoord = np.tile(np.array([[0,0],[0,1],[1,0],[1,0],[0,1],[1,1]], dtype=np.float32), (6,1))
        #light = wxgl.SunLight(direction=(0.2,-0.5,-1))
        tf = lambda t : ((1,0,0,(0.05*t)%360),)
        cf = lambda t : {'azim': (0.05*t)%360}

        sch = wxgl.Scheme()
        sch.cruise(cf)
        sch.surface(vs[indices], texture='res/earth.jpg', texcoord=texcoord, transform=tf)
        
        return sch

    def draw_line(self):
        vs = np.array([
            [-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5],
            [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5]
        ], dtype=np.float32)
        data = np.arange(8)

        sch = wxgl.Scheme()
        sch.line(vs, data=data, alpha=1, method='loop')
        sch.text('2D文字Hello', [0.5,0,0], size=64)
        
        return sch

    def draw_mesh(self):
        v, u = np.mgrid[-0.5*np.pi:0.5*np.pi:30j, 0:2*np.pi:60j]
        x = np.cos(v)*np.cos(u)
        y = np.cos(v)*np.sin(u)
        z = np.sin(v)

        light_y = wxgl.SunLight(direction=(0.2, -0.5, -1))
        light_z = wxgl.SunLight(direction=(0.2, 1, -0.5))
        cf = lambda t : {'azim': (0.05*t)%360}

        sch = wxgl.Scheme()
        sch.cruise(cf)
        sch.mesh(x, z, y, data=z, light=light_y, ccw=False, fill=False)

        return sch

if __name__ == '__main__':
    app = QApplication(sys.argv) 
    win = MyWindow()
    sys.exit(app.exec())

