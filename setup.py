
from setuptools import setup, find_packages

setup(
    name="opsyield",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "fastapi",
        "uvicorn",
        "google-cloud-storage",
        "google-cloud-compute",
        "azure-mgmt-compute",
        "boto3",
        "pandas"
    ],
    entry_points={
        "console_scripts": [
            "opsyield=opsyield.cli.main:cli",
        ],
    },
)
