#!/usr/bin/env python3

import setuptools

with open("README.md", "r", encoding="utf8") as fp:
    long_description = fp.read()

setuptools.setup(
    name="wxgl",
    version="0.9.8",
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
    install_requires = [ 
        'pyopengl>=3.1.5',
        'numpy>=1.20.2', 
        'matplotlib>=3.1.2',
        'pyqt6>=6.3.0', 
        'pillow>=8.2.0',
        'freetype-py>=2.3.0',
        'imageio>=2.22.0',
        'imageio-ffmpeg>=0.4.8',
        'webp>=0.1.5'
    ]
)
