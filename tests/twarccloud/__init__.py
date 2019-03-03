from twarccloud.collection_config import CollectionConfig


def extract_dict(changeset):
    del changeset['change_timestamp']
    return changeset


def timeline_config():
    config = CollectionConfig(
    {
        'id': 'foo',
        'type': 'user_timeline',
        'keys': {
                'consumer_key': 'mBbq9ruEckInQHUir8Kn0',
                'consumer_secret': 'Pf28yReBUD90pLVOsb4r5ZnKCQ6xlOomBAjD5npFEQ6Rm',
                'access_token': '481186914-5yIyfryJqcHV29YVL37BOzjseYuRzCLmwO6',
                'access_token_secret': 'S51yY5Hjffts4WMKMgvGendxbZVsZO014Z38Tfvc'
            },
        'users': {
                '481186914': {
                    'screen_name': 'justin_littman'
                },
                '6253282': {
                    'screen_name': 'twitterapi'
                },
                '12': {
                    'screen_name': 'jack',
                    'since_id': '12345'
                }
            }
    })
    return config


def filter_config():
    config = CollectionConfig({
        'id': 'foo',
        'type': 'filter',
        'keys': {
            'consumer_key': 'mBbq9ruEckInQHUir8Kn0',
            'consumer_secret': 'Pf28yReBUD90pLVOsb4r5ZnKCQ6xlOomBAjD5npFEQ6Rm',
            'access_token': '481186914-5yIyfryJqcHV29YVL37BOzjseYuRzCLmwO6',
            'access_token_secret': 'S51yY5Hjffts4WMKMgvGendxbZVsZO014Z38Tfvc'
        },
        'filter': {
            'track': 'foo,#bar'
        }
    })
    return config


def search_config():
    config = CollectionConfig(
    {
        'id': 'foo',
        'type': 'search',
        'keys': {
                'consumer_key': 'mBbq9ruEckInQHUir8Kn0',
                'consumer_secret': 'Pf28yReBUD90pLVOsb4r5ZnKCQ6xlOomBAjD5npFEQ6Rm',
                'access_token': '481186914-5yIyfryJqcHV29YVL37BOzjseYuRzCLmwO6',
                'access_token_secret': 'S51yY5Hjffts4WMKMgvGendxbZVsZO014Z38Tfvc'
            },
        'search': {
                'query': 'foo'
            }
    })
    return config
