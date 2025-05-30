from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="bruniai",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src", include=["*"]),
    include_package_data=True,
    install_requires=[
        "openai",
        "python-dotenv",
        "playwright",
        "pillow",
        "numpy",
        "aiohttp",
        "typing_extensions>=4.0.0",
    ],
    python_requires=">=3.10",
    author="Joao Garin",
    author_email="joao@nevinbuilds.com",
    description="AI-powered visual regression testing tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/nevinbuilds/bruniai",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "bruniai=src.runner.__main__:run_main",
        ],
    },
)
