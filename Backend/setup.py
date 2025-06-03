from setuptools import setup, find_packages

setup(
    name="flight_backend",
    version="0.1.0",
    packages=find_packages(include=['Backend*']),
    package_dir={"": "."},
    python_requires=">=3.8",
    install_requires=[
        "quart>=0.17.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=0.19.0",
        "quart-cors>=0.3.0",
        "pydantic>=1.8.0"
    ],
)
