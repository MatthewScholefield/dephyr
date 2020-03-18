from setuptools import setup

setup(
    name='dephyr',
    version='0.1.0',
    description='Database dependency solver tool',
    url='https://github.com/matthewscholefield/dephyr',
    author='Matthew D. Scholefield',
    author_email='matthew331199@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='dephyr',
    packages=['dephyr'],
    install_requires=[],
    entry_points={
        'console_scripts': [
            'dephyr=dephyr.__main__:main'
        ],
    }
)
