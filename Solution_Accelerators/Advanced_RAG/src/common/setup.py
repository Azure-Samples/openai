from setuptools import setup, find_packages

setup(
    name='common',
    version='0.1.0', 
    description='A shared library of common functionality',
    # long_description=open('README.md').read(),
    # long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        # Todo : Add common specific dependencies/requirements.txt here
        # For example: 'requests>=2.25.1',
    ],
    python_requires='>=3.10',
)
