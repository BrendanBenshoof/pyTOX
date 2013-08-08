# -*- coding: utf-8 -*-
# Cerealizer
# Copyright (C) 2005-2012 Jean-Baptiste LAMY
#
# This program is free software.
# It is available under the Python licence.

import sys

if sys.version[0] == "2":
  execfile("%s.py2" % __file__.rsplit(".", 1)[0])
else:
  exec(open("%s.py3" % __file__.rsplit(".", 1)[0]).read())
