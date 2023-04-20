# 更新日志

## [0.9.12] - 2023-04-20

### 新增

* App类新增tinfo和cinfo属性，分别表时间信息格式化函数和相机位置信息格式化函数。WxScene类和qtScene类的实例在刷新画布时调用这个函数（如果不是None的话）并更新UI的状态栏。
* App类新增info方法，用于设tinfo和cinfo属性。
* 新增版本更新日志。

<br>

## [0.9.11] - 2023-04-16

### 新增

* Scheme类新增lines方法，用于绘制多条线段。
* Scheme.line方法新增loop参数，用于绘制首尾闭合的连续线段。

### 修复

* 修复Scheme.colorbar方法的cm参数传入除'viridis'外的其他调色板都报错的问题。
* 修改App.savefig方法的outfile参数不含文件路径时报错的问题。

### 变更

* 将Scheme.line方法的stipple参数类型从元组改为字符串，选项包活：'solit'、'dashed'、'doted'和'dash-dot'。

### 删除

* 弃用Scheme.line方法的pair参数。
