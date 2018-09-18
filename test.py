#!/usr/bin/env python
from time import sleep, time
from json import loads
from threading import Thread
from tty_radio.radio import Radio
from tty_radio.stream import mpg_running
from tty_radio.api import Server, Client


def test_obj():  # noqa
    r = Radio()
    print('%02d>>> r:%s' % (0, r))
    print('%02d>>> r.stations:%s' % (1, r.stations))
    assert r.play()[0] is None and not mpg_running()
    r.set('favs')
    print('%02d>>> r.station:%s' % (2, r.station))
    print('%02d>>> r._station:%s' % (3, r._station))
    print('%02d>>> r._station.streams:%s' % (4, r._station.streams))
    assert r.set('favs', 'BAGeL Radio')
    print('%02d>>> Playing' % 5)
    t1 = time()
    assert r.play()[1] is not None
    while r.song is None:
        sleep(1)
    print('%02d>>> Play 1 wait was %s' % (6, int(time() - t1)))
    assert mpg_running()
    print('%02d>>> r.song:%s' % (7, r.song))
    print('%02d>>> Pausing' % 8)
    t1 = time()
    r.pause()
    while not r.is_paused:
        sleep(1)
    print('%02d>>> Pause wait was %s' % (9, int(time() - t1)))
    assert not mpg_running()
    print('%02d>>> Playing' % 10)
    t1 = time()
    assert r.play()[1] is not None
    while r.song is None:
        sleep(1)
    print('%02d>>> Play 2 wait was %s' % (11, int(time() - t1)))
    assert mpg_running()
    print('%02d>>> Stopping' % 12)
    t1 = time()
    r.stop()
    while r.is_playing:
        sleep(1)
    assert not mpg_running()
    print('%02d>>> Stop wait was %s' % (13, int(time() - t1)))
    assert r.set('favs', 'WCPE Classical')
    print('%02d>>> r.stream:%s' % (14, r.stream))
    print('%02d>>> r._stream:%s' % (15, r._stream))
    print('%02d>>> Playing' % 16)
    t1 = time()
    assert r.play()[1] is not None and mpg_running()
    while r._stream.meta_name is None:
        sleep(1)
    print('%02d>>> Play 3 wait was %s' % (17, int(time() - t1)))
    assert r.play()[0] is None
    assert r.set('favs')
    assert r.set('favs', 'WCPE Classical')
    assert not r.set('favs', 'BAGeL Radio')
    print('%02d>>> Stopping' % 18)
    t1 = time()
    r.stop()
    while r.is_playing:
        sleep(1)
    assert not mpg_running()
    print('%02d>>> Stop wait was %s' % (19, int(time() - t1)))
    assert not r.set('ewqrewrwer')
    assert not r.set('favs', 'ewqrewrwer')


def test_api_serv():  # noqa
    r = Radio()
    s = Server('127.0.0.1', 7887, radio=r)
    r = s.index()
    print('%02d>>> s.index:%s' % (0, r))
    assert loads(r)['success']
    r = s.status()
    print('%02d>>> s.status:%s' % (1, r))
    assert loads(r)['success']
    r = s.stations()
    print('%02d>>> s.stations:%s' % (2, r))
    assert loads(r)['success']
    r = s.streams()
    print('%02d>>> s.streams:%s' % (3, r))
    assert loads(r)['success']
    r = s.streams('favs')
    print('%02d>>> s.streams(favs):%s' % (4, r))
    assert loads(r)['success']
    r = s.streams('ewqrewrwer')
    print('%02d>>> s.streams(ewqrewrwer):%s' % (5, r))
    assert not loads(r)['success']
    r = s.set('favs')
    print('%02d>>> s.set(favs):%s' % (6, r))
    assert loads(r)['success']
    r = s.set('ewqrewrwer')
    print('%02d>>> s.set(ewqrewrwer):%s' % (7, r))
    assert not loads(r)['success']
    r = s.set('favs', 'ewqrewrwer')
    print('%02d>>> s.set(favs,ewqrewrwer):%s' % (8, r))
    assert not loads(r)['success']
    r = s.set('favs', 'WCPE Classical')
    print('%02d>>> s.set(favs,WCPE Classical):%s' % (9, r))
    assert loads(r)['success']
    r = s.play()
    print('%02d>>> s.play:%s' % (10, r))
    assert loads(r)['success']
    sleep(10)
    r = s.play()
    print('%02d>>> double s.play:%s' % (11, r))
    assert not loads(r)['success']
    r = s.set('favs', 'BAGeL Radio')
    print('%02d>>> set during play s.set(favs,BAGeL Radio):%s' % (12, r))
    assert not loads(r)['success']
    r = s.pause()
    print('%02d>>> s.pause:%s' % (13, r))
    assert loads(r)['success']
    sleep(2)
    # double pause currently allowed
    # r = s.pause()
    # print('%02d>>> double s.pause:%s' % (14, r))
    # assert not loads(r)['success']:
    r = s.play()
    print('%02d>>> s.play:%s' % (14, r))
    assert loads(r)['success']
    sleep(10)
    r = s.status()
    print('%02d>>> s.status:%s' % (15, r))
    assert loads(r)['success']
    r = s.stop()
    print('%02d>>> s.stop:%s' % (16, r))
    assert loads(r)['success']
    r = s.stop()
    # double stop currently allowed
    # print('%02d>>> double s.stop:%s' % (17, r))
    # assert not loads(r)['success']


def test_api_client():  # noqa
    r = Radio()
    s = Server('127.0.0.1', 7887, radio=r)
    st = Thread(target=s.run)
    st.daemon = True
    st.start()
    sleep(1)
    c = Client('127.0.0.1', 7887)
    r = c.status()
    print('%02d>>> c.status:%s' % (0, r))
    assert r is not None
    r = c.stations()
    print('%02d>>> c.stations:%s' % (1, r))
    assert len(r) > 0
    print('%02d>>> c.streams' % 2)
    r = c.streams()
    assert len(r) > 0
    print('%02d>>> c.streams(favs):' % 3)
    r = c.streams('favs')
    assert len(r) > 0
    print('%02d>>> c.streams(ewqrewrwer):' % 4)
    r = c.streams('ewqrewrwer')
    assert len(r) == 0
    print('%02d>>> c.play(favs,ewqrewrwer)' % 5)
    r = c.play('favs', 'ewqrewrwer')
    assert not r
    r = c.play('favs', 'BAGeL Radio')
    print('%02d>>> c.play(favs,BAGeL Radio):%s' % (6, r))
    assert r
    sleep(10)
    r = c.pause()
    print('%02d>>> c.pause:%s' % (6, r))
    assert r
    r = c.stop()
    print('%02d>>> c.stop:%s' % (7, r))
    assert r
    sleep(2)
    r = c.play('favs', 'WCPE Classical')
    print('%02d>>> c.play(favs,WCPE Classical):%s' % (8, r))
    assert r
    sleep(10)
    r = c.status()
    print('%02d>>> c.status:%s' % (9, r))
    assert r is not None
    r = c.stop()
    print('%02d>>> c.stop():%s' % (10, r))
    assert r
