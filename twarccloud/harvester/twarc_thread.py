import threading
import json
import requests
from twarc import Twarc
from twarccloud.harvester.tweet_writer_thread import TweetWriterThread
from twarccloud.filepaths_helper import get_users_filepath, get_user_changes_filepath
from twarccloud.harvester.file_queueing_writer import FileQueueingWriter
from twarccloud import log


# Thread that performs harvesting.
# pylint: disable=too-many-instance-attributes
class TwarcThread(threading.Thread):
    # pylint: disable=too-many-arguments
    def __init__(self, config, collections_path, harvest_timestamp, file_queue, changeset, stop_event, harvest_info,
                 connection_errors=5, http_errors=5, tweets_per_file=None):
        self.config = config
        self.file_queue = file_queue
        self.collections_path = collections_path
        self.harvest_timestamp = harvest_timestamp
        self.connection_errors = connection_errors
        self.http_errors = http_errors
        self.tweets_per_file = tweets_per_file
        self.twarc = self._create_twarc()
        self.stop_event = stop_event
        self.harvest_info = harvest_info
        self.changeset = changeset
        self.writer = None
        self.exception = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            log.debug('Starting twarc thread')
            api_method_type = self.config.get('type')
            log.debug("API method type is %s", api_method_type)
            with TweetWriterThread(self.collections_path, self.config['id'], self.harvest_timestamp, self.file_queue,
                                   self.harvest_info, self.tweets_per_file) as self.writer:
                if api_method_type == 'user_timeline':
                    self.user_timelines()
                elif api_method_type == 'filter':
                    self.filter()
                elif api_method_type == 'search':
                    self.search()
                else:
                    raise KeyError('Unknown API method type: {}'.format(api_method_type))
            self.harvest_info.end()
            log.debug('Ending twarc thread')
        # pylint: disable=broad-except
        except Exception as exception:
            self.exception = exception

    def filter(self):
        filter_config = self.config.get('filter')
        track = filter_config.get('track')
        follow = filter_config.get('follow')
        locations = filter_config.get('locations')

        assert track or follow or locations

        max_records = int(self.config['filter'].get('max_records', 0))
        for count, tweet in enumerate(
                self.twarc.filter(track=track, follow=follow, locations=locations, event=self.stop_event)):
            if not count % 1000:
                log.debug("Collected %s tweets", count)
            self.writer.write(tweet)
            if max_records and max_records-1 == count:
                log.debug("Reached max records of %s", max_records)
                self.stop_event.set()

    def search(self):
        assert 'query' in self.config.get('search', {})
        query = self.config['search']['query']
        since_id = self.config['search'].get('since_id')
        max_records = int(self.config['search'].get('max_records', 0))
        max_id = int(since_id) if since_id else 0
        for count, tweet in enumerate(self.twarc.search(q=query, since_id=since_id)):
            if not count % 1000:
                log.debug("Collected %s tweets", count)
            self.writer.write(tweet)
            max_id = max(max_id, tweet['id'])
            if self.stop_event.is_set():
                break
            if max_records and max_records-1 == count:
                log.debug("Reached max records of %s", max_records)
                break
        # Set since_id on changeset
        self.changeset.update_search(max_id)

    def user_timelines(self):
        assert 'users' in self.config
        user_ids = self.config['users'].keys()
        user_changes = []
        with FileQueueingWriter(
                get_users_filepath(self.config['id'], self.harvest_timestamp, collections_path=self.collections_path),
                self.file_queue, delete=True) as users_writer:
            for count, user_id in enumerate(user_ids):
                user_details = self.config['users'][user_id]
                screen_name = user_details.get('screen_name')
                result, user = self._lookup_user(user_id)
                if result != 'OK':
                    change_details = {
                        'user_id': user_id,
                        'change': result
                    }
                    if 'screen_name' in user_details:
                        change_details['screen_name'] = user_details['screen_name']
                    user_changes.append(change_details)
                    if result in self.config.get('delete_users_for', []):
                        self.changeset.delete_user(user_id)
                    continue
                users_writer.write_json(user)
                if 'screen_name' not in user_details:
                    user_changes.append({
                        'user_id': user_id,
                        'change': 'screen name found',
                        'screen_name': user['screen_name']
                    })
                    self.changeset.update_user('screen_name', user['screen_name'], user_id)
                elif user_details['screen_name'] != user['screen_name']:
                    user_changes.append({
                        'user_id': user_id,
                        'change': 'screen name changed',
                        'screen_name': user['screen_name']
                    })
                    self.changeset.update_user('screen_name', user['screen_name'], user_id)
                log.debug("Collecting timeline of %s (%s of %s)", screen_name or user_id, count + 1, len(user_ids))
                new_max_id = self._user_timeline(user_id=user_id, since_id=user_details.get('since_id'))
                if new_max_id and (new_max_id != user_details.get('since_id')):
                    self.changeset.update_user('since_id', new_max_id, user_id)
                if self.stop_event.is_set():
                    break
        with FileQueueingWriter(get_user_changes_filepath(self.config['id'], self.harvest_timestamp,
                                                          collections_path=self.collections_path),
                                self.file_queue, delete=True) as user_changes_writer:
            user_changes_writer.write_json(user_changes, indent=2)

    def _user_timeline(self, user_id=None, since_id=None):
        max_id = int(since_id) if since_id else 0
        for count, tweet in enumerate(self.twarc.timeline(user_id=user_id, since_id=since_id)):
            if not count % 100:
                log.debug("Collected %s tweets for %s", count, user_id)
            self.writer.write(tweet)
            max_id = max(max_id, tweet['id'])
            if self.stop_event.is_set():
                break
        return str(max_id) if max_id else None

    # From https://github.com/gwu-libraries/sfm-twitter-harvester/blob/master/twitter_harvester.py#L145
    def _lookup_user(self, user_id):
        url = "https://api.twitter.com/1.1/users/show.json"
        params = {'user_id': user_id}

        # USER_DELETED: 404 and {"errors": [{"code": 50, "message": "User not found."}]}
        # USER_PROTECTED: 200 and user object with "protected": true
        # USER_SUSPENDED: 403 and {"errors":[{"code":63,"message":"User has been suspended."}]}
        result = "OK"
        user = None
        try:
            resp = self.twarc.get(url, params=params, allow_404=True)
            user = resp.json()
            if user['protected']:
                result = "protected"
        except requests.exceptions.HTTPError as exception:
            try:
                resp_json = exception.response.json()
            except json.decoder.JSONDecodeError:
                raise exception
            if exception.response.status_code == 404 and self._has_error_code(resp_json, 50):
                result = "not_found"
            elif exception.response.status_code == 403 and self._has_error_code(resp_json, 63):
                result = "suspended"
            else:
                raise exception
        return result, user

    @staticmethod
    def _has_error_code(resp, code):
        if isinstance(code, int):
            code = (code,)
        for error in resp['errors']:
            if error['code'] in code:
                return True
        return False

    def _create_twarc(self):
        return Twarc(self.config["keys"]["consumer_key"],
                     self.config["keys"]["consumer_secret"],
                     self.config["keys"]["access_token"],
                     self.config["keys"]["access_token_secret"],
                     http_errors=self.http_errors,
                     connection_errors=self.connection_errors,
                     tweet_mode="extended")
