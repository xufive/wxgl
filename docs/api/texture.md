---
sort: 4
---

# wxgl.Texture

wxgl.Texture(tsrc, ttype=wxgl.GL_TEXTURE_2D, \*\*kwds)

WxGL纹理类。

```
tsrc        - 图像文件，或图像文件列表，或np.array数组
ttype       - 纹理类型，可选项
    - wxgl.TEXTURE_1D
    - wxgl.TEXTURE_2D（默认）
    - wxgl.TEXTURE_2D_ARRAY
    - wxgl.TEXTURE_3D
kwds        - 关键字参数
    level       - 纹理分级数，默认1
    min_filter  - 纹理缩小滤波器，可选项：
        - wxgl.GL_NEAREST
        - wxgl.GL_LINEAR
        - wxgl.GL_NEAREST_MIPMAP_NEAREST（默认）
        - wxgl.GL_LINEAR_MIPMAP_NEAREST
        - wxgl.GL_NEAREST_MIPMAP_LINEAR
        - wxgl.GL_LINEAR_MIPMAP_LINEAR
    mag_filter  - 纹理放大滤波器，可选项：
        - wxgl.GL_NEAREST
        - wxgl.GL_LINEAR（默认）
    s_tile      - S方向纹理铺贴方式，可选项：wxgl.GL_REPEAT（默认）|wxgl.GL_MIRRORED_REPEAT|wxgl.GL_CLAMP_TO_EDGE
    t_tile      - T方向纹理铺贴方式，可选项：wxgl.GL_REPEAT（默认）|wxgl.GL_MIRRORED_REPEAT|wxgl.GL_CLAMP_TO_EDGE
    r_tile      - R方向纹理铺贴方式，可选项：wxgl.GL_REPEAT（默认）|wxgl.GL_MIRRORED_REPEAT|wxgl.GL_CLAMP_TO_EDGE
    xflip       - 左右翻转，默认False
    yflip       - 上下翻转，默认False
```

## wxgl.Texture.create_texture

wxgl.Texture.create_texture()

创建纹理对象。该方法通常无需用户显式调用。



