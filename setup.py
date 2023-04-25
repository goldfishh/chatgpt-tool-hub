"""Setup script for chatgpt-tool-hub"""

import os.path
import setuptools
from setuptools import setup

# The directory containing this file
HERE = os.path.abspath(os.path.dirname(__file__))

# The text of the README file
with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

__version__ = None  # set __version__ in this exec() call
exec(open('chatgpt_tool_hub/version.py').read())
# This call to setup() does all the work
setup(
    name="chatgpt-tool-hub",
    version=str(__version__),
    description=(
        "An open-source chatgpt tool ecosystem where you can combine tools "
        "with chatgpt and use natural language to do anything."
    ),
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/goldfishh/chatgpt-tool-hub",
    author="goldfishh",
    author_email="goldfish.buaa@gmail.com",
    license="MIT",
    packages=setuptools.find_packages(exclude=["*.dev", "*.dev.*", "dev.*", "*.custom_tools", "*.custom_tools.*", "custom_tools.*"]),
    include_package_data=True,
    install_requires=[
        'pydantic~=1.10.7',
        'pyopenssl',
        'pyyaml~=6.0',
        'lxml',
        'beautifulsoup4~=4.12.0',
        "tenacity~=8.2.2",
        "openai~=0.27.2",
        "tiktoken~=0.3.2",
        "arxiv",
        "wikipedia",
        "wolframalpha",
        'aiohttp~=3.8.4',
        'requests~=2.28.2',
        "google-api-python-client",
        "SQLAlchemy~=2.0.7",
        "selenium",
        "webdriver_manager",
        "rich"
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)