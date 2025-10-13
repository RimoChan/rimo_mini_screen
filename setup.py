import setuptools


setuptools.setup(
    name='rimo_mini_screen',
    version='1.1.0',
    author='RimoChan',
    author_email='the@librian.net',
    description='RimoChan util.',
    long_description='喵喵喵！',
    long_description_content_type='text/markdown',
    url='https://github.com/RimoChan/rimo_mini_screen',
    packages=['rimo_mini_screen'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'pyserial~=3.5',
        'numpy>=1.24',
        'pillow>=10.0',
    ],
    python_requires='>=3.9',
)
