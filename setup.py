from setuptools import setup, find_packages

setup(
    name="timemeshin",
    version="0.1.0",
    description="TimeMeshin: Deterministic Spatio-Temporal Context Engine for LLMs",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Chandramouli",
    url="https://github.com/Changmaulee/timemeshin",
    license="Apache-2.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "tabulate>=0.9.0",
        "pydantic>=1.10.0",
        "tqdm>=4.65.0"
    ],
    extras_require={
        "embeddings": ["sentence-transformers>=2.2.0"],
        "server": ["fastapi>=0.100.0", "uvicorn>=0.20.0"],
        "all": ["sentence-transformers>=2.2.0", "fastapi>=0.100.0", "uvicorn>=0.20.0", "pypdf>=3.0.0"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
