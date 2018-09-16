#!/usr/bin/env python
from __future__ import print_function
import sys
import json
from time import sleep
from threading import Thread
from getopt import getopt, GetoptError
import logging

import click

from .ui import ui as start_ui
from .api import Server, Client, ApiConnError
from .ui import term_wh
from .color import colors
from .settings import Settings
from .notify import NotifyClient


__version__ = '2.0.0'


def main(do_ui):
    settings = Settings()

    notify_client = NotifyClient(settings)
    notify_thread = Thread(
        name='notify_client', target=notify_client.run)
    notify_thread.daemon = True
    notify_thread.start()

    s = Server()
    if not do_ui:
        s.run()
        return 0
    st = Thread(target=s.run)
    st.daemon = True
    st.start()
    sleep(0.5)
    start_ui(settings)


def print_config(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    settings = Settings()
    settings.config.write(sys.stdout)
    ctx.exit()


@click.group(invoke_without_command=True)
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
    arguments, or with the `ui` command (`radio ui`).
    Select station at prompt, by entering number found in left column

    The web UI can be accessed at http://localhost:7887.
    The `radio server` command starts the server without the interactive
    terminal UI.

    All other commands constitute the scripting interface. They assume a
    running server.

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
def server():
    """Run server without interactive terminal UI."""
    main(do_ui=False)


@radio.command()
def ui():
    """Run server with interactive terminal UI."""
    main(do_ui=True)


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


@click.option(
    '--station', default='favs',
    help='The "station" to play (\'favs\' (default) or \'soma\', see '
    '`radio stations`)')
@click.option(
    '--stream',
    help='Name of stream to play (see `radio stations`)')
@radio.command()
def play(station, stream):
    """Start stopped playback, or restart paused playback.

    Run as `radio play` to re-start playback after `radio pause` or `radio
    stop`. Use --station and --stream options to select and play a new radio
    stream. This works only if playback is stopped (not paused).
    """
    try:
        Client().play(station, stream)
    except ApiConnError:
        click.echo("Cannot connect to server")
        sys.exit(1)


@radio.command()
@click.option(
    '--song', is_flag=True,
    help='Print the current song name only, or a status indicator if '
    'paused/stopped')
def status(song):
    """Print the player status"""
    try:
        status = Client().status()
        if song:
            if status['paused']:
                song_str = '(paused)'
            else:
                song_str = status['song']
                if song_str == "No Title in Metadata":
                    song_str = "(stopped)"
            click.echo(song_str)
        else:
            click.echo(json.dumps(status))
    except ApiConnError:
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


@radio.command()
def toggle():
    """Toggle between play/pause."""
    try:
        client = Client()
        status = client.status()
        if status['stream'] is None:
            click.echo("Not tuned into a stream")
            return
        if status['paused']:
            client.play()
        else:
            client.pause()
    except ApiConnError:
        click.echo("Cannot connect to server")
        sys.exit(1)
