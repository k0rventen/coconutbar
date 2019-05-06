import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(  
    name="coconutbar",
    version="0.4",
    author="k0rventen",
    description="a clean x11 system bar with bspwm integration",
    long_description=long_description,
    packages=["coconutbar"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    entry_points={
          'console_scripts': ['coconutbar=coconutbar.coconutbar:main']
    },
)