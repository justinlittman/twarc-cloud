# Methods that produce paths and filepaths.

DEFAULT_COLLECTIONS_PATH = 'collections'


# Returns path for collection.
def get_collection_path(collection_id, collections_path=DEFAULT_COLLECTIONS_PATH):
    return '{}/{}'.format(collections_path, collection_id)


# Returns filepath for file in collection path.
def get_collection_file(collection_id, filename, collections_path=DEFAULT_COLLECTIONS_PATH):
    return '{}/{}'.format(get_collection_path(collection_id, collections_path=collections_path), filename)


# Returns path for a harvester.
def get_harvest_path(collection_id, harvest_timestamp, collections_path=DEFAULT_COLLECTIONS_PATH):
    return '{}/{}/harvests/{}'.format(collections_path, collection_id, harvest_timestamp.strftime('%Y/%m/%d/%H/%M/%S'))


# Returns filepath for a file in a harvester path.
def get_harvest_file(collection_id, harvest_timestamp, filename, collections_path=DEFAULT_COLLECTIONS_PATH):
    return '{}/{}'.format(get_harvest_path(collection_id, harvest_timestamp, collections_path=collections_path),
                          filename)


# Returns filepath for a harvester info file.
def get_harvest_info_file(collection_id, harvest_timestamp, collections_path=DEFAULT_COLLECTIONS_PATH):
    return get_harvest_file(collection_id, harvest_timestamp, 'harvester.json', collections_path=collections_path)


# Returns filepath for a users file.
def get_users_filepath(collection_id, harvest_timestamp, collections_path=DEFAULT_COLLECTIONS_PATH):
    return get_harvest_file(collection_id, harvest_timestamp, 'users.jsonl', collections_path=collections_path)


# Returns filepath for a user changes file.
def get_user_changes_filepath(collection_id, harvest_timestamp, collections_path=DEFAULT_COLLECTIONS_PATH):
    return get_harvest_file(collection_id, harvest_timestamp, 'user_changes.json', collections_path=collections_path)


# Returns filepath for a harvester manifest.
def get_harvest_manifest_filepath(collection_id, harvest_timestamp, collections_path=DEFAULT_COLLECTIONS_PATH):
    return get_harvest_file(collection_id, harvest_timestamp, 'manifest-sha1.txt', collections_path=collections_path)

# Returns filepath for a lock file.
def get_lock_file(collection_id, collections_path=DEFAULT_COLLECTIONS_PATH):
    return get_collection_file(collection_id, 'lock.json', collections_path=collections_path)


# Returns filepath for the last harvester file.
def get_last_harvest_file(collection_id, collections_path=DEFAULT_COLLECTIONS_PATH):
    return get_collection_file(collection_id, 'last_harvest.json', collections_path=collections_path)


# Returns filepath for the collection configuration file.
def get_collection_config_filepath(collection_id, collections_path=DEFAULT_COLLECTIONS_PATH):
    return get_collection_file(collection_id, 'collection.json', collections_path=collections_path)


# Returns path for changesets.
def get_changesets_path(collection_id, collections_path=DEFAULT_COLLECTIONS_PATH):
    return get_collection_file(collection_id, 'changesets', collections_path=collections_path)


# Returns filepath for a changeset file.
def get_changeset_file(collection_id, change_timestamp, collections_path=DEFAULT_COLLECTIONS_PATH):
    return '{}/change-{}.json'.format(get_changesets_path(collection_id, collections_path=collections_path),
                                      change_timestamp.strftime('%Y%m%d%H%M%S'))
