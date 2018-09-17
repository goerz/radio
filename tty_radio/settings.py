from __future__ import print_function
import os
from os.path import (
    expanduser,
    join as path_join)
import configparser

SETTINGS_FILE = ".tty_radio-settings.ini"


class Settings(object):
    def __init__(self, theme=None, vol=None, scrobble=None):
        self.config = configparser.ConfigParser()
        self.config['DEFAULT'] = {
            'theme': 'auto',
            'confirm_banner_font': 'no',
            'scrobble': 'no',
            'update_btt_widget': 'no',
            'notify_logfile': '',
            'compact_titles': 'yes',  # only show last title in UI?
            'figlet_banners': 'yes',
            'volume': '11000',
        }
        self.config['theme_miami_vice'] = {
            'ui_banner': 'red',
            'ui_names': 'yellow',
            'ui_desc': 'green',
            'stream_name_banner': 'yellow',
            'stream_name_confirm': 'purple',
            'meta_prefix_str': '>>>',
            'meta_prefix_pad': '1',
            'meta_prefix': 'blue',
            'meta_stream_name': 'blue',
            'meta_song_name': 'blue',
            'stream_exit_confirm': 'purple',
        }
        self.config['theme_light'] = {
            'ui_banner': 'purple',
            'ui_names': 'blue',
            'ui_desc': 'grey',
            'stream_name_banner': 'grey',
            'stream_name_confirm': 'purple',
            'meta_prefix_str': '>>>',
            'meta_prefix_pad': '1',
            'meta_prefix': 'blue',
            'meta_stream_name': 'blue',
            'meta_song_name': 'blue',
            'stream_exit_confirm': 'purple',
        }
        self.config['Lastfm'] = {
            'api key': 'b25b959554ed76058ac220b7b2e0a026',
            'shared secret': '425b55975eed76058ac220b7b4e8a054',
            'username': 'username',
            'password hash': '25b5192f9943196a6044ca1b6b1d30c2',
        }
        self.config['BTT'] = {
            'widget UUID': '',
            'shared secret': '',
        }
        home = expanduser('~')
        self.file = path_join(home, SETTINGS_FILE)
        self.config.read([self.file])
        if theme is not None:
            self.config['DEFAULT']['theme'] = theme
        if vol is not None:
            self.config['DEFAULT']['volume'] = str(vol)
        if scrobble is not None:
            if isinstance(scrobble, bool):
                if scrobble:
                    scrobble = 'yes'
                else:
                    scrobble = 'no'
            self.config['DEFAULT']['scrobble'] = str(scrobble)
        _check_volume(self.config['DEFAULT']['volume'])
        if not os.path.isfile(self.file):
            with open(self.file, 'w') as out_fh:
                self.config.write(out_fh)


def _check_volume(value):
    try:
        if 0 <= int(value) <= 32000:
            return value
        else:
            raise ValueError(
                "Invalid volume %s must be between 0 and 32000" % value)
    except (ValueError, TypeError):
        raise ValueError(
            "Invalid volume %s must be integer between 0 and 32000" % value)
