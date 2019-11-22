import sys
import os
import psycopg2
import music21
from smrpy import indexers
from io import StringIO
from dataclasses import dataclass

try:
    plpy
except NameError:
    plpy = False
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()

def log(msg):
    if plpy:
        plpy.warning(msg)
    else:
        logger.debug(msg)

def index_piece(self):
