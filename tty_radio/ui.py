from __future__ import print_function
import platform
import sys
import textwrap
import re
import math
from time import sleep
from io import StringIO
from subprocess import (
    check_output,
    CalledProcessError)
import click
PY3 = False
if platform.python_version().startswith('3'):
    PY3 = True
if PY3:
    get_input = input
else:
    get_input = raw_input

from .color import colors, THEME
from .banner import bannerize
from .album import gen_art
from .api import Client


# TODO
#   windows detect terminal size
#   leverage Radio/Station class to simplify menu "other stations"
#       aka station switch selections
#


def stream_list(streams):
    exploded = []
    name_re = re.compile("name=(.*),url")
    desc_re = re.compile("desc=\"(.*)\",art")
    for s in streams:
        name_m = name_re.search(s)
        desc_m = desc_re.search(s)
        s_exp = {
            'name': name_m.group(1),
            'desc': desc_m.group(1),
            'repr': s
        }
        exploded.append(s_exp)
    return exploded


def print_streams(station, streams, stations):
    (term_w, term_h) = click.get_terminal_size()
    line_cnt = 0
    if len(streams) == 0:
        print("Exiting, empty station file, delete it and rerun")
        sys.exit(1)
    # set up to pretty print station data
    # get left column width
    name_len = max([len(s['name']) for s in streams]) + 1
    # the first line has the name
    # each subsequent line has whitespace up to column begin mark
    # print the stations
    i = 0
    for s in streams:
        prefix = (" %2d" % i + " ) " + s['name'] +
                  ' ' * (name_len - len(s['name'])))
        (w, h) = print_blockify(
            prefix, THEME['ui_names'],
            s['desc'], THEME['ui_desc'])
        line_cnt += h
        i += 1
    # TODO get rid of hard coded access to the other stations
    prefix = (" %2d" % len(streams) + " ) SomaFM" +
              ' ' * (name_len - len("SomaFM")))
    desc = ("Enter " + str(len(streams)) +
            " or 's' to show SomaFM streams")
    if station == "soma":
        prefix = (" %2d" % len(streams) + " ) Favorites" +
                  ' ' * (name_len - len("Favorites")))
        desc = ("Enter " + str(len(streams)) +
                " or 'f' to show favorite streams")
    (w, h) = print_blockify(
        prefix, THEME['ui_names'],
        desc, THEME['ui_desc'])
    line_cnt += h
    return line_cnt - 1


# \033[A moves cursor up 1 line
# ' ' overwrites text
# '\b' resets cursor to start of line
# if the term is narrow enough, you need to go up multiple lines
def del_prompt(num_chars):
    # determine lines to move up, there is at least 1
    # bc user pressed enter to give input
    # when they pressed Enter, the cursor went to beginning of the line
    (term_w, term_h) = click.get_terminal_size()
    move_up = int(math.ceil(float(num_chars) / float(term_w)))
    print("\033[A" * move_up + ' ' * num_chars + '\b' * (num_chars), end='')


def read_input():
    try:
        stream_num = get_input("\nPlease select a stream [q to quit]: ")
    except SyntaxError:
        return
    if not stream_num:
        return
    stream_num = str(stream_num).strip().lower()
    if len(stream_num) == 0:
        return
    return stream_num


def try_as_int(stream_num, station, max_val):
    try:
        stream_num = int(stream_num)
    except ValueError:
        return None
    # keys[len] is the other station
    if stream_num < 0 or stream_num > max_val:
        return None
    # the final row is not a stream, but a station change
    if stream_num == max_val:
        if station == 'favs':
            return (None, 'soma')
        # else station == 'soma'
        return (None, 'favs')
    return (stream_num, station)


def get_choice(station, streams):
    """Get user choice of stream to play, or station to change"""
    while True:
        stream_num = read_input()
        if stream_num is None:
            continue
        ctrl_char = stream_num[0]
        if ctrl_char not in ['q', 'e', 's', 'f']:
            retval = try_as_int(stream_num, station, len(streams))
            if retval is None:
                continue
            else:
                return retval
        if (ctrl_char == 'q' or ctrl_char == 'e'):
            return (None, 'q')
        if ctrl_char == 'f':
            return (None, 'favs')
        if ctrl_char == 's':
            return (None, 'soma')
    # should never be here


def set_term_title(title=''):
    """Set (or clear) the terminal title"""
    sys.stdout.write("\x1b]0;" + title + "\x07")


