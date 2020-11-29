#!/usr/bin/env python

import argparse
import configparser
import pkg_resources
from tikka import tikka

usage = """
Provide a websocket interface for real time financial information.
The server runs securely over wss and therefore requires a certificate file and a private key file.
"""
parser = argparse.ArgumentParser(description="Tikka Server", usage=usage)
parser.add_argument('-c', '--certfile', help="server certificate file", required=True)
parser.add_argument('-k', '--keyfile', help="private key file", required=True)
parser.add_argument('-p', '--port', default=5001, type=int)
parser.add_argument('-a', '--api-key')
args = parser.parse_args()

api_key = args.api_key
if not api_key:
  config_filename = pkg_resources.resource_filename(tikka.__name__, 'config.ini')
  print(f"Loading API_KEY from file: {config_filename} ", end='')
  config = configparser.ConfigParser()
  config.read(config_filename)
  api_key = config['DEFAULT']['API_KEY']
  print(f"...done.")

print(f"Starting Tikka Server on port {args.port}")
tikka.main(api_key, args.certfile, args.keyfile, args.port)