v2.0.0
======

* New stateless command line interface ("scripting interface"): `radio play`, `radio pause`, `radio stop`, `radio toggle`, `radio station`, `radio status`, `radio config` commands (new dependency: `click`)
* Add support for scrobbling to Last.fm (requires `pylast` package and an API key)
* Add support for updating BetterTouchTool Macbook touchbar widgets with the currently playing song information
* New config file in ~/.tty_radio-settings.ini to control settings of the terminal UI (e.g. color themes) and scrobbling/notification support
* Automatically choose a light or dark terminal UI color scheme based on the `$COLORFGBG` environment variable. Fallback to no colors. This may be overridden in the config file.
* Support changing the playback volume with `radio volume` command or a direct API call (the terminal UI or web clients currently do not support changing the volume)
* Allow to disable figlet banners alltogether, or just the prompt to confirm the choice of the random figlet font for banner (in config file)
* Switch testing to pytest
