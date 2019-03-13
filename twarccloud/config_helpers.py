import logging
import os
import configparser
from collections import namedtuple
from honeybadger import honeybadger
from twarc import Twarc
from twarccloud.exceptions import TwarcCloudException
from twarccloud import log


AwsConfiguration = namedtuple('AwsConfiguration',
                              ['cluster', 'task_role_arn', 'task_execution_role_arn', 'event_role_arn',
                               'security_group', 'subnet', 'log_group', 'honeybadger_key', 'image_tag'])


def setup_logging(debug=False):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    logging.getLogger('requests').setLevel(logging.INFO)
    logging.getLogger('requests_oauthlib').setLevel(logging.INFO)
    logging.getLogger('oauthlib').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('botocore').setLevel(logging.INFO)
    logging.getLogger('botocore.credentials').setLevel(logging.WARNING)
    logging.getLogger('s3transfer').setLevel(logging.INFO)
    logging.getLogger('boto3').setLevel(logging.INFO)
    logging.getLogger('twarc').setLevel(logging.WARNING)


def setup_honeybadger():
    if 'HONEYBADGER_API_KEY' in os.environ:
        honeybadger.configure()


def get_twitter_keys(profile=None, twarc_config=None):
    twarc = Twarc(config=twarc_config, profile=profile)
    return {
        'consumer_key': twarc.consumer_key,
        'consumer_secret': twarc.consumer_secret,
        'access_token': twarc.access_token,
        'access_token_secret': twarc.access_token_secret
    }


def load_ini_config(filepath):
    if not os.path.exists(filepath):
        raise TwarcCloudException('twarc_cloud.ini configuration required')
    ini_config = configparser.ConfigParser()
    ini_config.read(filepath)
    _assert_ini_config_fields(
        ['subnet', 'security_group', 'task_role_arn', 'task_execution_role_arn', 'event_role_arn', 'cluster',
         'image_tag'], ini_config)
    return ini_config


def _assert_ini_config_fields(field_names, ini_config):
    for field_name in field_names:
        if not field_name in ini_config['DEFAULT']:
            raise TwarcCloudException('{} is required in twarc_cloud.ini configuration.'.format(field_name))


def setup_aws_keys(ini_config):
    # See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#guide-configuration
    section = ini_config['DEFAULT']
    if 'access_key' in section and 'secret_key' in section:
        os.environ['AWS_ACCESS_KEY_ID'] = section['access_key']
        os.environ['AWS_SECRET_ACCESS_KEY'] = section['secret_key']
    else:
        log.warning(
            'Access key and/or secret key missing from twarc_cloud.ini. Maybe you used a different key '
            'configuration mechanism?')

def bucket_value(args, ini_config):
    return _config_value('bucket', args, ini_config)

def _config_value(key, args, ini_config):
    args_dict = vars(args)
    value = args_dict.get(key)
    if not value:
        value = ini_config['DEFAULT'].get(key)
    if not value:
        raise TwarcCloudException('{} is required.'.format(key))
    return value


def aws_configuration(ini_config):
    section = ini_config['DEFAULT']
    return AwsConfiguration(section['cluster'], section['task_role_arn'], section['task_execution_role_arn'],
                            section['event_role_arn'], section['security_group'], section['subnet'],
                            section['log_group'], section.get('honeybadger_key'), section['image_tag'])
