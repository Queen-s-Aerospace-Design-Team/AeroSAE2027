from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'mcu_pi'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'comms'),
            ['mcu_pi/comms/test_vectors.json']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='qadt',
    maintainer_email='jacob.wong1606@gmail.com',
    description='Pi-side serial bridge between a Raspberry Pi 5 and an Arduino Nano',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'serial_bridge_node = mcu_pi.serial_bridge_node:main',
        ],
    },
)
