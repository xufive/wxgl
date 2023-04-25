#!/usr/bin/env python3

from OpenGL.GL import *
from wxgl.app import App
from wxgl.scheme import Scheme
from wxgl.texture import Texture
from wxgl.model import Model
from wxgl.light import BaseLight, SunLight, LampLight, SkyLight, SphereLight
from wxgl.util import font_list, color_list, cm_list, cmap

name = 'wxgl'
version = '0.9.14'
version_info = (0, 9, 14, 0)

VERTEX_SHADER                   = GL_VERTEX_SHADER
TESS_CONTROL_SHADER             = GL_TESS_CONTROL_SHADER
TESS_EVALUATION_SHADER          = GL_TESS_EVALUATION_SHADER
GEOMETRY_SHADER                 = GL_GEOMETRY_SHADER
FRAGMENT_SHADER                 = GL_FRAGMENT_SHADER
COMPUTE_SHADER                  = GL_COMPUTE_SHADER

POINTS	                        = GL_POINTS	      
LINES	                        = GL_LINES	      
LINE_STRIP	                    = GL_LINE_STRIP	  
LINE_LOOP	                    = GL_LINE_LOOP
TRIANGLES	                    = GL_TRIANGLES	  
TRIANGLE_STRIP                  = GL_TRIANGLE_STRIP
TRIANGLE_FAN                    = GL_TRIANGLE_FAN  
QUADS	                        = GL_QUADS	      
QUAD_STRIP                      = GL_QUAD_STRIP

TEXTURE_1D                      = GL_TEXTURE_1D                         
TEXTURE_1D_ARRAY                = GL_TEXTURE_1D_ARRAY                   
TEXTURE_2D                      = GL_TEXTURE_2D                         
TEXTURE_2D_ARRAY                = GL_TEXTURE_2D_ARRAY                   
TEXTURE_3D                      = GL_TEXTURE_3D                         
TEXTURE_RECTANGLE               = GL_TEXTURE_RECTANGLE                  
TEXTURE_CUBE_MAP                = GL_TEXTURE_CUBE_MAP                   
TEXTURE_CUBE_MAP_ARRAY          = GL_TEXTURE_CUBE_MAP_ARRAY             
TEXTURE_BUFFER                  = GL_TEXTURE_BUFFER
    
NEAREST                         = GL_NEAREST             
LINEAR                          = GL_LINEAR              
NEAREST_MIPMAP_NEAREST          = GL_NEAREST_MIPMAP_NEAREST
LINEAR_MIPMAP_NEAREST           = GL_LINEAR_MIPMAP_NEAREST
NEAREST_MIPMAP_LINEAR           = GL_NEAREST_MIPMAP_LINEAR
LINEAR_MIPMAP_LINEAR            = GL_LINEAR_MIPMAP_LINEAR
    
REPEAT                          = GL_REPEAT         
MIRRORED_REPEAT                 = GL_MIRRORED_REPEAT
CLAMP_TO_EDGE                   = GL_CLAMP_TO_EDGE
