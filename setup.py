from setuptools import setup, find_packages

setup(
    name="bruniai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai-agents>=0.0.11",
        "asyncio>=3.4.3",
        "python-dotenv>=1.0.0",
        "pillow>=11.2.1",
        "numpy>=2.2.4",
        "playwright>=1.42.0",
        "requests>=2.31.0",
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
)
