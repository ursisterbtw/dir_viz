from setuptools import setup

setup(
    name="flowcharter",
    version="0.1.0",
    description="Generate animated SVG flowcharts of directory structures",
    author="sister",
    packages=[],
    scripts=["flowcharter.py"],
    install_requires=[
        "pydot",
        "graphviz",
    ],
    entry_points={
        "console_scripts": [
            "flowcharter=flowcharter:main",
        ],
    },
    python_requires=">=3.6",
)
