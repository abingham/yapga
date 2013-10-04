import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name='yapga',
    version='1',
    packages=find_packages(),

    # metadata for upload to PyPI
    author='Austin Bingham',
    author_email='austin.bingham@gmail.com',
    description="Yet Another Python Gerrit API",
    license='MIT',
    keywords='gerrit',
    url='http://github.com/abingham/yapga',
    # download_url = '',
    long_description='An API for working with Gerrit '
                     'from Python via the REST API.',
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    platforms='any',
    setup_requires=[],
    install_requires=[
        'baker',
        'matplotlib',
        'numpy',
    ],

    entry_points={
        'console_scripts': [
            #'yapga = yapga.app:main',
        ],
    },
)
