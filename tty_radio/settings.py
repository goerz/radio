from __future__ import print_function
import os
from textwrap import dedent
from os.path import (
    expanduser,
    join as path_join)
import configparser
from collections import OrderedDict

SETTINGS_FILE = ".tty_radio-settings.ini"
# if you change SETTINGS_FILE, make sure to update the documentation


class Settings(object):
    def __init__(self, read_file=True, theme=None, vol=None, scrobble=None):
        self.config = configparser.ConfigParser(
            comment_prefixes=('#', ';'),
            inline_comment_prefixes=(';',),
            strict=True)
        self.config.read_dict(OrderedDict([
            ('Server', OrderedDict([
                ('host', '127.0.0.1'),
                ('port', '7887'),
                ('volume', '11000'),
                ('scrobble', 'no'),
                ('notify_logfile', ''),
                ('update_btt_widget', 'no'),
            ])),
            ('UI',  OrderedDict([
                ('theme', 'auto'),
                ('light_theme', 'light'),
                ('dark_theme', 'miami_vice'),
                ('fallback_theme', 'nocolor'),
                ('confirm_banner_font', 'no'),
                ('compact_titles', 'yes'),
                ('figlet_banners', 'yes'),
                ('figlet_fonts', dedent("""\
                     3-d, 3x5, 5lineoblique, a_zooloo, acrobatic,
                     alligator, alligator2, alphabet, avatar, banner, banner3-D,
                     banner4, barbwire, basic, bell, big, bigchief, block, britebi,
                     broadway, bubble, bulbhead, calgphy2, caligraphy, catwalk,
                     charact1, charact4, chartri, chunky, clb6x10, coinstak, colossal,
                     computer, contessa, contrast, cosmic, cosmike, courbi, crawford,
                     cricket, cursive, cyberlarge, cybermedium, cybersmall, devilish,
                     diamond, digital, doh, doom, dotmatrix, double, drpepper,
                     dwhistled, eftichess, eftifont, eftipiti, eftirobot, eftitalic,
                     eftiwall, eftiwater, epic, fender, fourtops, fraktur, funky_dr,
                     fuzzy, goofy, gothic, graceful, graffiti, helvbi, hollywood,
                     home_pak, invita, isometric1, isometric2, isometric3, isometric4,
                     italic, ivrit, jazmine, jerusalem, kban, larry3d, lean, letters,
                     linux, lockergnome, madrid, marquee, maxfour, mike, mini, mirror,
                     moscow, mshebrew210, nancyj-fancy, nancyj-underlined, nancyj,
                     new_asci, nipples, ntgreek, nvscript, o8, odel_lak, ogre, os2,
                     pawp, peaks, pebbles, pepper, poison, puffy, rectangles, relief,
                     relief2, rev, roman, rounded, rowancap, rozzo, runic, runyc,
                     sansbi, sblood, sbookbi, script, serifcap, shadow, short, sketch_s,
                     slant, slide, slscript, small, smisome1, smkeyboard, smscript,
                     smshadow, smslant, smtengwar, speed, stacey, stampatello, standard,
                     starwars, stellar, stop, straight, t__of_ap, tanja, tengwar, thick,
                     thin, threepoint, ticks, ticksslant, tinker-toy, tombstone, trek,
                     tsalagi, twin_cob, twopoint, univers, usaflag, utopiabi, weird,
                     whimsy, xbritebi, xcourbi""")
                ),  # line breaks MUST match __main__.config docstring
                ('show_stream_ascii_art', 'yes'),
            ])),
            ('theme_miami_vice', OrderedDict([
                ('ui_banner', 'red'),
                ('ui_names', 'yellow'),
                ('ui_desc', 'green'),
                ('stream_name_banner', 'yellow'),
                ('stream_name_confirm', 'purple'),
                ('meta_prefix_str', '>>>'),
                ('meta_prefix_pad', '1'),
                ('meta_prefix', 'blue'),
                ('meta_stream_name', 'blue'),
                ('meta_song_name', 'blue'),
                ('stream_exit_confirm', 'purple'),
            ])),
            ('theme_light', OrderedDict([
                ('ui_banner', 'purple'),
                ('ui_names', 'blue'),
                ('ui_desc', 'grey'),
                ('stream_name_banner', 'grey'),
                ('stream_name_confirm', 'purple'),
                ('meta_prefix_str', '>>>'),
                ('meta_prefix_pad', '1'),
                ('meta_prefix', 'blue'),
                ('meta_stream_name', 'blue'),
                ('meta_song_name', 'blue'),
                ('stream_exit_confirm', 'purple'),
            ])),
            ('theme_nocolor', OrderedDict([
                ('ui_banner', 'endc'),
                ('ui_names', 'endc'),
                ('ui_desc', 'endc'),
                ('stream_name_banner', 'endc'),
                ('stream_name_confirm', 'endc'),
                ('meta_prefix_str', '>>>'),
                ('meta_prefix_pad', '1'),
                ('meta_prefix', 'endc'),
                ('meta_stream_name', 'endc'),
                ('meta_song_name', 'endc'),
                ('stream_exit_confirm', 'endc'),
            ])),
            ('Lastfm', OrderedDict([
                ('api key', ''),
                ('shared secret', ''),
                ('username', ''),
                ('password hash', ''),
            ])),
            ('BTT', OrderedDict([
                ('widget UUID', ''),
                ('shared secret', ''),
            ])),
        ]))
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
