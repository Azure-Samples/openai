# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from setuptools import setup, find_packages

setup(
    name="common",
    version="0.1.0",
    description="A shared library of common functionality",
    packages=find_packages(),
    install_requires=[
        # Todo : Add common specific dependencies/requirements.txt here
        # For example: 'requests>=2.25.1',
    ],
    python_requires=">=3.12",
)
