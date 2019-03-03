from twarc import Twarc
from .changeset import Changeset


# Configuration specifying what is to be harvested and other information about the collection.
class CollectionConfig(dict):
    # Returns a list of the reasons a collection configuration is invalid.
    def invalid_reasons(self):
        reasons = []
        reasons.extend(self._check_id())
        reasons.extend(self._check_keys())
        reasons.extend(self._check_type())
        if self['type'] == 'user_timeline':
            reasons.extend(self._check_timeline())
        elif self['type'] == 'filter':
            reasons.extend(self._check_filter())
        elif self['type'] == 'search':
            reasons.extend(self._check_search())
        return reasons

    def _check_id(self):
        reasons = []
        if 'id' not in self:
            reasons.append('Missing id.')
            return reasons

        if ' ' in self['id']:
            reasons.append('Id contains spaces.')
        return reasons

    def _check_keys(self):
        reasons = []
        if 'keys' in self:
            if 'consumer_key' not in self['keys']:
                reasons.append('Missing consumer_key.')
            if 'consumer_secret' not in self['keys']:
                reasons.append('Missing consumer_secret.')
            if 'access_token' not in self['keys']:
                reasons.append('Missing access_token.')
            if 'access_token_secret' not in self['keys']:
                reasons.append('Missing access_token_secret.')
        else:
            reasons.append('Missing keys.')
        return reasons

    def _check_type(self):
        reasons = []
        if 'type' not in self:
            reasons.append('Missing type.')
            return reasons

        if self['type'] not in ('user_timeline', 'filter', 'search'):
            reasons.append('Unrecognized collection type.')
        return reasons

    def _check_timeline(self):
        reasons = []
        if 'users' not in self:
            reasons.append('A user_timeline collection, but missing users.')
            return reasons
        if not isinstance(self['users'], dict):
            reasons.append('Users is not properly structured.')
            return reasons
        for user_id, user in self['users'].items():
            if not user_id.isdigit():
                reasons.append('{} is not a user_id.'.format(user_id))
            if not isinstance(user, dict):
                reasons.append('User {} is not properly structured.'.format(user_id))
        return reasons

    def _check_filter(self):
        reasons = []
        if 'filter' not in self:
            reasons.append('A filter collection, but missing filter.')
            return reasons
        if not isinstance(self['filter'], dict):
            reasons.append('Filter is not properly structured.')
            return reasons
        if 'track' not in self['filter'] and 'follow' not in self['filter'] and 'locations' not in self['filter']:
            reasons.append('Must provide track, follow, or locations for a filter.')
        return reasons

    def _check_search(self):
        reasons = []
        if 'search' not in self:
            reasons.append('A search collection, but missing search.')
            return reasons
        if not isinstance(self['search'], dict):
            reasons.append('Search is not properly structured.')
            return reasons
        if 'query' not in self['search']:
            reasons.append('Query must be provided.')
        return reasons


    # Adds users based on a list of user ids.
    def add_users_by_user_ids(self, user_ids):
        if 'users' not in self:
            self['users'] = {}
        for user_id in user_ids:
            if user_id and user_id not in self['users']:
                self['users'][user_id] = {}

    # Adds users based on a list of screen names.
    # The user ids for these screen names are retrieved from Twitter's API.
    # This collection must have valid keys provided.
    # Returns a list of screen names that were not found.
    def add_users_by_screen_names(self, screen_names):
        if 'keys' not in self:
            raise CollectionConfigException('Keys are required to add users by screen name.')
        keys = self['keys']
        twarc = Twarc(keys['consumer_key'],
                      keys['consumer_secret'],
                      keys['access_token'],
                      keys['access_token_secret'])
        # Lower case to original case
        screen_name_case_map = {}
        for screen_name in screen_names:
            clean_screen_name = screen_name.lstrip('@')
            if clean_screen_name:
                screen_name_case_map[clean_screen_name.lower()] = clean_screen_name
        if 'users' not in self:
            self['users'] = {}
        delete_users = []
        for user in twarc.user_lookup(screen_name_case_map.keys(), id_type='screen_name'):
            if user['id_str'] not in self['users']:
                self['users'][user['id_str']] = {'screen_name': user['screen_name']}
            delete_users.append(user['screen_name'].lower())
        for screen_name in delete_users:
            del screen_name_case_map[screen_name]
        return screen_name_case_map.values()

    # Merge a changeset into this collection configuration.
    def merge_changeset(self, changeset):
        # Update
        self._merge_update_dict(self, changeset['update'])

        # Delete
        self._merge_delete_list(self, changeset['delete'])
        # Set the timestamp
        self['timestamp'] = changeset['change_timestamp']


    @staticmethod
    def _merge_update_dict(merge_dict, update):
        for key, value in update.items():
            if isinstance(value, dict):
                new_update_dict = merge_dict.get(key, {})
                merge_dict[key] = new_update_dict
                CollectionConfig._merge_update_dict(new_update_dict, value)
            else:
                merge_dict[key] = value

    @staticmethod
    def _merge_delete_list(merge_dict, delete):
        for key in delete:
            if isinstance(key, dict):
                for dict_key in key.keys():
                    if dict_key in merge_dict:
                        CollectionConfig._merge_delete_list(merge_dict[dict_key], key[dict_key])
            elif key in merge_dict:
                del merge_dict[key]

    # Returns a changeset created by diffing this collection configuration and a provided collection configuration.
    # The ids and types must match.
    def diff(self, other_config):
        reasons = other_config.invalid_reasons()
        if reasons:
            raise CollectionConfigException('New configuration is not valid: {}'.format(' '.join(reasons)))
        if self['id'] != other_config['id']:
            raise CollectionConfigException('Collection id may not change.')
        if self['type'] != other_config['type']:
            raise CollectionConfigException('Collection type may not change.')

        changeset = Changeset()
        self._diff_dict(self, other_config, changeset['update'], changeset['delete'], 'keys')
        if other_config['type'] == 'filter':
            self._diff_dict(self, other_config, changeset['update'], changeset['delete'], 'filter')
        elif other_config['type'] == 'user_timeline':
            self._diff_dict(self, other_config, changeset['update'], changeset['delete'], 'users')
        elif other_config['type'] == 'search':
            self._diff_dict(self, other_config, changeset['update'], changeset['delete'], 'search')
        return changeset

    @staticmethod
    def _diff_dict(orig_dict, new_dict, update_diff, delete_diff, only_key):
        update_diff.update(CollectionConfig._dict_diff_update(orig_dict, new_dict, only_key=only_key))
        delete_diff.extend(CollectionConfig._diff_dict_deletes(orig_dict, new_dict, only_key=only_key))

    @staticmethod
    def _diff_dict_deletes(orig_dict, new_dict, only_key=None):
        delete_diff = []
        for key, value in orig_dict.items():
            if only_key in (key, None):
                if key not in new_dict:
                    delete_diff.append(key)
                elif isinstance(value, dict):
                    child_delete_diff = CollectionConfig._diff_dict_deletes(value, new_dict[key])
                    if child_delete_diff:
                        delete_diff.append({key: child_delete_diff})
        return delete_diff

    @staticmethod
    def _dict_diff_update(orig_dict, new_dict, only_key=None):
        update_diff = {}
        for key, value in orig_dict.items():
            if key in new_dict and only_key in (key, None):
                if isinstance(value, dict):
                    child_update_diff = CollectionConfig._dict_diff_update(value, new_dict[key])
                    if child_update_diff:
                        update_diff[key] = child_update_diff
                elif value != new_dict[key]:
                    update_diff[key] = new_dict[key]

        for key, value in new_dict.items():
            if key not in orig_dict and only_key in (key, None):
                update_diff[key] = value

        return update_diff


def config_template(collection_type, collection_id=None):
    template = {
        'id': collection_id or '<Identifier for collection. Should not have spaces. Must be unique for bucket.>',
        'keys': {
            'consumer_key': '<Your Twitter API consumer key>',
            'consumer_secret': '<Your Twitter API consumer secret>',
            'access_token': '<Your Twitter API access token>',
            'access_token_secret': '<Your Twitter API access token secret>'
        },
        'type': collection_type
    }

    if collection_type == 'user_timeline':
        template['users'] = {}
        template['delete_users_for'] = ['protected', 'suspended', 'not_found']
    elif collection_type == 'filter':
        template['filter'] = {}
        template['filter']['track'] = '<Comma separated list of terms or hashtags>'
        template['filter']['follow'] = '<Comma separated list of user ids>'
        template['filter']['max_records'] = '<Optional. Maximum number of records to collect per harvester.'
    elif collection_type == 'search':
        template['search'] = {}
        template['search']['query'] = '<Query>'
        template['search']['max_records'] = '<Optional. Maximum number of records to collect per harvester.'
    return template


class CollectionConfigException(Exception):
    pass
