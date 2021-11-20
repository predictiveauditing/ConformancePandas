import setuptools
import os
# os.system('pip install git+https//github.com/timbaessler/ConformancePandas.git@master')

setuptools.setup(name='conformancepandas',
				 version="0.0.1",
				 author="Tim Bäßler",
				 author_email="tim.baessler@web.de",
				 url="https://github.com/timbaessler/ConformancePandas",
				 packages=["conformancepandas",
						   "conformancepandas.conformance_checking",
						   "conformancepandas.util"],
				 install_requires=["pm4py"])
