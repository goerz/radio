from __future__ import print_function
import os
from os.path import (
    expanduser,
    join as path_join)
import configparser

SETTINGS_FILE = ".tty_radio-settings.ini"


class Settings(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config['DEFAULT'] = {
            'theme': 'auto',
        }
        self.config['theme_miami_vice'] = {
            'ui_banner': 'red',
            'ui_names': 'yellow',
            'ui_desc': 'green',
            'stream_name_banner': 'yellow',
            'stream_name_confirm': 'purple',
            'meta_prefix_str': '>>> ',
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
            'meta_prefix_str': '>>> ',
            'meta_prefix': 'blue',
            'meta_stream_name': 'blue',
            'meta_song_name': 'blue',
            'stream_exit_confirm': 'purple',
        }
        home = expanduser('~')
        self.file = path_join(home, SETTINGS_FILE)
        self.config.read([self.file])
        if not os.path.isfile(self.file):
            with open(self.file, 'w') as out_fh:
                self.config.write(out_fh)
