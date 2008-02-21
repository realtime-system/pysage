import ez_setup
ez_setup.use_setuptools()

from distutils.core import setup
setup(name='pysage',
      version='1.1.2',
      packages=['pysage'],
      
    # metadata for upload to PyPI
    author = "John Yang",
    author_email = "bigjhnny@gmail.com",
    description = "pySage",
    license = "creative commons attribution share-alike 1.0",
    keywords = "python message publisher subscriber",
    url = "http://code.google.com/p/pysage/"
      )
