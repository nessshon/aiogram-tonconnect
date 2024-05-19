import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aiogram-tonconnect",
    version="0.13.6",
    author="nessshon",
    description="TON Connect UI for aiogram bots.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=["example", "docs"]),
    install_requires=[
        "aiofiles",
        "aiogram",
        "aiohttp",
        "cachetools",
        "pillow",
        "pydantic",
        "pytonconnect",
        "pytoniq-core",
        "qrcode-styled",
        "redis",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    url="https://github.com/nessshon/aiogram-tonconnect/",
    project_urls={
        "Documentation": "https://nessshon.github.io/aiogram-tonconnect/",
        "Bot example": "https://t.me/aiogramTONConnectBot/",
    },
)
