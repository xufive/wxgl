---
sort: 5
---

# wxgl.Texture

**wxgl.Texture(tsrc, ttype=wxgl.GL_TEXTURE_2D, \*\*kwds)**

WxGL纹理类。参数说明如下：

```
tsrc        - 图像全路径或者np.array数组
ttype       - 纹理类型，可选项
                - wxgl.TEXTURE_1D
                - wxgl.TEXTURE_2D
                - wxgl.TEXTURE_2D_ARRAY
                - wxgl.TEXTURE_3D
kwds        - 关键字参数
                level       - 纹理分级数，默认1
                min_filter  - 纹理缩小滤波器，可选项：
                                - wxgl.GL_NEAREST
                                - wxgl.GL_LINEAR
                                - wxgl.GL_NEAREST_MIPMAP_NEAREST
                                - wxgl.GL_LINEAR_MIPMAP_NEAREST
                                - wxgl.GL_NEAREST_MIPMAP_LINEAR
                                - wxgl.GL_LINEAR_MIPMAP_LINEAR
                mag_filter  - 纹理放大滤波器，可选项：
                                - wxgl.GL_NEAREST
                                - wxgl.GL_LINEAR
                s_tile      - S方向纹理铺贴方式，可选项：wxgl.GL_REPEAT|wxgl.GL_MIRRORED_REPEAT|wxgl.GL_CLAMP_TO_EDGE
                t_tile      - T方向纹理铺贴方式，可选项：wxgl.GL_REPEAT|wxgl.GL_MIRRORED_REPEAT|wxgl.GL_CLAMP_TO_EDGE
                r_tile      - R方向纹理铺贴方式，可选项：wxgl.GL_REPEAT|wxgl.GL_MIRRORED_REPEAT|wxgl.GL_CLAMP_TO_EDGE
                xflip       - 左右翻转
                yflip       - 上下翻转
```

## wxgl.Texture.create_texture

**wxgl.Texture.create_texture()**

创建纹理对象。无参数。该方法通常无需用户显式调用。



