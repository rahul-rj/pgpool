#!/usr/bin/python

# Start script for the pgpool service.

from __future__ import print_function

import sys
import os
import time
import subprocess

NODE = sys.argv[1]
# Time script needs to wait before executing the repair command
WAIT_TIME=15
time.sleep(WAIT_TIME)
os.environ["PCPPASSFILE"] = '/etc/pgpool-II/.pcppass'
subprocess.Popen('/usr/bin/pcp_attach_node -h localhost -p 9898 -U postgres -n {} -w'.format(NODE), shell=True)
