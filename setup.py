from setuptools import setup, find_packages

setup(
    name="wsi_viewer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0,<0.69.0",
        "uvicorn[standard]>=0.15.0,<0.16.0",
        "python-multipart>=0.0.5,<0.0.6",
        "aiofiles>=0.7.0,<0.8.0",
        "openslide-python>=1.1.2",
        "Pillow>=8.3.2",
        "numpy>=1.21.2",
        "websockets>=10.0",
        "tifffile>=2023.3.15",
        "opencv-python>=4.5.0",
        "python-multipart>=0.0.5"
    ],
    entry_points={
        'console_scripts': [
            'wsi-viewer=wsi_viewer.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'wsi_viewer': [
            'api/**/*',
            'frontend/**/*',
            'static/**/*'
        ],
    },
    python_requires=">=3.7",
    author="DSGM Team",
    description="A WSI (Whole Slide Image) viewer module",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
