from setuptools import setup

setup(
    name='tty_radio',
    packages=['tty_radio'],
    version='2.0.0',
    description=(
        "Linux/OS X RESTful player for online radio streams, " +
        "like SomaFM and WCPE. Comes with a terminal UI " +
        "flavored with colors and ASCII art " +
        "and web UI for remote management."),
    author='Ryan Farley',
    author_email='rfarley3@gmu.edu',
    url='https://github.com/rfarley3/radio',
    download_url='https://github.com/rfarley3/radio/tarball/1.1.2',
    keywords=['radio', 'somafm', 'streaming', 'mpg123'],
    classifiers=[],
    install_requires=[
        'beautifulsoup4',
        'pyfiglet',
        'bottle',
        'requests',
        'click',
        'configparser',  # backport for Python 2.7
    ],
    entry_points={
        'console_scripts': [
            'radio = tty_radio.__main__:radio',
        ]
    },
    include_package_data=True,
)
