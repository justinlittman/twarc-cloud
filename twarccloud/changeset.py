from datetime import datetime


# Changes to a collection configuration
class Changeset(dict):
    def __init__(self):
        dict.__init__(self)
        self['update'] = {}
        self['delete'] = []
        self['change_timestamp'] = datetime.utcnow().isoformat()

    # Add a new key / value for a user.
    def update_user(self, key, value, user_id):
        if 'users' not in self['update']:
            self['update']['users'] = {}
        if user_id not in self['update']['users']:
            self['update']['users'][user_id] = {}
        self['update']['users'][user_id][key] = value

    # Deletes a user.
    def delete_user(self, user_id):
        users = None
        for field in self['delete']:
            if isinstance(field, dict) and 'users' in field:
                users = field['users']
                break
        if users is None:
            users = []
            self['delete'].append({
                'users': users
            })
        users.append(user_id)

    # Sets since_id for a search.
    def update_search(self, since_id):
        if 'search' not in self['update']:
            self['update']['search'] = {}
        self['update']['search']['since_id'] = str(since_id)

    # Returns True if this changeset has changes.
    def has_changes(self):
        return self['update'] or self['delete']

    # If there are any user updates in changeset for users that are not in collection config, remove them.
    def clean_changeset(self, new_collection_config):
        if 'users' not in self['update']:
            return
        remove_users_ids = []
        for user_id in self['update']['users']:
            if user_id not in new_collection_config.get('users', {}):
                remove_users_ids.append(user_id)
        for user_id in remove_users_ids:
            del self['update']['users'][user_id]
        if not self['update']['users']:
            del self['update']['users']
