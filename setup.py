# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r", encoding="utf8") as fp:
    long_description = fp.read()

setuptools.setup(
    name="wxgl",
    version="0.8.4",
    author="xufive",
    author_email="xufive@gmail.com",
    description="A 3d library based pyOpenGL.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xufive/wxgl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    data_files = [
        ('lib/site-packages/wxgl/res', [
            'wxgl/res/info.png', 
            'wxgl/res/tb_config_32.png', 
            'wxgl/res/tb_hide_32.png', 
            'wxgl/res/tb_show_32.png', 
            'wxgl/res/tb_play_32.png', 
            'wxgl/res/tb_stop_32.png', 
            'wxgl/res/tb_restore_32.png', 
            'wxgl/res/tb_save_32.png', 
            'wxgl/res/tb_style_32.png',
            'wxgl/res/wxplot.ico'
        ])
    ],
    install_requires = [ 
        'pyopengl>=3.1.5',
        'numpy>=1.20.2', 
        'scipy>=1.4.1', 
        'matplotlib>=3.1.2', 
        'wxpython>=4.0.7.post2',
        'pillow>=8.2.0',
        'freetype-py>=2.2.0'
    ]
)
