from distutils.core import setup

setup(
    name='cbsmr',
    version='0.1dev',
    packages=['indexer', 'proto'],
    package_dir={
        'indexer': 'indexer/',
        'proto': 'proto/',
    },
    long_description=open('README.md').read()
)

