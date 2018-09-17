#!/usr/bin/env python
from __future__ import print_function
import sys
import json
from time import sleep
from threading import Thread
import logging

import click

from .ui import ui as start_ui
from .api import Server, Client, ApiConnError
from .color import load_theme
from .settings import Settings, _check_volume
from .notify import NotifyClient, _render_song_str
from .stream import Stream


__version__ = '2.0.0'


def main(do_ui, theme=None, vol=None, scrobble=None):
    try:
        settings = Settings(theme=theme, vol=vol, scrobble=scrobble)
        Stream.vol = settings.config['Server']['volume']
        if do_ui:
            load_theme(settings)
    except (ValueError, TypeError) as exc_info:
        click.echo("Error in config: %s" % str(exc_info))
        sys.exit(1)

    try:
        # is there a server running already?
        Client().status()  # raises ApiConnError if no server running
        if not do_ui:
            click.echo("Server already running")
            sys.exit(1)
    except ApiConnError:
        # no server running ...
        s = Server()
        # ... start server in background thread
        server_thread = Thread(target=s.run)
        server_thread.daemon = True
        server_thread.start()
        sleep(1.0)
        # run notify-client in background (always together with server)
        try:
            notify_client = NotifyClient(settings)
        except ValueError as exc_info:
            click.echo("Cannot start notify-thread: %s" % exc_info)
            sys.exit(1)
        notify_thread = Thread(
            name='notify_client', target=notify_client.run)
        notify_thread.daemon = True
        notify_thread.start()

    # foreground process:
    if do_ui:
        try:
            start_ui(settings)
        except ApiConnError:
            click.echo("Cannot connect to server")
            sys.exit(1)
    else:
        server_thread.join()
    sys.exit(0)


def _get_volume_input_format(value):
    if value.endswith('%'):
        return 'percent'
    elif 0 <= float(value) <= 1.0:
        return 'float'
    elif 0 <= float(value) <= 100:
        return 'percent'
    else:
        return 'int'


