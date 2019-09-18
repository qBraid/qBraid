from setuptools import setup, find_packages

setup(name='qbraid',
      version='0.1',
      description='Platform for accessing quantum computers',
      url='https://github.com/kanavsetia/qBraid',
      author='qbraid developers',
      author_email='noreply@qBraid.com',
      license='Restricted',
      packages=find_packages(where='src'),
      package_dir={'':'src'},
      zip_safe=False)