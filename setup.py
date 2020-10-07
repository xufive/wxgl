# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wxgl",
    version="0.6.2",
    author="xufive",
    author_email="xufive@gmail.com",
    description="A 3d library based pyOpenGL.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xufie/wxgl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    data_files = [
        ('lib/site-packages/wxgl/res', [
            'wxgl/res/tb_args.png', 
            'wxgl/res/tb_axes.png', 
            'wxgl/res/tb_grid.png', 
            'wxgl/res/tb_restore.png', 
            'wxgl/res/tb_save.png',
            'wxgl/res/wxplot.ico'
        ])
    ],
    install_requires = [
        'numpy>=1.18.2', 
        'scipy>=1.4.1', 
        'matplotlib>=3.1.2', 
        'wxpython>=4.0.7.post2', 
        'pyopengl>3.1.3b2'
    ]
)
