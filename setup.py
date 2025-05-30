from pathlib import Path
from setuptools import setup, find_packages
import sys
import re

sys.path.insert(0, str(Path(__file__).parent))

import ichier

VERSION = ichier.__version__
DESCRIPTION = "Integrated Circuit Hierarchy"
PROJECT = "ichier"
AUTHOR = ichier.__author__
EMAIL = ichier.__email__
URL = ichier.__url__

readme = re.sub(
    r"(!\[.*?\]\()(\./)?",
    lambda m: m.group(1) + URL + "/raw/main/",
    Path("README.md").read_text("utf-8"),
)

setup(
    name=PROJECT,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=readme,
    long_description_content_type="text/markdown",
    url=URL,
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.8",
    install_requires=Path("requirements.txt").read_text("utf-8").split(),
    extras_require={
        "full": ["ipython", "rich"],
    },
    keywords=[
        PROJECT,
        "verilog",
        "spice",
        "cdl",
        "ic",
        "hierarchy",
        "linux",
    ],
    entry_points={
        "console_scripts": [
            "ichier=ichier._main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: Unix",
    ],
)
