# WxGL

基于PyOpenGL的三维数据展示库，以wx为显示后端。WxGL的容器名为WxGLScene，称为场景。每个场景可以使用addRegion()生成多个WxGLRegion对象，称为视区。在视区内可以创建模型，每个模型由一个或多个组件构成——所谓组件，可以理解为子模型。WxGLRegion提供了以下方法创建模型或组件：

* WxGLRegion.drawText() 绘制文本
* WxGLRegion.drawPoint() 绘制点
* WxGLRegion.drawLine() 绘制线段
* WxGLRegion.drawSurface() 绘制曲面
* WxGLRegion.drawMesh() 绘制网格
* WxGLRegion.drawVolume() 绘制体数据
* WxGLRegion.drawAxes() 绘制坐标
* WxGLRegion.drawColorBar() 绘制绘制colorBar
