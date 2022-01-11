from setuptools import setup
from setuptools import find_namespace_packages

setup(
    name='smtquery',
    version='0.0.1',
    package_dir={'smtquery' : 'smtquery',
                 },
    packages=find_namespace_packages (),
    scripts=['./bin/smtquery'],
    include_package_data=True
)


