import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wedos_api",
    version="0.0.1",
    author="Adam Hlavacek",
    author_email="git@adamhlavacek.com",
    description="A Python client for wedos.com API",
    long_description=long_description,
    url="https://github.com/esoadamo/Python-SQLiteDB",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "requests",
    ],
)
