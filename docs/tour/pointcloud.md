---
sort: 7
---

# 绘制点云

只需要一个点云数据文件名（支持.ply和.pcd格式），即可绘制点云模型。此外，WxGL还提供了读取点云数据文件的函数read_pcfile，返回一个PointCloudData类实例。

```python
import wxgl

app = wxgl.App(haxis='z')
app.pointcloud('res/pointcloud/3.pcd')
app.show()
```

![tour_colorbar.png](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/tour_pc.png)

