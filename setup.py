import re

import setuptools

with open("src/cli_scheduler/__init__.py", "rt", encoding="utf8") as f:
    version = re.search(r"__version__ = \"(.*?)\"", f.read()).group(1)

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="DefiServicesLib",
    version=version,
    author="Viet-Bang Pham",
    author_email="phamvietbang2965@gmail.com",
    description="Calculate apy, apr, and wallet information,... in decentralized applications.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hoangthanhlamm/python-cli-scheduler",
    project_urls={"Bug Tracker": "https://github.com/hoangthanhlamm/python-cli-scheduler", },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[],
)