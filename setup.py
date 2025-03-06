from setuptools import setup, find_packages

setup(
    name="api_inceptionlabs",
    version="0.0.1",
    author="DarkPyDoor",
    author_email="futureforge.developer@gmail.com",
    description="An unofficial Python library for interacting with chat.inceptionlabs.ai API",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/DarkPyDoor/api-inceptionlabs",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "brotli>=1.0.9",
        "requests>=2.28.0",
        "playwright>=1.28.0",
        "flask[async]>=2.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'inceptionlabs-API = api_inceptionlabs.cli:main',
        ],
    },
    keywords="chat api openai-style async streaming inceptionlabs",
    license="MIT",
    include_package_data=True,
)