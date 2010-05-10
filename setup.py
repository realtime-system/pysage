# import ez_setup
# ez_setup.use_setuptools()

# to deploy, use:
#   (does not work ) python setup.py register sdist bdist bdist_wininst upload
#   python setup.py register sdist upload
# version numbers:
#   the version number here is the version number pypi uses, you have to bump it up if upload error occurs
#   the version number under pysage/__init__.py is the real pysage version number

from distutils.core import setup
setup(name='pysage',
      version='1.5.4',
      packages=['pysage'],
      
    # metadata for upload to PyPI
    author = "John S. Yang",
    author_email = "bigjhnny@gmail.com",
    description = "pysage",
    license = "MIT",
    keywords = "message passing, actor model, concurrency",
    url = "http://code.google.com/p/pysage/"
      )
