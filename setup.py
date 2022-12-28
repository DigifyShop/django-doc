import os
import re
from setuptools import setup


def version() -> str:
    with open(os.path.join('django_doc/__init__.py')) as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read()).group(1)


_version = version()
_long_description = open('README.md').read()

setup(
    name='django-doc',
    version=_version,
    python_requires='>=3.10',
    author='Digify',
    author_email='a.rajabnejad@digikala.com',
    keywords='django automate documentation',
    url='https://github.com/digifyshop/django-doc',
    description='Automate Django RestFramework Documentation',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    license='MIT',
    package_data={},
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
    ],
    install_requires=[
    ],
)
