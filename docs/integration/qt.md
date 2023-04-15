---
sort: 2
---

# 与PyQt集成

场景类wxgl.qtscene.QtScene是PyQt6.QtOpenGLWidgets.QOpenGLWidget的派生类，因此可以无缝地在PyQt6中使用该类。三维绘图功能封装在wxgl.Scheme中，只需要将一个Scheme类实例传到场景类中即可显示三维绘图结果。

```python
import sys
import os, sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog
from PyQt6.QtCore import Qt
import wxgl

class MyWindow(QWidget):
    """从QWidget类派生的桌面应用程序窗口类"""
    
    def __init__(self):
        """构造函数"""
        
        super().__init__()
        
        self.setWindowTitle('在PyQt中使用WxGL')
        self.setGeometry(0, 0, 640, 480) # 设置窗位置和大小
        
        self.scene = wxgl.qtscene.QtScene(self, self.draw(), fovy=40)
        self.visible = True

        btn_home = QPushButton('复位')
        btn_animate = QPushButton('启动/停止')
        btn_visible = QPushButton('隐藏/显示')
        btn_save = QPushButton('保存')

        vbox = QVBoxLayout() 
        vbox.addSpacing(40)
        vbox.addWidget(btn_home)
        vbox.addSpacing(40)
        vbox.addWidget(btn_animate)
        vbox.addSpacing(40)
        vbox.addWidget(btn_visible)
        vbox.addSpacing(40)
        vbox.addWidget(btn_save)
        vbox.addStretch(1)

        hbox = QHBoxLayout()
        hbox.setSpacing(20)
        hbox.setContentsMargins(10,10,20,10)
        hbox.addWidget(self.scene, stretch=1)
        hbox.addLayout(vbox)
        
        self.setLayout(hbox)
        self.show()

        btn_home.clicked.connect(self.on_home)
        btn_animate.clicked.connect(self.on_animate)
        btn_visible.clicked.connect(self.on_visible)
        btn_save.clicked.connect(self.on_save)

    def closeEvent(self, evt):
        self.scene.clear_buffer()

    def draw(self):
        """绘制网格球和圆柱的组合体"""

        tf = lambda t : ((0, 1, 0, (0.03*t)%360), )
        sch = wxgl.Scheme()
        sch.sphere((0,0,0), 1, fill=False)
        sch.cylinder((-1.2,0,0), (1.2,0,0), 0.3, color='cyan', transform=tf, name='cudgel')
        sch.circle((-1.2,0,0), 0.3, vec=(-1,0,0), color='cyan', transform=tf, name='cudgel')
        sch.circle((1.2,0,0), 0.3, vec=(1,0,0), color='cyan', transform=tf, name='cudgel')
        sch.axes()
        
        return sch

    def on_home(self):
        """点击复位按钮"""

        self.scene.home()

    def on_animate(self):
        """点击启动/停止按钮"""

        self.scene.pause()

    def on_visible(self):
        """点击隐藏/显示按钮"""

        self.visible = not self.visible
        self.scene.set_visible('cudgel', self.visible)

    def on_save(self):
        """点击保存按钮"""

        self.scene.stop_idle()
        im = self.scene.get_buffer()

        file_type = 'PNG files (*.png);;JPEG file (*.jpg)'
        fname, fext = QFileDialog.getSaveFileName(self, '保存文件', directory=os.getcwd(), filter=file_type)
        name, ext = os.path.splitext(fname)

        if name:
            if ext != '.png' and ext != '.jpg':
                ext = '.png' if fext == 'PNG files (*.png)' else '.jpg'

            if ext == '.jpg':
                im.convert('RGB').save('%s%s'%(name, ext))
            else:
                im.save('%s%s'%(name, ext))

        self.scene.start_idle()

if __name__ == '__main__':
    app = QApplication(sys.argv) 
    win = MyWindow()
    sys.exit(app.exec())
```

![qt.png](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/qt.png)

