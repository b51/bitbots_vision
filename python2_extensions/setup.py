from distutils.core import setup, Extension

module1 = Extension('VisionExtensions',
                    sources=['vision_extensions.cpp'],
                    extra_compile_args=["-std=c++14"],
                    # extra_compile_args=["-O0", "-g"],
                    )

setup(name='Bit-Bots-Extensions',
      version='1.0',
      description='This is a package with python extensions for the Hamburg Bit-Bots',
      ext_modules=[module1])
