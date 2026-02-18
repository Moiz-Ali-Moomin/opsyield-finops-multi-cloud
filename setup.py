
from setuptools import setup, find_packages

setup(
    name="opsyield",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "fastapi",
        "uvicorn",
        "google-cloud-storage",
        "google-cloud-compute",
        "google-cloud-bigquery",
        "google-auth",
        "google-api-core",
        "azure-mgmt-compute",
        "azure-identity",
        "azure-mgmt-costmanagement",
        "azure-mgmt-resource",
        "boto3",
        "pandas",
        "pyyaml",
        "rich",
        "python-dotenv",
        "pydantic",
        "httpx",
        "tenacity",
    ],
    entry_points={
        "console_scripts": [
            "opsyield=opsyield.cli.main:main",
        ],
    },
)
