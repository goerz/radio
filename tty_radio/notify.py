from __future__ import print_function

from os.path import expanduser
import time
import datetime

from .api import Client, ApiConnError

PYLAST = True
try:
    import pylast
except ImportError:
    PYLAST = False
    print("Hey-o, you don't have the pylast last.fm client installed:")
    print("  pip install pylast")


class NotifyClient(object):
    """Client for polling and forwarding artist/title information

    Monitors the server for changes in the metadata that indicate the currently
    playing arist and song title.

    If ``scrobble`` in the ``DEFAULT`` section of `settings` is activated, send
    songs to the Last.fm service, using the credentials specified in the
    ``Lastfm`` section of `settings`.

    Args:
        settings (configparser.ConfigParser): config file settings
    """
    def __init__(self, settings):
        self._scrobble = (
            settings.config['DEFAULT'].getboolean('scrobble') and PYLAST)
        logfile = settings.config['DEFAULT']['notify_logfile']
        if len(logfile) > 0:
            self._log_fh = open(expanduser(logfile), 'w')
        else:
            self._log_fh = None
        self._filters = ["Commercial-free", ]
        if self._scrobble:
            api_key = settings.config['Lastfm']['api key']
            api_secret = settings.config['Lastfm']['shared secret']
            username = settings.config['Lastfm']['username']
            password_hash = settings.config['Lastfm']['password hash']
            self.log("Scrobble API_KEY: %s" % api_key)
            self.log("Scrobble api_secret: %s" % api_secret)
            self.log("Last.fm username: %s" % username)
            self.log("Last.fm password_hash: %s" % password_hash)
            try:
                self._lastfm_network = pylast.LastFMNetwork(
                    api_key=api_key, api_secret=api_secret,
                    username=username, password_hash=password_hash)
                self.client = Client()
            except pylast.WSError as exc_info:
                self._scrobble = False
                self.log("ERROR connecting to Last.fm:")
                self.log("    " + str(exc_info), timestamp=False)
                self.log("    Check your credentials", timestamp=False)
            self._scrobbles = []

    def log(self, msg, timestamp=True):
        """Write a msg to the internal log file

        The log file is specified by ``notify_client_logfile`` in the
        ``DEFAULT`` section of the config file settings. If this setting is
        blank, the log `msg` is silently discarded.

        Args:
            msg (str): message to be written to the log file. Newlines in `msg`
                are stripped
            timestamp (bool): if True, prepend a timestamp to `msg` in the log
            file
        """
        if self._log_fh is not None:
            if timestamp:
                timestamp = datetime.datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
                self._log_fh.write(
                    "%s: %s\n" % (timestamp, msg.replace("\n", "")))
            else:
                self._log_fh.write(
                    "%s\n" % (msg.replace("\n", " ").strip()))
            self._log_fh.flush()

    def run(self):
        """Run the event loop

        If scrobbling is deactivated, return immediately.
        """
        current_artist = None
        current_title = None
        current_timestamp = 0
        try:
            if not self._scrobble:
                return
            prev_status = None
            while True:
                try:
                    status = self.client.status()
                except ApiConnError as exc_info:
                    self.log(str(exc_info))
                    time.sleep(5)
                    continue
                if status == prev_status:
                    time.sleep(1.0)
                    continue
                else:
                    prev_status = status
                self.log("status = %s" % str(status))
                artist, title = self._get_artist_title(status)
                if artist != current_artist or title != current_title:
                    timestamp = int(time.time())
                    need_to_scrobble = (
                        current_artist is not None and
                        current_title is not None and
                        timestamp - current_timestamp > 30)
                    if need_to_scrobble:
                        self.scrobble(
                            current_artist, current_title,
                            current_timestamp)
                    current_artist = artist
                    current_title = title
                    current_timestamp = timestamp
                    self.log(
                        "Setting current artist/title: %s - %s"
                        % (current_artist, current_title))
                time.sleep(1.0)
        except Exception as exc_info:
            self.log("FATAL: %s" % str(exc_info))
        finally:
            if self._log_fh is not None:
                self._log_fh.close()

    def scrobble(self, artist, title, timestamp):
        """Send a scrobble to Last.fm

        Assuming srobbling is active in the config file settings, send the
        given `arist`/`title` to Last.fm

        Args:
            artist (str): artist to submit in scrobble
            title (str): track title to submit in scrobble
            timestamp (int): play time stamp in epoch seconds to submit in
                scrobble
        """
        if self._scrobble:
            try:
                prev_artist, prev_title = self._scrobbles[-1]
                if artist == prev_artist and title == prev_title:
                    self.log("Duplicate scrobble: %s - %s" % (artist, title))
                    return
            except IndexError:
                pass
            self.log(
                "Scrobbling: %s - %s (%s)" % (
                    artist, title,
                    time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))))
            self._lastfm_network.scrobble(artist, title, int(timestamp))
            self._scrobbles.append([artist, title])

    def _get_artist_title(self, status):
        try:
            song = str(status['song'])
            for s in self._filters:
                if s in song:
                    self.log("Filter %s" % song)
                    return None, None
            artist, title = song.split(" - ", 1)
            return artist, title
        except (ValueError, AttributeError, KeyError) as exc_info:
            self.log("cannot get artist/title: %s" % exc_info)
            return None, None