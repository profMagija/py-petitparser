from setuptools import setup, find_packages

from petitparser import __version__

with open('README.md') as f:
    long_description = f.read()

setup(
    name='petitparser',
    version=__version__,
    description='PetitParser implemented in Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/profMagija/py-petitparser',
    author='Nikola Bebić',
    author_email='nikola.bebic99@gmail.com',
    license='MIT',
    packages=find_packages(include=['petitparser', 'petitparser.*']),
    install_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
    ],
)