def ui(settings):
    set_term_title("~=radio tuner=~")
    host = settings.config['Server']['host']
    port = settings.config['Server'].getint('port')
    c = Client(host, port)
    do_another = True
    next_st = 'favs'
    while do_another:
        try:
            next_st = ui_loop(c, settings, next_st)
        except KeyboardInterrupt:
            do_another = False
        if next_st == 'q':
            do_another = False
    set_term_title()  # clear


def ui_loop(client, settings, station='favs'):
    """list possible stations, read user input, and call player"""
    # when the player is exited, this loop happens again
    c = client
    if station is None:
        station = c.stations()[0]
    deets = c.station(station)
    streams = stream_list(c.streams(station))
    stations = c.stations()
    # streams.sort()  # put in alpha order
    # ######
    # print stations
    (term_w, term_h) = click.get_terminal_size()
    try:
        use_pyfiglet = settings.config['UI'].getboolean('figlet_banners')
    except ValueError:
        use_pyfiglet = False
    try:
        confirm_banner_font = (
            settings.config['UI'].getboolean('confirm_banner_font'))
    except ValueError:
        confirm_banner_font = False
    banner_txt = deets['ui_name'] + ' Tuner'
    with colors(THEME['ui_banner']):
        figlet_fonts = settings.config['UI']['figlet_fonts']
        (banner, font) = bannerize(
            banner_txt, term_w, figlet_fonts=figlet_fonts,
            use_pyfiglet=use_pyfiglet)
        b_IO = StringIO(banner)
        b_h = len(b_IO.readlines())
        print(banner)
        b_h += 1
    line_cnt = print_streams(station, streams, stations)
    loop_line_cnt = line_cnt + b_h + 2
    loop_line_cnt += 1
    if term_h > loop_line_cnt:
        print('\n' * (term_h - loop_line_cnt - 1))
    (stream_num, station) = get_choice(station, streams)
    if station == 'q':
        return 'q'
    # no stream given, must have been a station change, refresh list
    if stream_num is None:
        return station
    # ######
    # otherwise stream num specified, so call player
    ##
    # get the stream name only
    to_stream = streams[stream_num]
    # convert the name only into more details
    stream = c.stream(station, to_stream['name'])
    if stream is None:
        print('Error, could not get stream details')
        return station
    display_banner(
        stream['name'],
        figlet_fonts=settings.config['UI']['figlet_fonts'],
        confirm=confirm_banner_font,
        use_pyfiglet=use_pyfiglet)
    try:
        if settings.config['UI'].getboolean('show_stream_ascii_art'):
            display_album(stream['art'])
    except ValueError:
        pass
    try:
        compact_titles = settings.config['UI'].getboolean('compact_titles')
    except ValueError:
        compact_titles = False
    # this play->pause->play loop should never accumulate lines
    # in the output (except for the first Enter they press
    # at a prompt and even then, it's just an empty line)
    i = 0
    do_another = True
    while do_another:
        display_info()
        try:
            if display_metadata(c, stream, settings):
                c.stop()
                do_another = False
        # TODO poll user input for q to stop
        except KeyboardInterrupt:
            c.pause()
            # clear ctrl+c
            print('\b' * 5 + ' ' * 5 + '\b' * 5, end='')
            if compact_titles:
                # clear info, name, song
                to_del = click.get_terminal_size()[0]
                for i in range(3):
                    print("\033[A" + ' ' * to_del + '\b' * to_del, end='')
                sys.stdout.flush()
            prompt = "Paused. Press enter to Resume; m for menu. "
            with colors(THEME['stream_exit_confirm']):
                reloop = get_input(prompt)
            del_prompt(len(prompt) + len(reloop))
            # any key, not just m, takes you to the menu
            if len(reloop) != 0:
                c.stop()
                do_another = False
        i += 1
    # you can't use mpg123's 'pause' cmd (spacebar) bc it'll
    # fail a minute or two after resuming (buffer errors)
    # it literally pauses the music,
    # buffering the stream until unpaused, but the
    # behavior we want is to stop recving the stream
    # (like turning off a radio)
    return station


def display_info():
    msg1 = "Playing stream, enjoy..."
    msg2 = "[ctrl-c for pause/options]"
    with colors(THEME['stream_name_confirm']):
        if click.get_terminal_size()[0] <= (len(msg1) + len(msg2)):
            print(msg1)
        else:
            print(msg1 + ' ' + msg2)

def meta_prefix_str(theme):
    return theme['meta_prefix_str'] + " " * int(theme['meta_prefix_pad'])


