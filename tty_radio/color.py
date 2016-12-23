from __future__ import print_function
import sys


miami_vice = {
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
THEME = miami_vice


class colors:
    COLORS = {
        'purple': '\033[95m',
        'blue'  : '\033[94m',
        'green' : '\033[92m',
        'yellow': '\033[93m',
        'red'   : '\033[91m',
        'endc'  : '\033[0m',
    }

    def __init__(self, color, out=sys.stdout):
        self.color = color
        self.out = out

    def __enter__(self):
        self.out.write(self.COLORS[self.color])

    def __exit__(self, type, value, traceback):
        self.out.write(self.COLORS['endc'])
