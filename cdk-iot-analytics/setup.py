import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="cdk_sap_blog",
    version="0.0.1",

    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "cdk_sap_blog"},
    packages=setuptools.find_packages(where="cdk_sap_blog"),

    install_requires=[
        "aws_cdk.core",
        "aws_cdk.aws_s3",
        "aws_cdk.aws_sns",
        "aws_cdk.aws_iot",
        "aws_cdk.aws_iam",
        "aws_cdk.aws_lambda",
        "aws_cdk.aws_dynamodb",
        "aws_cdk.aws_iotevents",
        "aws_cdk.aws_iotanalytics",
        "aws_cdk.aws_secretsmanager",
        "click",
        "pyOpenSSL",
        "requests",
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
