from setuptools import find_packages, setup

package_name = 'ly_pubsub'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lucas Yaskowich',
    maintainer_email='lyaskowich@gmail.com',
    description='Examples of minimal pub/sub using rclpy',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'talker = ly_pubsub.publisher_member_function:main',
            'listener = ly_pubsub.subscriber_member_function:main',
        ],
    },
)
