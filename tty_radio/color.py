from __future__ import print_function
import time
import os
import sys
from .settings import Settings


def term_bg_is_dark():
    """Return True if the terminal background is dark, False otherwise"""
    fg, bg = os.environ.get('COLORFGBG', '0;15').split(";")
    return (int(bg) == 8 or int(bg) <= 6)


def set_theme_from_settings(settings=None):
    if settings is None:
        settings = Settings()
    theme = settings.config['DEFAULT']['theme']
    if theme == 'auto':
        theme = 'light'
        if term_bg_is_dark():
            theme = 'miami_vice'
    try:
        return dict(settings.config['theme_' + theme])
    except KeyError:
        print("##############################################################")
        print("ERROR")
        print("No theme '%s' defined in the config file (%s)"
              % (theme, settings.file))
        print("")
        print("The config file must contain a section 'theme_%s'" % theme)
        print("See e.g. 'theme_light' in config (--show-config)")
        print("")
        print("Fallback to 'auto'")
        print("##############################################################")
        time.sleep(5)
        if term_bg_is_dark():
            return dict(settings.config['theme_miami_vice'])
        else:
            return dict(settings.config['theme_light'])


THEME = set_theme_from_settings()


def update_theme(settings):
    theme = set_theme_from_settings(settings)
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
