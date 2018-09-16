#!/usr/bin/env python
from __future__ import print_function
import sys
from time import sleep
from threading import Thread
from getopt import getopt, GetoptError
import logging

import click

from .ui import ui as start_ui
from .api import Server
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
    """Run server without interactive terminal UI"""
    main(do_ui=False)


@radio.command()
def ui():
    """Run server with interactive terminal UI"""
    main(do_ui=True)
