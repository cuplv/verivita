from setuptools import setup

setup(
   name='cbverifier',
   version='2.0',
   description='Dynamic verification for Android Apps',
   author='Sergio Mover',
   author_email='sergio.mover@colorado.edu',
   packages=['cbverifier'],
   install_requires=['pysmt'],
    entry_points={
        'console_scripts': [
            'cbverifier = cbverifier.driver:main'
        ],
    },
)
