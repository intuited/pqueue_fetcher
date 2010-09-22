try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from textwrap import dedent, fill

def format_desc(desc):
    return fill(dedent(desc), 200)

def format_classifiers(classifiers):
    return dedent(classifiers).strip().split('\n')

def split_keywords(keywords):
    return dedent(keywords).strip().replace('\n', ' ').split(' ')

def file_contents(filename):
    with open(filename) as f:
        return f.read()

setup(
    name = "pqueue_fetcher",
    version = "0.0.6",
    author = "Ted Tibbetts",
    author_email = "intuited@gmail.com",
    url = "http://github.com/intuited/pqueue_fetcher",
    description = format_desc("""
        Implements a priority-queue-based fetching system.
        """),
    long_description = file_contents('README.rst'),
    classifiers = format_classifiers("""
        Development Status :: 2 - Pre-Alpha
        Intended Audience :: Developers
        License :: OSI Approved :: MIT License
        Operating System :: OS Independent
        Programming Language :: Python
        Programming Language :: Python :: 2
        Topic :: Software Development :: Libraries :: Python Modules
        Topic :: Utilities
        """),
    keywords = split_keywords("""
        threading multithreading networking queue priority_queue
        """),
    install_requires = ['terminable_thread'],
    packages = ['pqueue_fetcher', 'pqueue_fetcher.test'],
    package_dir = {'pqueue_fetcher': ''},
    test_suite = 'pqueue_fetcher.test.suite',
    )
