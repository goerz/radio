from __future__ import print_function
import os
from os.path import (
    expanduser,
    join as path_join)
import configparser

SETTINGS_FILE = ".tty_radio-settings.ini"
# if you change SETTINGS_FILE, make sure to update the documentation


class Settings(object):
    def __init__(self, read_file=True, theme=None, vol=None, scrobble=None):
        self.config = configparser.ConfigParser()
        self.config['UI'] = {
            'theme': 'auto',
            'light_theme': 'light',
            'dark_theme': 'miami_vice',
            'fallback_theme': 'nocolor',
            'confirm_banner_font': 'no',
            'compact_titles': 'yes',  # only show last title in UI?
            'figlet_banners': 'yes',
        }
        self.config['Server'] = {
            'host': '127.0.0.1',
            'port': '7887',
            'scrobble': 'no',
            'notify_logfile': '',
            'volume': '11000',
            'update_btt_widget': 'no',
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
        self.config['theme_nocolor'] = {
            'ui_banner': 'endc',
            'ui_names': 'endc',
            'ui_desc': 'endc',
            'stream_name_banner': 'endc',
            'stream_name_confirm': 'endc',
            'meta_prefix_str': '>>>',
            'meta_prefix_pad': '1',
            'meta_prefix': 'endc',
            'meta_stream_name': 'endc',
            'meta_song_name': 'endc',
            'stream_exit_confirm': 'endc',
        }
        self.config['Lastfm'] = {
            'api key': '',
            'shared secret': '',
            'username': '',
            'password hash': '',
        }
        self.config['BTT'] = {
            'widget UUID': '',
            'shared secret': '',
        }
        home = expanduser('~')
        self.file = path_join(home, SETTINGS_FILE)
        if read_file:
            self.config.read([self.file])
        if theme is not None:
            self.config['UI']['theme'] = theme
        if vol is not None:
            self.config['UI']['volume'] = str(vol)
        if scrobble is not None:
            if isinstance(scrobble, bool):
                if scrobble:
                    scrobble = 'yes'
                else:
                    scrobble = 'no'
            self.config['Server']['scrobble'] = str(scrobble)
        _check_volume(self.config['Server']['volume'])
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
