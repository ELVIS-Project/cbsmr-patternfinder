from distutils.core import setup

setup(
    name='cbsmr',
    version='0.1dev',
    packages=['proto', 'smrpy'],
    package_dir={
        'proto': 'proto/',
        'smrpy': 'smrpy/',
    },
)

