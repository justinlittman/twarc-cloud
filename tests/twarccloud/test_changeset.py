from unittest import TestCase
from twarccloud.collection_config import Changeset
from . import *


class TestChangeSet(TestCase):
    def setUp(self):
        self.changeset = Changeset()

    def test_template(self):
        self.assertEqual(self.changeset['update'], {})
        self.assertEqual(self.changeset['delete'], [])
        self.assertTrue('change_timestamp' in self.changeset)

    def test_has_changes_update(self):
        self.assertFalse(self.changeset.has_changes())
        self.changeset.update_user('foo', 'bar', '12345')
        self.assertTrue(self.changeset.has_changes())

    def test_has_changes_delete(self):
        self.assertFalse(self.changeset.has_changes())
        self.changeset.delete_user('12345')
        self.assertTrue(self.changeset.has_changes())

    def test_clean(self):
        self.changeset['update'] = {
                'users': {
                    '6253282': {
                        'since_id': '56789'
                    },
                    '12345': {
                        'screen_name': 'foo'
                    }
                }
            }
        self.changeset.clean_changeset(timeline_config())
        self.assertDictEqual(extract_dict(self.changeset), {
            'update': {
                'users': {
                    '6253282': {
                        'since_id': '56789'
                    }
                }
            },
            'delete': []
        })

    def test_clean_no_users(self):
        self.changeset['update'] =  {
                'users': {
                    '12345': {
                        'screen_name': 'foo'
                    }
                }
            }
        self.changeset.clean_changeset(timeline_config())
        self.assertFalse(self.changeset['update'])
