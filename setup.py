from setuptools import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="neptuneapex-hass-mqtt",
    version="1.0",
    description="Feed data from a neptune apex into HASS via MQTT",
    license='GPL',
    packages=['neptuneapex-hass-mqtt'],
    author='Tim Rightnour',
    author_email='the@garbled.one',
    url='https://github.com/garbled1/neptuneapex-hass-mqtt',
    project_urls={
        'Gitub Repo': 'https://github.com/garbled1/neptuneapex-hass-mqtt',
    },
    install_requires=[
        'paho-mqtt',
        'requests',
        'homeassistant-mqtt-binding',
    ],
    python_requires='>3.9',
    long_description=long_description,
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            'neptuneapex-hass-mqtt=neptuneapex-hass-mqtt.__main__:main'
        ]
    }
)
