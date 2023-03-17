---
sort: 5
---

# wxgl.Model

wxgl.Model(gltype, vshader, fshader, \*\*kwds)

WxGL模型类。

```
gltype      - GL基本图元
vshader     - 顶点着色器源码
fshader     - 片元着色器源码
kwds        - 关键字参数
    visible     - 模型可见性，默认True
    opacity     - 模型不透明，默认True
    inside      - 模型显示在视锥体内，默认True
    sprite      - 开启点精灵，默认False
    alive       - 启动渲染计时器，默认False
```

## wxgl.Model.add_shader

wxgl.Model.add_shader(shader_src, shader_type)

添加着色器。

```
shader_src  - 着色器源码
shader_type - 着色器类型
```

## wxgl.Model.add_texture

wxgl.Model.add_texture(var_name, texture)

添加纹理。

```
var_name    - 纹理在着色器中的变量名
texture     - wxgl.Texture对象
```

## wxgl.Model.set_ae

wxgl.Model.set_ae(var_name)

设置相机方位角和高度角。

```
var_name    - 相机方位角和高度角在着色器中的变量名
```

## wxgl.Model.set_argument

wxgl.Model.set_argument(var_name, var_value)

设置变量。

```
var_name    - 变量在着色器中的变量名
var_value   - 变量值或生成变量值的函数
```

## wxgl.Model.set_cam_pos

wxgl.Model.set_cam_pos(var_name)

设置相机位置。

```
var_name    - 相机位置在着色器中的变量名
```

## wxgl.Model.set_color

wxgl.Model.set_color(var_name, data)

设置顶点颜色。

```
var_name    - 顶点颜色在着色器中的变量名
data        - 顶点颜色数据
```

## wxgl.Model.set_cull_mode

wxgl.Model.set_cull_mode(mode)

设置面剔除方式。

```
mode        - 剔除的面：'front'|'back'
```

## wxgl.Model.set_fill_mode

wxgl.Model.set_fill_mode(mode)

设置填充方式。

```
mode        - 填充模式：布尔型，或'FCBC'|'FLBC'|'FCBL'|'FLBL'
```

## wxgl.Model.set_line_style

wxgl.Model.set_line_style(width=None, stipple=None)

设置线宽和线型。

```
width       - 线宽
stipple     - 线型，重复因子（整数）和模式（16位二进制）组成的元组
```

## wxgl.Model.set_model_matrix

wxgl.Model.set_model_matrix(var_name, mmatrix=None)

设置模型矩阵。

```
var_name    - 模型矩阵在着色器中的变量名
mmatrix     - 模型矩阵或生成模型矩阵的函数，None表示模型无几何变换
```

## wxgl.Model.set_normal

wxgl.Model.set_normal(var_name, data)

设置顶点法向量。

```
var_name    - 顶点法向量在着色器中的变量名
data        - 顶点法向量数据
```

## wxgl.Model.set_picked

wxgl.Model.set_picked(var_name)

设置拾取状态。

```
var_name    - 拾取状态在着色器中的变量名
```

## wxgl.Model.set_proj_matrix

wxgl.Model.set_proj_matrix(var_name, pmatrix=None)

设置投影矩阵。

```
var_name    - 投影矩阵在着色器中的变量名
mmatrix     - 投影矩阵或生成投影矩阵的函数，None表示使用当前投影矩阵
```

## wxgl.Model.set_psize

wxgl.Model.set_psize(var_name, data)

设置顶点大小。

```
var_name    - 顶点大小在着色器中的变量名
data        - 顶点大小数据
```

## wxgl.Model.set_slide

wxgl.Model.set_slide(slide)

设置幻灯片函数。

```
slide    	- 以渲染时长（ms）为参数的函数，该函数返回布尔值
```

## wxgl.Model.set_texcoord

wxgl.Model.set_texcoord(var_name, data)

设置顶点纹理坐标。

```
var_name    - 顶点纹理坐标在着色器中的变量名
data        - 顶点纹理坐标数据
```

## wxgl.Model.set_text_size

wxgl.Model.set_text_size(var_name, size)

设置2D文本的宽度和高度。

```
var_name    - 变量在着色器中的变量名
size        - 2D文本的宽度和高度
```

## wxgl.Model.set_timestamp

wxgl.Model.set_timestamp(var_name)

设置渲染时间戳（以毫秒为单位的浮点数）。

```
var_name    - 渲染时间戳在着色器中的变量名
```

## wxgl.Model.set_vertex

wxgl.Model.set_vertex(var_name, data, indices=None)

设置顶点。

```
var_name    - 顶点在着色器中的变量名
data        - 顶点数据
indices     - 顶点索引数据
```

## wxgl.Model.set_view_matrix

wxgl.Model.set_view_matrix(var_name, vmatrix=None)

设置视点矩阵。

```
var_name    - 视点矩阵在着色器中的变量名
vmatrix     - 视点矩阵或生成视点矩阵的函数，None表示使用当前视点矩阵
```

## wxgl.Model.verify

wxgl.Model.verify()

验证模型数据、检查着色器源码。该方法通常无需用户显式调用。
