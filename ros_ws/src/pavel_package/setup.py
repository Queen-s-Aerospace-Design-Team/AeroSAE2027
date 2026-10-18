from setuptools import find_packages, setup

package_name = 'pavel_package'

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
    maintainer='qadt',
    maintainer_email='pavel.timofeev2008@gmail.com',
    description='Package for the onboarding project by Pavel Timofeev',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'pavel_node = pavel_package.pavel_node:main',
            'talker = pavel_package.publisher_member_function:main',
            'listener = pavel_package.subscriber_member_function:main',
        ],
    },
)