def display_metadata(client, stream, settings):
    # to test these updates against another stream
    #   without conflicting audio:
    #   mpg123 -f 0 -C -@ <url>
    c = client
    try:
        compact_titles = settings.config['UI'].getboolean('compact_titles')
    except ValueError:
        compact_titles = False
    station_name = stream['station']
    stream_name = stream['name']
    if compact_titles:
        print()
        print()
    # stop anything playing from another client
    status = c.status()
    if status['currently_streaming'] and not status['paused']:
        c.stop()
    if not c.play(station_name, stream_name):
        print('Error for stream %s, already playing %s' % (stream, status))
        c.stop()
        return False
    showed_name = False
    i = 0
    disp_name = stream['meta_name']
    # disp names of '', like DEF CON Radio will escape loop
    while i < 10 and disp_name is None:
        stream = c.stream(station_name, stream_name)
        disp_name = stream['meta_name']
        sleep(0.5)
        i += 1
    if disp_name is None:
        disp_name = stream_name
    if disp_name is not None and disp_name.strip() != '':
        showed_name = True
        if compact_titles:
            print("\033[A" * 2, end='')
        print_blockify(
            meta_prefix_str(THEME), THEME['meta_prefix'],
            disp_name, THEME['meta_stream_name'],
            wrap=False)
        if compact_titles:
            print()
    # wait for initial song
    i = 0
    song_len = 0
    song_name = stream['meta_song']
    # song names of '', like WCPE will escape loop
    while i < 10 and song_name is None:
        stream = c.stream(station_name, stream_name)
        song_name = stream['meta_song']
        sleep(0.5)
        i += 1
    showed_song = False
    if song_name is not None and song_name.strip() != '':
        showed_song = True
        if compact_titles:
            print("\033[A", end='')
            if not showed_name:
                print("\033[A", end='')
        song_len = print_blockify(
            meta_prefix_str(THEME), THEME['meta_prefix'],
            song_name, THEME['meta_song_name'],
            wrap=False)[0]
        if compact_titles and not showed_name:
            print()
    # keep polling for song title changes
    do_another = True
    while do_another:
        status = c.status()
        song_now = status['song']
        if (song_now != song_name and
                song_now is not None and song_now.strip() != ''):
            if compact_titles:
                if not showed_name:
                    print("\033[A", end='')
                if not showed_song:
                    print("\033[A", end='')
                showed_song = True
                if song_len > 0:
                    del_prompt(song_len)
            song_len = print_blockify(
                meta_prefix_str(THEME), THEME['meta_prefix'],
                song_now, THEME['meta_song_name'],
                wrap=False)[0]
            song_name = song_now
        is_playing = status['currently_streaming']
        if not is_playing:
            return True
        sleep(1)
    return True


def print_blockify(prefix='', prefix_color='endc',
                   blk='', blk_color='endc',
                   wrap=True):
    # NOTE won't print only prefix without blk
    if len(blk) == 0:
        return (0, 0)
    p_len = len(prefix)
    with colors(prefix_color):
        # sys.stdout.write && flush
        print(prefix, end='')
    (term_w, term_h) = click.get_terminal_size()
    lines = textwrap.wrap(blk, term_w - p_len)
    max_blk_len = len(lines[0])
    with colors(blk_color):
        print(lines[0])
    if not wrap:
        return (len(prefix) + max_blk_len, 1)
    # prefix only appears on 1st line, justifying remainder
    prefix = ' ' * p_len
    for line in lines[1:]:
        if len(line) > max_blk_len:
            max_blk_len = len(line)
        with colors(blk_color):
            print(prefix + line)
    return (max_blk_len, len(lines))


def display_album(art_url):
    if art_url is None or art_url == '':
        return
    (term_w, term_h) = click.get_terminal_size()
    art = gen_art(art_url, term_w, term_h)
    if art is None:
        return
    print("")
    print(art)
    print("")


def display_banner(
        stream_name, figlet_fonts, confirm=False, use_pyfiglet=True):
    unhappy = True
    while unhappy:
        (term_w, term_h) = click.get_terminal_size()
        font = "unknown"
        with colors(THEME['stream_name_banner']):
            (banner, font) = bannerize(
                stream_name, term_w, figlet_fonts, use_pyfiglet)
            b_IO = StringIO(banner)
            b_height = len(b_IO.readlines())
            if term_h > (b_height + 3):  # Playing, Station Name, Song Title
                print('\n' * (term_h - b_height - 2))
            print(banner, end='')
        if confirm:
            with colors(THEME['stream_name_confirm']):
                prompt = "Press enter if you like banner"
                prompt += " (font: " + font + "), else any char then enter "
                try:
                    happiness = get_input(prompt)
                except SyntaxError:
                    happiness = ''
                del_prompt(len(prompt) + len(happiness))
                if len(happiness) == 0:
                    unhappy = False
                else:
                    print("")  # empty line for pretty factor
        else:
            unhappy = False
