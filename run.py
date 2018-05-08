#!/usr/bin/env python

# Start script for the pgpool service.

from __future__ import print_function

import os
import sys
import stat
import grp
import pwd
import socket
import subprocess
import jinja2
from jinja2 import exceptions
import logging


# setup logging
logger = logging.getLogger('org.pgpool')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def convert_dns_to_ip(POSTGRESQL_HOST_LOCAL):
  """ convert dns to ip
  """

  if IP_FORMAT == 'IPV6':
      try:
          if socket.inet_pton(socket.AF_INET6, POSTGRESQL_HOST_LOCAL):
              POSTGRESQL_HOST_LOCAL = POSTGRESQL_HOST_LOCAL
      except socket.error:
          try:
              POSTGRESQL_HOST_LOCAL = socket.getaddrinfo(POSTGRESQL_HOST_LOCAL, None, socket.AF_INET6)[0][4][0]
          except socket.error:
              POSTGRESQL_HOST_LOCAL = '::1'
  else:
      try:
          if socket.inet_aton(POSTGRESQL_HOST_LOCAL):
              POSTGRESQL_HOST_LOCAL = POSTGRESQL_HOST_LOCAL
      except socket.error:
          try:
              POSTGRESQL_HOST_LOCAL = socket.gethostbyname(POSTGRESQL_HOST_LOCAL)
          except socket.error:
              POSTGRESQL_HOST_LOCAL = '127.0.0.1'
  return(POSTGRESQL_HOST_LOCAL)


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


def set_env():
  """ Setting default env
  """

  global UID
  global GID
  global PATH_PID
  global PATH_LOG
  global IP_FORMAT
  global LISTENING_ADDRESS
  global POSTGRES_USER
  global POSTGRES_PASSWORD
  global POSTGRESQL_MASTER
  global POSTGRESQL_SLAVE
  global HEALTH_CHECK_MAX_RETRIES

  pgpool_node_list = []
  LISTENING_ADDRESS = os.environ.get('LISTENING_ADDRESS', '0.0.0.0')
  UID = pwd.getpwnam("postgres").pw_uid
  GID = grp.getgrnam("postgres").gr_gid
  POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
  POSTGRES_PASSWORD = get_password('postgres')
  POSTGRESQL_MASTER = os.environ.get('POSTGRES_MASTER', 'postgresql_master')
  POSTGRESQL_SLAVE = os.environ.get('POSTGRES_SLAVE', 'postgresql_slave')
  HEALTH_CHECK_MAX_RETRIES = os.environ.get('HEALTH_CHECK_MAX_RETRIES', 10)


def render(name, conf):
  """ Render configuration file from template.
  """

  template_filename = '/etc/pgpool-II/templates/{}'.format(name)
  output_filename = '/etc/pgpool-II/{}'.format(name)

  env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(template_filename)),
                           extensions=['jinja2.ext.with_'])

  try:
    template = env.get_template(os.path.basename(template_filename))
  except exceptions.TemplateNotFound as e:
        logger.info('Error reading template file {}!'.format(template_filename))

  logger.debug('Conf list passed to Jinja template file {}.'.format(conf))
  with open(output_filename, "w") as f:
        f.write(template.render(conf))

  # set permission of rendered files to postgres:postgres
  os.chown(output_filename, UID, GID)


def configure_pgpool():

    logger.info('Configuring PGPOOL.')

      
    conf = {}

    conf['POSTGRESQL_MASTER']= POSTGRESQL_MASTER
    conf['POSTGRESQL_SLAVE']= POSTGRESQL_SLAVE
    conf['POSTGRES_USER']= POSTGRES_USER
    conf['POSTGRES_PASSWORD']= POSTGRES_PASSWORD
    conf['HEALTH_CHECK_MAX_RETRIES']= HEALTH_CHECK_MAX_RETRIES
    conf['LISTENING_ADDRESS']= LISTENING_ADDRESS
    render('pgpool.conf', conf)
      
    # creating pool_passwd file with the user and md5 password
    subprocess.Popen(['/usr/bin/pg_md5', '-f', '/etc/pgpool-II/pgpool.conf', '-m', '-u', POSTGRES_USER, POSTGRES_PASSWORD]).communicate()
    logger.info('pool_passwd file created with user {}'.format(POSTGRES_USER))


def configure_pool_hba():

  conf = {}
  PGSQL_SUBNET = os.environ.get('PGSQL_SUBNET', '10.0.0.0/8')
  conf['PGSQL_SUBNET']= PGSQL_SUBNET

  render('pool_hba.conf', conf)


def configure_pcp():

  conf = {}
  render('pcp.conf', conf)


def configure_pcppass():

  conf = {}
  conf['POSTGRES_USER']= POSTGRES_USER
  conf['POSTGRES_PASSWORD']= POSTGRES_PASSWORD
  render('.pcppass', conf)
  os.chmod('/etc/pgpool-II/.pcppass', 0600)


def run():

  logger.info('Starting PGPOOL.')
  try:
    if stat.S_ISSOCK(os.stat('/tmp/.s.PGSQL.{}'.format(5432)).st_mode):
       os.remove('/tmp/.s.PGSQL.{}'.format(5432))
  except OSError:
    logger.info("/tmp/.s.PGSQL.{} does not exist".format(5432))
  try:
    if stat.S_ISSOCK(os.stat('/tmp/.s.PGSQL.9898').st_mode):
       os.remove('/tmp/.s.PGSQL.9898')
  except OSError:
    logger.info("/tmp/.s.PGSQL.9898 does not exist")
  try:
    if stat.S_ISSOCK(os.stat('/tmp/.s.PGPOOLWD_CMD.9000').st_mode):
       os.remove('/tmp/.s.PGPOOLWD_CMD.9000')
  except OSError:
    logger.info("/tmp/.s.PGPOOLWD_CMD.9000 does not exist")
  if os.path.isfile('/var/run/pgpool/pgpool.pid'):
     os.remove('/var/run/pgpool/pgpool.pid')
  os.execl('/usr/bin/pgpool', 'pgpool', '-n',
           '-f', '/etc/pgpool-II/pgpool.conf',
           '-F', '/etc/pgpool-II/pcp.conf',
           '-a', '/etc/pgpool-II/pool_hba.conf')

def main():

  set_env()
  configure_pgpool()
  configure_pool_hba()
  configure_pcp()
  configure_pcppass()
  run()


if __name__ == "__main__":
  main()
