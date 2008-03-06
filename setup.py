import ez_setup
ez_setup.use_setuptools()

from distutils.core import setup
setup(name='pysage',
      version='1.2.1',
      packages=['pysage'],
      
    # metadata for upload to PyPI
    author = "John S. Yang",
    author_email = "bigjhnny@gmail.com",
    description = "pysage",
    license = "MIT",
    keywords = "distributed python publisher-subscriber, message-passing, object management library",
    url = "http://code.google.com/p/pysage/"
      )
