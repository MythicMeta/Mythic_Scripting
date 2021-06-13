import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="mythic",
    version="0.0.20",
    description="Interact with Mythic C2 Framework Instances",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://docs.mythic-c2.net/scripting",
    author="@its_a_feature_",
    author_email="",
    license="BSD3",
    classifiers=[
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["mythic"],
    include_package_data=True,
    install_requires=["aiohttp", "asyncio"],
    entry_points={
    },
)
