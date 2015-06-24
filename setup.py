#!/usr/bin/env python

from distutils.core import setup

setup(name='TES Arena Utils',
      version='1.0',
      description='TES Arena Resource Utility Library',
      author='Oleksii Kuchma',
      author_email='nod3pad@gmail.com',
      url='https://github.com/Nodepad/python-tes-arena-resource-lib',
      packages=['TESAExport'],
      package_data={'TESAExport': ['db.xml']}
     )
