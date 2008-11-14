# import ez_setup
# ez_setup.use_setuptools()

# to deploy, use:
#   python setup.py register sdist bdist bdist_wininst upload

from distutils.core import setup
setup(name='pysage',
      version='1.5.0',
      packages=['pysage'],
      
    # metadata for upload to PyPI
    author = "John S. Yang",
    author_email = "bigjhnny@gmail.com",
    description = "pysage",
    license = "MIT",
    keywords = "message passing, actor model, concurrency",
    url = "http://code.google.com/p/pysage/"
      )
