import os
import json
from .collection_config import CollectionConfig


def describe_changes(changesets_path, ignore_keys=('since_id',), deletes_only=False):
    collection_config = CollectionConfig()
    for changeset_filename in sorted(os.listdir(changesets_path)):
        # Load the changeset
        with open('{}/{}'.format(changesets_path, changeset_filename)) as file:
            changeset = json.load(file)
            if not deletes_only:
                for key, value in changeset['update'].items():
                    for change in _describe_update(key, value, collection_config, [], changeset['change_timestamp'],
                                                   ignore_keys):
                        yield change
            for value in changeset['delete']:
                for change in _describe_delete(value, collection_config, [], changeset['change_timestamp'],
                                               ignore_keys):
                    yield change
            collection_config.merge_changeset(changeset)


# pylint: disable=too-many-arguments
def _describe_update(update_key, update_value, config, ancestor_keys, change_timestamp, ignore_keys):
    new_ancestor_keys = ancestor_keys.copy()
    new_ancestor_keys.append(update_key)
    if isinstance(update_value, dict):
        for key, value in update_value.items():
            for change in _describe_update(key, value, config.get(update_key, {}), new_ancestor_keys, change_timestamp,
                                           ignore_keys):
                yield change
    elif update_key not in ignore_keys:
        yield '{} changed from {} to {} on {}'.format(' -> '.join(new_ancestor_keys), config.get(update_key),
                                                      update_value, change_timestamp)


def _describe_delete(delete_value, config, ancestor_keys, change_timestamp, ignore_keys):
    new_ancestor_keys = ancestor_keys.copy()
    if isinstance(delete_value, dict):
        for key, values in delete_value.items():
            new_ancestor_keys.append(key)
            for value in values:
                for change in _describe_delete(value, config.get(key, {}), new_ancestor_keys, change_timestamp,
                                               ignore_keys):
                    yield change
    elif delete_value not in ignore_keys:
        new_ancestor_keys.append(delete_value)
        config_value = config.get(delete_value)
        if isinstance(config_value, dict):
            for key, value in config_value.items():
                if key not in ignore_keys:
                    new_ancestor_keys.append(key)
                    yield '{} deleted with value {} on {}'.format(' -> '.join(new_ancestor_keys), value,
                                                                  change_timestamp)
        else:
            yield '{} deleted with value {} on {}'.format(' -> '.join(new_ancestor_keys), config.get(delete_value),
                                                          change_timestamp)
