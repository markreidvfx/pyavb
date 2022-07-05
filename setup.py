import os
import sys

from setuptools import setup, find_packages
import setuptools.command.build_py
import setuptools.command.build_ext
from distutils.extension import Extension

PROJECT_METADATA = {
    "version": "1.2.0",
    "author": 'Mark Reid',
    "author_email": 'mindmark@gmail.com',
    "license": 'MIT',
}

METADATA_TEMPLATE = """
__version__ = "{version}"
__author__ = "{author}"
__author_email__ = "{author_email}"
__license__ = "{license}"
"""

sourcefiles = [
"src/avb/_ext.pyx",
]

extensions =[]
try:
    from Cython.Build import cythonize
    if int(os.environ.get("PYAVB_BUILD_EXT", '1')):
        extensions = cythonize([Extension("avb._ext",
                                sourcefiles,
                                language="c++")])
except ImportError as e:
    print('unable to build optional cython extension')


class PyavbBuildExt(setuptools.command.build_ext.build_ext):
    """Custom Extension command"""

    def build_extensions(self):
        for ext in self.extensions:
            flags = []
            if self.compiler.compiler_type == 'msvc':
                if sys.version_info[0] == 2:
                    # If we are compiling for Python 2.7 on Windows, statically link
                    # the runtime libraries. THis will allow to compile using an
                    # msvc greater than the one used to compile Python 2.7.
                    # See See https://docs.microsoft.com/en-us/cpp/build/reference/md-mt-ld-use-run-time-library?view=msvc-160.
                    flags.append('/MT')
                flags.append('/O2')

            else:
                flags.extend(['-g0', '-O3'])

            ext.extra_compile_args = flags
        setuptools.command.build_ext.build_ext.build_extensions(self)


class AddMetadata(setuptools.command.build_py.build_py):
    """Stamps PROJECT_METADATA into __init__ files."""

    def run(self):
        setuptools.command.build_py.build_py.run(self)

        if self.dry_run:
            return

        target_file = os.path.join(self.build_lib, 'avb', "__init__.py")
        source_file = os.path.join(os.path.dirname(__file__), 'src', 'avb', "__init__.py")

        # get the base data from the original file
        with open(source_file, 'r') as fi:
            src_data = fi.read()

        # write that + the suffix to the target file
        with open(target_file, 'w') as fo:
            fo.write(src_data)
            fo.write(METADATA_TEMPLATE.format(**PROJECT_METADATA))

setup(
    name='pyavb',
    description='A python module for the reading and writing Avid Bin Files files.',
    url='https://github.com/markreidvfx/pyavb',

    project_urls={
        'Source':
            'https://github.com/markreidvfx/pyavb',
        'Documentation':
            'http://pyavb.readthedocs.io',
        'Issues':
            'https://github.com/markreidvfx/pyavb/issues',
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Video :: Display',
        'Topic :: Multimedia :: Video :: Non-Linear Editor',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
        'Natural Language :: English',
    ],

    keywords='film tv editing editorial edit non-linear edl time',

    platforms='any',

    packages=['avb'],
    package_dir={'': 'src'},

    cmdclass={
        'build_py': AddMetadata,
        'build_ext': PyavbBuildExt
    },
    ext_modules = extensions,
    extras_require= {'cython' : ['cython']},
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, !=3.6.*',

    **PROJECT_METADATA
)
