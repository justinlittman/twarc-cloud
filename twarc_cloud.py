#!/usr/bin/env python3

import argparse
from twarccloud.config_helpers import setup_logging, load_ini_config, aws_configuration, setup_aws_keys
from twarccloud.cli.harvest import add_harvest_subparser, handle_harvest_command
from twarccloud.cli.collection_config import add_collection_config_subparser, handle_collection_config_command
from twarccloud.cli.collection import add_collection_subparser, handle_collection_command
from twarccloud.exceptions import TwarcCloudException
from twarccloud import __version__


def main():

    parser = argparse.ArgumentParser(description='Manage AWS resources for Twarc Cloud.')
    parser.add_argument('-V', '--version', action='store_true', help='Show version and exit')
    parser.add_argument('--debug', action='store_true')
    subparsers = parser.add_subparsers(help='command help', dest='command')
    collection_config_subparser = add_collection_config_subparser(subparsers)
    collection_parser = add_collection_subparser(subparsers)
    harvest_parser = add_harvest_subparser(subparsers)

    # Setup configuration
    m_args = parser.parse_args()
    setup_logging(debug=m_args.debug)
    m_ini_config = load_ini_config('twarc_cloud.ini')
    m_aws_config = aws_configuration(m_ini_config)
    setup_aws_keys(m_ini_config)

    try:
        if m_args.version:
            print('Version {}'.format(__version__))
        elif m_args.command == 'collection':
            handle_collection_command(m_args, m_ini_config, m_aws_config, collection_parser)
        elif m_args.command == 'harvest':
            handle_harvest_command(m_args, m_aws_config, m_ini_config, harvest_parser)
        elif m_args.command == 'collection-config':
            handle_collection_config_command(m_args, m_ini_config, collection_config_subparser)
        else:
            parser.print_help()
            exit(1)
    except TwarcCloudException as exception:
        print(exception)
        exit(1)


if __name__ == "__main__":
    main()
