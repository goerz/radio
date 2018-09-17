from __future__ import print_function
import time
import os
import sys
from .settings import Settings

THEME = {}  # initialized in main via load_theme

def term_bg_is_dark():
    """Return True if the terminal background is dark, False otherwise"""
    fg, bg = os.environ.get('COLORFGBG', '0;15').split(";")
    return (int(bg) == 8 or int(bg) <= 6)


def load_theme(settings):
    theme_name = settings.config['UI']['theme']
    if theme_name == 'auto':
        theme_name = 'light'
        if term_bg_is_dark():
            theme_name = 'miami_vice'
    try:
        theme = dict(settings.config['theme_' + theme_name])
    except KeyError:
        raise ValueError(
            "No theme '%s' defined in the config file (%s): must contain "
            "section 'theme_%s'" % (theme_name, settings.file, theme_name))
    for (key, val) in theme.items():
        if key not in ['meta_prefix_str', 'meta_prefix_pad']:
            if val not in colors.COLORS:
                raise ValueError(
                    "Error in color theme '%s': invalid color '%s' for %s"
                    % (theme_name, val, key))
    THEME.update(theme)


class colors:
    COLORS = {
        'grey'     : '\033[90m',
        'red'      : '\033[91m',
        'green'    : '\033[92m',
        'yellow'   : '\033[93m',
        'blue'     : '\033[94m',
        'purple'   : '\033[95m',
        'turquoise': '\033[96m',
        'endc'     : '\033[0m',
    }

    def __init__(self, color, out=sys.stdout):
        self.color = color
        self.out = out

    def __enter__(self):
        self.out.write(self.COLORS[self.color])

    def __exit__(self, type, value, traceback):
        self.out.write(self.COLORS['endc'])
