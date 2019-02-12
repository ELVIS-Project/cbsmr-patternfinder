from distutils.core import setup

setup(
    name='scmr_search',
    version='0.1dev',
    packages=['indexers'],
    package_dir={'indexers': 'indexers/'},
    package_data={'indexers': ['tests/leiermann*']},
    long_description=open('README.md').read()
)