def print_config(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    settings = Settings()
    settings.config.write(sys.stdout)
    ctx.exit()


class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if cmd_name == 'start':
            matches = ['play']
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


@click.group(cls=AliasedGroup, invoke_without_command=True)
@click.help_option('--help', '-h')
@click.version_option(version=__version__)
@click.option(
    '--debug', is_flag=True,
    help='Enable debug logging')
@click.option(
    '--show-config', is_flag=True, callback=print_config,
    expose_value=False, is_eager=True,
    help='Show the active configuration ')
@click.pass_context
def radio(ctx, debug):
    """
    \b
    tty-radio User Interfaces
    -------------------------

    The interactive terminal user interface is shown if `radio` is run without
    arguments, or with the `ui` command (`radio ui`, which accepts additional
    options).

    Select station at prompt, by entering number found in left column

    The web UI can be accessed at http://localhost:7887.
    The `radio server` command starts the server without the interactive
    terminal UI.

    All other commands constitute the scripting interface. They assume a
    running server. Run ``radio COMMAND --help`` for details on each command.

    \b
    About
    -----

    RESTful service for listening to online music streams.
    Built-in compatibility with SomaFM.
    Add custom station scrapers or manually add to ~/.tty_radio-favs.csv.
    Organizes your stations into a list to select from, then calls mpg123.
    (You can use any player that doesn't buffer stdout.)
    And let's not forget the pretty ASCII art...

    The program reads settings from the ~/.tty_radio-settings.ini config file.
    If this file does not exist, it will be created with the default settings.
    A complete config file with all currently active settings can be obtained
    via the `--show-config` option.
    """
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Enabled debug output")
    if ctx.invoked_subcommand is None:
        main(do_ui=True)


@radio.command()
@click.option(
    '--vol', metavar='INT',
    help="Volume value 0..32k. Overrides setting in config file.")
@click.option(
    '--scrobble/--no-scrobble', default=None,
    help="Activate or de-activate Last.fm scrobbling, overriding the "
    "value in the config file.")
def server(vol, scrobble):
    """Run server without interactive terminal UI."""
    main(do_ui=False, vol=vol, scrobble=scrobble)


@click.option(
    '--theme', metavar='NAME',
    help="Name of theme to use. Overrides setting in config file.")
@click.option(
    '--vol', metavar='INT',
    help="Volume value 0..32k. Overrides setting in config file.")
@click.option(
    '--scrobble/--no-scrobble', default=None,
    help="Activate or de-activate Last.fm scrobbling, overriding the "
    "value in the config file.")
@radio.command()
def ui(theme, vol, scrobble):
    """Run server with interactive terminal UI."""
    main(do_ui=True, theme=theme, vol=vol, scrobble=scrobble)


@radio.command()
def pause():
    """Pause playback."""
    try:
        Client().pause()
    except ApiConnError:
        click.echo("Cannot connect to server")
        sys.exit(1)


@radio.command()
def stop():
    """Stop playback."""
    try:
        Client().stop()
    except ApiConnError:
        click.echo("Cannot connect to server")
        sys.exit(1)


def _find_station(stations, search_str, station):
    search_str = search_str.replace(" ", "").lower()
    for station_dict in stations:
        station_name = station_dict['name']
        if station is not None and station != station_name:
            continue
        for stream_name in station_dict['streams']:
            if search_str in stream_name.replace(" ", "").lower():
                return station_name, stream_name


@click.option(
    '--station',
    help='The "station" to which to limit searching for a stream '
    '(\'favs\' or \'soma\', see `radio stations`)')
@click.argument('search', nargs=-1)
@radio.command()
def play(station, search):
    """(alias: start) start or re-start playback.

    Run as `radio play` without arguments to re-start playback after `radio
    pause` or `radio stop`. To start playback of a particular station, either
    use SEARCH arguments, possibly in combination with --station: all available
    streams are searched for a matching stream name (case-insensitive, ignoring
    whitespace).
    """
    try:
        client = Client()
        stream = None
        if len(search) > 0:
            search_str = "".join(search)
            stations = Client().stations()
            try:
                station, stream = _find_station(stations, search_str, station)
            except TypeError:
                if station is None:
                    click.echo(
                        "Cannot find a stream matching '%s'" % search_str)
                else:
                    click.echo(
                        "Cannot find a stream matching '%s' in station '%s'"
                        % (search_str, station))
                sys.exit(1)
            click.echo("Playing station: %s" % stream)
        status = client.status()
        if not status['paused'] or status['currently_streaming']:
            client.stop()
        if stream is None and status['stream'] is None:
            click.echo("No active stream. Specify a stream name")
            sys.exit(1)
        client.play(station, stream)
    except ApiConnError:
        click.echo("Cannot connect to server")
        sys.exit(1)


@radio.command()
@click.option(
    '--song', is_flag=True,
    help='Print the current song or stream name if not stopped.')
@click.option(
    '--stream', is_flag=True,
    help='Print the current stream name. In combination with --song, two '
    'lines may be printed (stream name on the first line, song title on '
    'the second line)')
@click.option(
    '--quiet', is_flag=True, help='Fail silenty if no server is running')
def status(song, stream, quiet):
    """Print the player status.

    ``radio status --song --quiet`` is useful to generate a string to be shown
    in a UI element.
    """
    try:
        status = Client().status()
        if song:
            click.echo(_render_song_str(status, show_stream=stream))
        elif stream:
            click.echo(status['stream'])
        else:
            click.echo(json.dumps(status))
    except ApiConnError:
        if not quiet:
            click.echo("Cannot connect to server")
        sys.exit(1)


@radio.command()
def stations():
    """List stations and feeds, as json-formatted string"""
    try:
        stations = Client().stations()
        click.echo(json.dumps(stations))
    except ApiConnError:
        click.echo("Cannot connect to server")
        sys.exit(1)


@click.option(
    '--stop', is_flag=True, help='stop, instead of pause')
@radio.command()
def toggle(stop):
    """Toggle between play/pause."""
    try:
        client = Client()
        status = client.status()
        if status['stream'] is None:
            click.echo("Not tuned into a stream")
            return
        if status['paused'] or not status['currently_streaming']:
            client.play()
        else:
            if stop:
                client.stop()
            else:
                client.pause()
    except ApiConnError:
        click.echo("Cannot connect to server")
        sys.exit(1)


@radio.command()
@click.option(
    '--value', metavar='VALUE',
    help='Volume value. An integer 0..32k, a float 0..1.0, or an '
    'integer 0..100 (with an optional trailing percentage sign), '
    'depending on the value of --format')
@click.option(
    '--reset', is_flag=True,
    help="Reset the volume to the value in the config file.")
@click.option(
    '--format', type=click.Choice(['float', 'int', 'percent']),
    help="Format in which to print volume, or in which to parse --value")
def volume(value, reset, format):
    """Show or adjust the volume.

    If called without arguments, print the current volume and exit. The volume
    can be changed by passing a --value, or --reset. Changing the volume stops
    and re-starts any active stream.

    If --format is not specified, the format of --value will be autodetected
    """
    try:
        client = Client()
        status = client.status()
        if reset:
            settings = Settings()
            value = _check_volume(settings.config['Server']['volume'])
            format = 'int'
        if value is not None:
            input_format = format
            if input_format is None:
                try:
                    input_format = _get_volume_input_format(value)
                except (ValueError, TypeError):
                    click.echo("Invalid value: %s" % value)
                    sys.exit(1)
            if input_format == 'float':
                value = int(float(value) * 32000)
            elif input_format == 'percent':
                if value.endswith('%'):
                    value = value[:-1]
                value = int(float(value) * 320)
            if value != status['volume']:
                client.volume(value)
                if status['currently_streaming']:
                    client.stop()
                    client.play()
                status = client.status()
        value = status['volume']
        float_str = str(float(value)/32000.0)
        int_str = str(int(value))
        percent_str = str(int(float(value)/320)) + "%"
        if reset:
            format = None
        if format == 'float':
            value_str = float_str
        elif format == 'int':
            value_str = int_str
        elif format == 'percent':
            value_str = percent_str
        else:
            value_str = "%s / %s / %s" % (int_str, float_str, percent_str)
        click.echo(value_str)
    except ApiConnError:
        click.echo("Cannot connect to server")
        sys.exit(1)
