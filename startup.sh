#!/bin/sh
tikka_server.py -c fullchain.pem -k privkey.pem > startup.log 2>&1
