from setuptools import setup, find_packages

setup(
    name='xbox_notify',
    version='1.0',
    author='Antonio Davide Cali',
    requires=["telethon", "requests", "apscheduler", "dynaconf"],
    packages=find_packages()
)
