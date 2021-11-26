import setuptools
import os

setuptools.setup(name='conformancelabeler',
				 version="0.0.1",
				 author="Tim Bäßler",
				 author_email="tim.baessler@web.de",
				 url="https://github.com/timbaessler/conformance-labeler",
				 packages=["conformancelabeler",
						   "conformancelabeler.conformance_checking",
						   "conformancelabeler.util"],
				 install_requires=["pm4py", "pandas"])
