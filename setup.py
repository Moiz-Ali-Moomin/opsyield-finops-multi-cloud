
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
        "google-cloud-bigquery",
        "google-auth",
        "azure-mgmt-compute",
        "azure-identity",
        "azure-mgmt-costmanagement",
        "boto3",
        "pandas",
        "pyyaml",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "opsyield=opsyield.cli.main:main",
        ],
    },
)
