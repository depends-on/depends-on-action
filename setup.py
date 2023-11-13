import json

from setuptools import setup

setup(
    name="depends-on",
    description="A Python library to manage dependencies between changes.",
    long_description_content_type="text/markdown",
    long_description=open("README.md").read(),
    author="The Depends-On Team",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Public License v3 (GPLv3)",
    ],
    version=json.load(open("package.json"))["version"],
    packages=["depends_on"],
    scripts=["depends_on_stage2", "depends_on_stage3"],
)
