import setuptools
import os
# os.system('pip install git+https//github.com/timbaessler/ConformancePandas.git@master')

setuptools.setup(name='conformancelabeler',
				 version="0.0.1",
				 author="Tim Bäßler",
				 author_email="tim.baessler@web.de",
				 url="https://github.com/timbaessler/ConformancePandas",
				 packages=["conformancelabeler"],
				 install_requires=["pm4py", "pandas"])
