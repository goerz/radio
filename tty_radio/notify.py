from __future__ import print_function

from os.path import expanduser
import time
import datetime
import subprocess

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

    If ``scrobble`` in the ``Server`` section of `settings` is activated, send
    songs to the Last.fm service, using the credentials specified in the
    ``Lastfm`` section of `settings`.

    Args:
        settings (configparser.ConfigParser): config file settings
    """
    def __init__(self, settings):
        try:
            self._scrobble = (
                settings.config['Server'].getboolean('scrobble') and PYLAST)
        except ValueError as exc_info:
            raise ValueError(
                "Error in configuration, section '%s', key '%s': %s"
                % ('Server', 'scrobble', exc_info))
        logfile = settings.config['Server']['notify_logfile']
        if len(logfile) > 0:
            self._log_fh = open(expanduser(logfile), 'w')
        else:
            self._log_fh = None
        self._filters = ["Commercial-free", ]  # TODO: get this from config
        try:
            self._update_btt = (
                settings.config['Server'].getboolean('update_btt_widget'))
        except ValueError as exc_info:
            raise ValueError(
                "Error in configuration, section '%s', key '%s': %s"
                % ('Server', 'update_btt_widget', exc_info))
        if self._update_btt:
            self._btt_widget_uuid  = settings.config['BTT']['widget UUID']
            self._btt_shared_secret = settings.config['BTT']['shared secret']
            if self._btt_widget_uuid == '':
                self.log("Disabling update_bbt_widget: no widget UUID")
                self._update_btt = False
        if self._scrobble:
            self._lastfm_api_key = settings.config['Lastfm']['api key']
            self._lastfm_api_secret = settings.config['Lastfm']['shared secret']
            self._lastfm_username = settings.config['Lastfm']['username']
            self._lastfm_password_hash = settings.config['Lastfm']['password hash']
            self.log("Scrobble API_KEY: %s" % self._lastfm_api_key)
            self.log("Scrobble api_secret: %s" % self._lastfm_api_secret)
            self.log("Last.fm username: %s" % self._lastfm_username)
            self.log("Last.fm password_hash: %s" % self._lastfm_password_hash)
            self._lastfm_network = None  # set by _authenticate_lastfm
            self._authenticate_lastfm()
            self._scrobbles = []
        host = settings.config['Server']['host']
        port = settings.config['Server'].getint('port')
        self.client = Client(host, port)

    def log(self, msg, timestamp=True):
        """Write a msg to the internal log file

        The log file is specified by ``notify_client_logfile`` in the
        ``Server`` section of the config file settings. If this setting is
        blank, the log `msg` is silently discarded.

        Args:
            msg (str): message to be written to the log file. Newlines in `msg`
                are stripped
            timestamp (bool): if True, prepend a timestamp to `msg` in the log
            file
        """
        msg = str(msg)
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

    def _authenticate_lastfm(self):
            if isinstance(self._lastfm_network, pylast.LastFMNetwork):
                return  # already authenticated
            try:
                self._lastfm_network = pylast.LastFMNetwork(
                    api_key=self._lastfm_api_key,
                    api_secret=self._lastfm_api_secret,
                    username=self._lastfm_username,
                    password_hash=self._lastfm_password_hash)
                self.log(
                    "Authenticated Last.fm: %s" % str(self._lastfm_network))
            except pylast.WSError as exc_info:
                self._scrobble = False  # give up permanently
                self.log("ERROR connecting to Last.fm:")
                self.log("    " + str(exc_info), timestamp=False)
                self.log("    Check your credentials", timestamp=False)
            except pylast.NetworkError as exc_info:
                self.log("ERROR connecting to Last.fm:")
                self.log("    " + str(exc_info), timestamp=False)
                self.log("    No network connection", timestamp=False)

    def run(self):
        """Run the event loop

        If scrobbling and btt updating is deactivated, return immediately.
        """
        current_artist = None
        current_title = None
        current_timestamp = 0
        try:
            if not (self._scrobble or self._update_btt):
                self.log("Exit event loop: nothing to do")
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
                    self.update_btt(status)
                    prev_status = status
                self.log("status = %s" % str(status))
                artist, title = self._get_artist_title(status)
                if artist != current_artist or title != current_title:
                    timestamp = int(time.time())
                    if self._scrobble:
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
            raise
        finally:
            if self._log_fh is not None:
                self._log_fh.close()

    def update_btt(self, status):
        if not self._update_btt:
            return
        song_str = _render_song_str(status)
        song_str = song_str.replace("'", "\'")
        cmd = [
            'osascript', '-e',
            'tell application "BetterTouchTool" '
            'to update_touch_bar_widget "' + self._btt_widget_uuid +
            '" text "' + song_str + '"']
        if self._btt_shared_secret != '':
            cmd[-1] = cmd[-1] + ' shared_secret "%s"' % self._btt_shared_secret
        self.log(cmd)
        subprocess.call(cmd)

    def scrobble(self, artist, title, timestamp):
        """Send a scrobble to Last.fm

        Assuming srobbling is active in the config file settings, send the
        given `artist`/`title` to Last.fm

        Args:
            artist (str): artist to submit in scrobble
            title (str): track title to submit in scrobble
            timestamp (int): play time stamp in epoch seconds to submit in
                scrobble
        """
        if self._scrobble:
            self._authenticate_lastfm()
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
            try:
                self._lastfm_network.scrobble(artist, title, int(timestamp))
            except pylast.NetworkError as exc_info:
                self.log(
                    "Failed to scrobble %s - %s: %s"
                    % (artist, title, str(exc_info)))
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


def _render_song_str(status, show_stopped=False, show_stream=True):
    stream = status['stream']
    if status['currently_streaming']:
        if status['paused']:
            if stream is not None and len(str(stream)) > 0:
                song_str = '(paused: %s)' % stream
        else:
            song_str = status['song']
            if song_str == "No Title in Metadata":
                song_str = status['stream']
            else:
                if show_stream and stream is not None and len(str(stream)) > 0:
                    song_str = "%s\n%s" % (stream, song_str)
    else:
        if show_stopped:
            if stream is not None and len(str(stream)) > 0:
                song_str = '(stopped: %s)' % stream
            else:
                song_str = '(stopped)'
        else:
            song_str = ""
    return song_str
