from pathlib import Path
from setuptools import setup, find_packages
import sys

sys.path.insert(0, ".")

import ichier

VERSION = ichier.__version__
DESCRIPTION = "Integrated Circuit Hierarchy"
PROJECT = "ichier"
AUTHOR = "YEUNGCHIE"

setup(
    name=PROJECT,
    version=VERSION,
    author=AUTHOR,
    description=DESCRIPTION,
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url=f"https://github.com/{AUTHOR.lower()}/{PROJECT}",
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.7",
    install_requires=Path("requirements.txt").read_text().split(),
    keywords=[
        PROJECT,
        "ic",
        "hierarchy",
        "linux",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: Unix",
    ],
)
