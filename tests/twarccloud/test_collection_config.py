from unittest import TestCase
from twarccloud.collection_config import CollectionConfigException, Changeset
from . import *


class TestInvalidReasons(TestCase):
    def setUp(self):
        self.timeline_config = timeline_config()
        self.filter_config = filter_config()
        self.search_config = search_config()

    def test_valid(self):
        self.assertFalse(self.timeline_config.invalid_reasons())
        self.assertFalse(self.filter_config.invalid_reasons())

    def test_id_with_space(self):
        self.timeline_config['id'] = 'time line'
        self.assertEqual(len(self.timeline_config.invalid_reasons()), 1)

    def test_missing_keys(self):
        del self.timeline_config['keys']
        self.assertEqual(len(self.timeline_config.invalid_reasons()), 1)

    def test_missing_key_values(self):
        del self.timeline_config['keys']['consumer_key']
        del self.timeline_config['keys']['consumer_secret']
        del self.timeline_config['keys']['access_token']
        del self.timeline_config['keys']['access_token_secret']
        self.assertEqual(len(self.timeline_config.invalid_reasons()), 4)

    def test_invalid_type(self):
        self.timeline_config['type'] = 'foo'
        self.assertEqual(len(self.timeline_config.invalid_reasons()), 1)

    def test_misstructured_users(self):
        self.timeline_config['users'] = [1, 2]
        self.assertEqual(len(self.timeline_config.invalid_reasons()), 1)

    def test_user_id_not_digits(self):
        self.timeline_config['users'] = {
            '481186914x': {
                'screen_name': 'justin_littman'
            }
        }
        self.assertEqual(len(self.timeline_config.invalid_reasons()), 1)

    def test_filter_fields(self):
        del self.filter_config['filter']['track']
        self.assertEqual(len(self.filter_config.invalid_reasons()), 1)

    def test_missing_query(self):
        del self.search_config['search']['query']
        self.assertEqual(len(self.search_config.invalid_reasons()), 1)


class TestDiff(TestCase):
    def setUp(self):
        self.timeline_config = timeline_config()
        self.filter_config = filter_config()
        self.other_timeline_config = timeline_config()
        self.other_filter_config = filter_config()

    def test_changed_id(self):
        self.other_timeline_config['id'] = 'bar'
        self.assertRaises(CollectionConfigException, self.timeline_config.diff, self.other_timeline_config)

    def test_changed_type(self):
        self.other_timeline_config['type'] = 'filter'
        self.assertRaises(CollectionConfigException, self.timeline_config.diff, self.other_timeline_config)

    def test_invalid_new_config(self):
        del self.other_timeline_config['keys']
        self.assertRaises(CollectionConfigException, self.timeline_config.diff, self.other_timeline_config)

    def test_changed_key(self):
        self.other_timeline_config['keys']['consumer_key'] = 'foo'
        changeset = self.timeline_config.diff(self.other_timeline_config)
        self.assertDictEqual(extract_dict(changeset), {
            'update': {
                'keys': {
                    'consumer_key': 'foo'
                }
            },
            'delete': []
        })

    def test_changed_filter(self):
        self.other_filter_config['filter']['follow'] = '123'
        del self.other_filter_config['filter']['track']
        changeset = self.filter_config.diff(self.other_filter_config)
        self.assertDictEqual(extract_dict(changeset), {
            'update': {
                'filter': {
                    'follow': '123'
                }
            },
            'delete': [{
                'filter': ['track']
            }]
        })

    def test_changed_timeline(self):
        self.other_timeline_config['users']['2244994945'] = {
            'screen_name': 'twitterdev',
            'since_id': '56789'
        }
        self.other_timeline_config['users']['481186914'] = {
            'screen_name': 'real_justin_littman'
        }
        del self.other_timeline_config['users']['6253282']
        del self.other_timeline_config['users']['12']['since_id']
        changeset = self.timeline_config.diff(self.other_timeline_config)
        self.assertDictEqual(extract_dict(changeset), {
            'update': {
                'users': {
                    '2244994945': {
                        'screen_name': 'twitterdev',
                        'since_id': '56789'
                    },
                    '481186914': {
                        'screen_name': 'real_justin_littman'
                    }
                }
            },
            'delete': [{
                    'users': ['6253282', {
                        '12': ['since_id']
                    }]
                }]
        })


class TestMerge(TestCase):
    def setUp(self):
        self.timeline_config = timeline_config()
        self.filter_config = filter_config()
        self.assert_timeline_config = timeline_config()
        self.assert_timeline_config['timestamp'] = '2019-03-10T13:57:52.432349'
        self.assert_filter_config = filter_config()
        self.assert_filter_config['timestamp'] = '2019-03-10T13:57:52.432349'
        self.changeset = Changeset()
        self.changeset['change_timestamp'] = '2019-03-10T13:57:52.432349'

    def test_merged_key(self):
        self.assert_timeline_config['keys']['consumer_key'] = 'foo'
        self.changeset['update'] = {
                'keys': {
                    'consumer_key': 'foo'
                }
            }
        self.timeline_config.merge_changeset(self.changeset)
        self.assertDictEqual(self.assert_timeline_config, self.timeline_config)

    def test_merged_timeline(self):
        self.assert_timeline_config['users']['2244994945'] = {
                        'screen_name': 'twitterdev',
                        'since_id': '56789'
                    }
        self.assert_timeline_config['users']['481186914']['screen_name'] = 'real_justin_littman'
        del self.assert_timeline_config['users']['6253282']
        del self.assert_timeline_config['users']['12']['since_id']

        self.changeset['update'] = {
                'users': {
                    '2244994945': {
                        'screen_name': 'twitterdev',
                        'since_id': '56789'
                    },
                    '481186914': {
                        'screen_name': 'real_justin_littman'
                    }
                }
        }
        self.changeset['delete'] = [{
                    'users': ['6253282', {
                        '12': ['since_id']
                    }]
                }]

        self.timeline_config.merge_changeset(self.changeset)
        self.assertDictEqual(self.assert_timeline_config, self.timeline_config)

    def test_merged_filter(self):
        self.assert_filter_config['filter']['follow'] = '123'
        del self.assert_filter_config['filter']['track']

        self.changeset['update'] = {
                'filter': {
                    'follow': '123'
                }
            }
        self.changeset['delete'] = [
            {'filter': ['track']
         }]

        self.filter_config.merge_changeset(self.changeset)
        self.assertDictEqual(self.assert_filter_config, self.filter_config)
