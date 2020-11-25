#!/usr/bin/env python

import argparse
from tikka import tikka

usage = """
Provide a websocket interface for real time financial information.
The server runs securely over wss and therefore requires a certificate file and a private key file.
"""
parser = argparse.ArgumentParser(description="Tikka Server", usage=usage)
parser.add_argument('-c', '--certfile', help="server certificate file", required=True)
parser.add_argument('-k', '--keyfile', help="private key file", required=True)
parser.add_argument('-p', '--port', default=5001, type=int)
args = parser.parse_args()

print(f"Starting Tikka Server on port {args.port}")
tikka.main(args.certfile, args.keyfile, args.port)