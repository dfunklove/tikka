#!/usr/bin/env python

"""
Transform financial symbol listings from the FinnHub format to Fuse.js format.
"""

import sys
import json

if (len(sys.argv) < 2):
  print(f"usage: {sys.argv[0]} filename")
  sys.exit()

with open(sys.argv[1]) as infile:
  data = infile.read()
  data = json.loads(data)
  for chunk in data:
    print(f'{{"value": "{chunk["symbol"]}", "text": "{chunk["displaySymbol"]}{" | " if chunk["description"] else ""}{chunk["description"]}"}},')
