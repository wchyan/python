#!/usr/bin/python

import os
import logging

#logger basic usage
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info('Start reading database')
records = {'john': 55, 'tom': 66}
logger.debug('Records: %s', records)
logger.info('Updating records ...')
logger.info('Finish updating records')


#handler, level name, format
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.addLevelName(logging.INFO, "[ logging]")
# create a file handler
handler = logging.FileHandler('log.txt')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)
logger.info('Hello baby')


#except
try:
    open('/path/to/does/not/exist', 'rb')
except (SystemExit, KeyboardInterrupt):
    raise
except Exception, e:
    logger.error('Failed to open file', exc_info=True)


import logging.config
#logger config
logger = logging.getLogger(__name__)
 
# load config from file 
# logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
# or, for dictConfig
 
logging.config.dictConfig({
    'version': 1,              
    'disable_existing_loggers': False,  # this fixes the problem
 
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'INFO',    
            'class':'logging.StreamHandler',
        },  
    },
    'loggers': {
        '': {                  
            'handlers': ['default'],        
            'level': 'INFO',  
            'propagate': True 
        }
    }
})
 
logger.info('It works!')


import json
#logging from json
def setup_logging_json(
    default_path='logging.json', 
    default_level=logging.INFO,
    env_key='LOG_CFG'):
    
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

setup_logging_json()
logger = logging.getLogger(__name__)
logger.info('logger json config!')


import yaml
 
def setup_logging_yaml(
    default_path='logging.yaml', 
    default_level=logging.INFO,
    env_key='LOG_CFG'):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

setup_logging_yaml()
logger = logging.getLogger(__name__)
logger.info('logger yaml config!')
