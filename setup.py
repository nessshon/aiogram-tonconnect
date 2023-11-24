import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aiogram-tonconnect",
    version="0.0.4",
    author="nessshon",
    description="aiogram-tonconnect seamlessly integrates TonConnect into aiogram bots, "
                "simplifying wallet connections and transactions with a ready UI. "
                "Effortless middleware for enhancing your aiogram-based bots.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=["example"]),
    python_requires='>=3.7, <3.11',
    install_requires=[
        "aiofiles>=23.1.0",
        "aiogram>=3.1.1",
        "aiohttp>=3.8.6",
        "cachetools>=5.3.2",
        "pydantic==2.3.0",
        "pytonconnect==0.3.0",
        "pytoniq-core>=0.1.14",
        "redis>=5.0.1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    url="https://github.com/nessshon/aiogram-tonconnect/",
    project_urls={
        "Documentation": "https://nessshon.github.io/aiogram-tonconnect/",
        "Bot example": "https://t.me/aiogramTONConncetBot/",
    },
)
