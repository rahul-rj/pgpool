#!/usr/bin/python

# Start script for the pgpool service.

from __future__ import print_function

import os
import sys
import subprocess
import psycopg2
import psycopg2.extras
import logging


# setup logging
logger = logging.getLogger('com.cenx.deployer.postgresql')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_password(USERNAME):
    """ Getting password either from secret file, environment variable or setting it to default
    """

    FILENAME = '/run/secrets/{}'.format(USERNAME)
    if os.path.isfile(FILENAME):
        with open(FILENAME) as f:
            DB_PASSWORD = f.read().splitlines()[0]
    else:
        DB_PASSWORD = 'postgres'
    return DB_PASSWORD


def execute_command(POSTGRESQL_HOST, POSTGRESQL_CLIENT_PORT):
  """ executing the remote SQL command
  """

  con = None
  try:
      con = psycopg2.connect(host=POSTGRESQL_HOST, port=POSTGRESQL_CLIENT_PORT,
                             database='postgres', user='postgres', password=get_password('postgres'))
      cursor = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
      cursor.execute("select pg_is_in_recovery()")
      answer = cursor.fetchall()
      cursor.close()
      con.close()
      return(answer)
  except Exception as e:
      logger.error('Unable to execute SQL on database. Postgresql error: {}.'.format(e))
      sys.exit(1)
  finally:
      if con:
        con.close()


POSTGRESQL_HOST1 = os.environ.get('PGSQL_HOST1', 'postgresql_master')
POSTGRESQL_CLIENT_PORT1 = os.environ.get('PGSQL_PORT1', '5432')
POSTGRESQL_HOST2 = os.environ.get('PGSQL_HOST2', 'postgresql_slave')
POSTGRESQL_CLIENT_PORT2 = os.environ.get('PGSQL_PORT2', '5432')
RSYNC_PORT = os.environ.get('RSYNC_PORT', '873')
CHECK = sys.argv[1]


if (CHECK == '0'):
    code=execute_command(POSTGRESQL_HOST2,POSTGRESQL_CLIENT_PORT2)
    if code[0][0]:
       CURL_COMMAND = 'http://' + POSTGRESQL_HOST2 + ':' + '5000/failover'
       subprocess.call(['/usr/bin/curl', '-s',  CURL_COMMAND])
       pid = subprocess.Popen([sys.executable, "/etc/pgpool-II/templates/repair_pgpool.py", '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
elif (CHECK == '1'):
    code=execute_command(POSTGRESQL_HOST1,POSTGRESQL_CLIENT_PORT1)
    if code[0][0]:
       CURL_COMMAND = 'http://' + POSTGRESQL_HOST1 + ':' + '5000/failover'
       subprocess.call(['/usr/bin/curl', '-s',  CURL_COMMAND])
       pid = subprocess.Popen([sys.executable, "/etc/pgpool-II/templates/repair_pgpool.py", '0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
