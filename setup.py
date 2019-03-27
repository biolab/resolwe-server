from setuptools import find_packages, setup

# Use codecs' open for a consistent encoding
from codecs import open
from os import path

base_dir = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(base_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

requirements = ['requirements.txt']
INSTALL_REQUIRES = sorted(
    set(
        line.partition('#')[0].strip()
        for req_file in (path.join(base_dir, req_file) for req_file in requirements)
        for line in open(req_file)
    )
    - {''}
)


VERSION = '0.0.1'

setup(
    name='resolwe-server',
    description='Resolwe based server',
    long_description=long_description,
    url='https://github.com/biolab/resolwe-server',
    author='Bioinformatics Laboratory, FRI UL',
    author_email='info@biolab.si',
    license='Apache License (2.0)',
    version=VERSION,
    # exclude tests from built/installed package
    packages=find_packages(exclude=['tests', 'tests.*', '*.tests', '*.tests.*']),
    package_data={
        'resolwe_server': [
            'descriptors/*.yml',
            'processes/**/*.yml',
            'processes/**/*.py',
            'tools/*.py',
            'tools/*.R',
            'tools/*.sh',
        ]
    },
    install_requires=INSTALL_REQUIRES,
    python_requires='>=3.6, <3.7',
    extras_require={},
    classifiers=[
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='orange resolwe server bioinformatics singlecell dataflow django',
)
