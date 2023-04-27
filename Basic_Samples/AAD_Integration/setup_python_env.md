# Python Environment Setup

This document describes the packages you need to install to use the Azure OpenAI (AOAI) API from Python.  These packages are included in the `requirements.txt` file in this repository.

## Virtual Environment
We recommend setting up a Python virtual environment to run the samples.  This will allow you to install the required packages without affecting your system Python installation.  We assume that the reader is familiar with Python and setting up virtual environments.  Installing Python and setting up a virtual environment is beyond the scope of this document.  

The examples are tested with Python 3.10.6 using Miniconda on WSL2.

## Packages
The following packages are required to use the AOAI API from Python and included in [`requirements.txt`](requirements.txt):

1. `azure-identity` - This package provides the `DefaultAzureCredential` class that is used to authenticate with Azure Active Directory (AAD).  This package is part of the Azure SDK for Python.  See [Azure Identity SDK for Python](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python).
2. `openai` - This package provides the `openai` class that is used to call the AOAI API.  This package is part of the OpenAI Python SDK.  See [OpenAI Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python).

In addition, the following packages are required to run the samples:

3. `jupyter` - This package provides the `jupyter` command that is used to run Jupyter notebooks.  See [Jupyter](https://jupyter.org/).

## Tested Versions
For reference, the tested version of packages are captured in [`pip-freeze.txt`](pip-freeze.txt).
