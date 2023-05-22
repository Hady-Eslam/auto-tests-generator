from setuptools import setup, find_packages

setup(
    name='auto_tests_generator',
    version='0.3.3',
    description='Auto Tests Generator',
    url='https://github.com/Hady-Eslam/auto-tests-generator.git',
    author='Hady Eslam',
    author_email='abdoaslam000@gmail.com',
    license='Apache',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'isort==4.3.21',
        'black==23.1.0',
        'autoflake==1.7.8',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
