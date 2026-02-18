from setuptools import setup, find_packages

setup(
    name="opsyield",
    version="0.1.0",
    description="OpsYield - Multi-cloud cost optimization, analytics, and governance platform for AWS, Azure, and GCP",
    author="Moiz Ali Moomin",
    author_email="moizalimoomin.53@gmail.com",
    url="https://github.com/yourusername/opsyield",  # update this
    license="MIT",

    packages=find_packages(),

    include_package_data=True,

    package_data={
        "opsyield.web.templates": ["*.html"],
    },

    install_requires=[
        "click>=8.0.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.25.0",
        "google-cloud-storage>=2.16.0",
        "google-cloud-compute>=1.19.0",
        "google-cloud-bigquery>=3.25.0",
        "google-auth>=2.29.0",
        "google-api-core>=2.19.0",
        "azure-mgmt-compute>=30.0.0",
        "azure-identity>=1.16.0",
        "azure-mgmt-costmanagement>=4.0.0",
        "azure-mgmt-resource>=23.0.0",
        "boto3>=1.34.0",
        "pandas>=2.2.0",
        "pyyaml>=6.0.0",
        "rich>=13.7.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.6.0",
        "httpx>=0.27.0",
        "tenacity>=8.2.0",
    ],

    entry_points={
        "console_scripts": [
            "opsyield=opsyield.cli.main:main",
        ],
    },

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],

    python_requires=">=3.10",

    keywords=[
        "cloud",
        "aws",
        "azure",
        "gcp",
        "devops",
        "finops",
        "cost-optimization",
        "cloud-cost",
        "multi-cloud",
        "kubernetes",
    ],
)
