# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "insights_generator"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

#REQUIRES = [
#    "connexion==2.14.1",
#    "aiohttp_jinja2==1.5.0",
#]

setup(
    name=NAME,
    version=VERSION,
    description="Insights Generator",
    author_email="qnamakerteam@microsoft.com",
    url="",
    keywords=["Insights Generator"],
    packages=find_packages(),
    package_data={'': [
        'core/prompt_template_NL.txt',
        'core/prompt_template_key_value.txt',
        'core/prompt_template_summary.txt',
        'core/prompt_template_direct_summary.txt',
        'core/prompt_template_prepare_query.txt',
        'core/prompt_template_extract_top_tags.txt',
        'core/prompt_template_extract_statistics.txt'
        ]},
    include_package_data=True,
    long_description="""\
            This is a GPT powered code to get insights from a corpus of product reviews.
    """)
