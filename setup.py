import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aiogram-tonconnect",
    version="0.15.0",
    author="nessshon",
    description=(
        "aiogram-tonconnect is a user-friendly library for integrating TON Connect UI "
        "into aiogram-based Telegram bots."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nessshon/aiogram-tonconnect/",
    project_urls={
        "Bot example": "https://t.me/aiogramTONConnectBot/",
        "Source Code": "https://github.com/nessshon/aiogram-tonconnect/",
        "Usage example": "https://github.com/nessshon/aiogram-tonconnect/tree/main/example/",
    },
    packages=setuptools.find_packages(exclude=["example"]),
    package_data={"aiogram_tonconnect": ["py.typed"]},
    python_requires=">=3.10",
    install_requires=[
        "aiogram>=3.0.0,<=3.20.0",
        "cachetools>=5.3.0",
        "pillow>=10.0.0",
        "qrcode-styled>=0.2.2",
        "redis>=5.0.5",
        "tonutils>=0.4.5",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: AsyncIO",
        "Environment :: Console",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],

    keywords=(
        "aiogram, Telegram bots, TON blockchain, TON Connect, "
        "asynchronous, crypto, qrcode"
    ),
    license="MIT",
)
