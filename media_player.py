"""
Dune HD Smart D1
"""
import logging
import voluptuous as vol

from datetime import timedelta
import urllib.request
import xml.etree.ElementTree as ET
import os.path

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    PLATFORM_SCHEMA
)

from homeassistant.const import (
    CONF_HOST, CONF_NAME, CONF_TIMEOUT
)

import homeassistant.helpers.config_validation as cv
from homeassistant.util.dt import utcnow


class mylogger():
    def debug(self, format, *args):
        print(format % args)

    def warning(self, format, *args):
        print(format % args)


if __name__ == '__main__':
    _LOGGER = mylogger()
else:
    _LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'dunehd'
DEFAULT_TIMEOUT = 20
URL = 'http://{}/cgi-bin/do?cmd={}&timeout={}'
SCAN_INTERVAL = timedelta(seconds=30)

DUNE_PLAYING = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.SEEK
)
DUNE_IDLE = (
    MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
)
DUNE_OFF = None
DUNE_STANDBY = MediaPlayerEntityFeature.TURN_ON

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.socket_timeout,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    # _LOGGER.debug('setup_platform')
    dunehd = DuneHDDevice(
        config.get(CONF_NAME),
        config.get(CONF_HOST),
        config.get(CONF_TIMEOUT))
    add_entities([dunehd])


class DuneHDDevice(MediaPlayerEntity):
    def __init__(self, name, host, timeout):
        # _LOGGER.debug('__init__')
        self._name = name
        self._host = host
        self._timeout = timeout
        self._state = MediaPlayerState.OFF
        self._volume = None
        self._muted = None
        self._source = None
        self._source_list = None
        self._sound_mode = None
        self._sound_mode_list = None
        self._media_title = None
        self._position = None
        self._duration = None
        self._position_updated = None
        self._supported_features = DUNE_OFF

    def send_command(self, command):
        # _LOGGER.debug('send_command %s', command)
        url = URL.format(self._host, command, self._timeout)
        # print(url)
        try:
            resp = urllib.request.urlopen(url)
        except Exception:
            self._supported_features = DUNE_OFF
            self._state = MediaPlayerState.OFF
            return
        xml = ET.parse(resp)
        # ET.dump(xml)
        param = {}
        for e in xml.findall('param'):
            param[e.attrib['name']] = e.attrib['value']
        # print(param)

        player_state = param.get('player_state')
        self._source = player_state

        if player_state == 'standby':
            self._media_title = 'standby'
            self._supported_features = DUNE_STANDBY
            self._state = MediaPlayerState.STANDBY
            return

        if player_state == 'navigator':
            self._media_title = 'navigator'
            self._supported_features = DUNE_IDLE
            self._state = MediaPlayerState.IDLE
            return

        if player_state == 'file_playback':
            self._supported_features = DUNE_PLAYING
            playback_url = param.get('playback_url')
            self._media_title = os.path.basename(playback_url)
            playback_state = param.get('playback_state')
            if playback_state == 'paused':
                self._state = MediaPlayerState.PAUSED
            elif playback_state in ['playing', 'buffering']:
                self._state = MediaPlayerState.PLAYING
            else:
                self._state = MediaPlayerState.OFF
            self._muted = True if int(param.get('playback_mute')) else False
            self._volume = int(param.get('playback_volume')) / 100
            self._duration = int(param.get('playback_duration'))
            self._position = int(param.get('playback_position'))
            self._position_updated = utcnow()

    def update(self):
        # _LOGGER.debug('update')
        self.send_command('status')

    @property
    def is_on(self):
        # _LOGGER.debug('is_on')
        if self._state in [MediaPlayerState.OFF, MediaPlayerState.STANDBY]:
            return False
        return True

    @property
    def name(self):
        # _LOGGER.debug('name')
        return self._name

    @property
    def state(self):
        # _LOGGER.debug('state')
        return self._state

    @property
    def volume_level(self):
        # _LOGGER.debug('volume_level')
        return self._volume

    @property
    def is_volume_muted(self):
        # _LOGGER.debug('is_volume_muted')
        return self._muted

    @property
    def supported_features(self):
        # _LOGGER.debug('supported_features')
        return self._supported_features

    @property
    def source(self):
        # _LOGGER.debug('source')
        return self._source

    @property
    def source_list(self):
        # _LOGGER.debug('source_list')
        return self._source_list

    @property
    def sound_mode(self):
        # _LOGGER.debug('sound_mode')
        return self._sound_mode

    @property
    def sound_mode_list(self):
        # _LOGGER.debug('sound_mode_list')
        return self._sound_mode_list

    @property
    def media_title(self):
        # _LOGGER.debug('media_title')
        return self._media_title

    @property
    def media_position(self):
        return self._position

    @property
    def media_duration(self):
        return self._duration

    @property
    def media_position_updated_at(self):
        return self._position_updated

    @property
    def state_attributes(self):
        if self._state in [MediaPlayerState.OFF, MediaPlayerState.STANDBY,
                           MediaPlayerState.IDLE]:
            return None
        return super().state_attributes

    def turn_off(self):
        # _LOGGER.debug('turn_off')
        self.send_command('standby')
        self.schedule_update_ha_state()

#    def volume_up(self):
#        _LOGGER.debug('volume_up')
#        self.schedule_update_ha_state()
#        pass

#    def volume_down(self):
#        _LOGGER.debug('volume_down')
#        self.queue_command('VD')
#        self.schedule_update_ha_state()
#        pass

    def set_volume_level(self, volume):
        # _LOGGER.debug('set_volume_level %s', str(volume))
        self.send_command('set_playback_state&volume=' + str(int(volume*100)))
        self.schedule_update_ha_state()

    def mute_volume(self, mute):
        # _LOGGER.debug('mute_volume')
        self.send_command('set_playback_state&mute=' + ('1' if mute else '0'))
        self.schedule_update_ha_state()

    def turn_on(self):
        # _LOGGER.debug('turn_on')
        self.send_command('main_screen')
        self.schedule_update_ha_state()

    def media_stop(self):
        # _LOGGER.debug('media_stop')
        self.send_command('main_screen')
        self.schedule_update_ha_state()

    def select_source(self, source):
        # _LOGGER.debug('select_source %s', source)
        self.send_command('open_path&url=' + source)
        self.schedule_update_ha_state()

    def select_sound_mode(self, sound_mode):
        # _LOGGER.debug('select_sound_mode %s', sound_mode)
        # self.schedule_update_ha_state()
        pass

    def play_media(self, media_type, media_id, **kwargs):
        # _LOGGER.debug('play_media %s %s', media_type, media_id)
        self.send_command('launch_media_url&media_url=' + media_id)
        self.schedule_update_ha_state()

    def media_play(self):
        # _LOGGER.debug('media_play')
        self.send_command('set_playback_state&speed=256')
        self.schedule_update_ha_state()

    def media_pause(self):
        # _LOGGER.debug('media_pause')
        self.send_command('set_playback_state&speed=0')
        self.schedule_update_ha_state()

    def media_previous_track(self):
        # _LOGGER.debug('media_previous_track')
        self.send_command('ir_code&ir_code=B649BF00')
        self.schedule_update_ha_state()

    def media_next_track(self):
        # _LOGGER.debug('media_next_track')
        self.send_command('ir_code&ir_code=E21DBF00')
        self.schedule_update_ha_state()

    def media_seek(self, position):
        self.send_command('set_playback_state&position=' + str(position))
        self.schedule_update_ha_state()

#    @property
#    def media_channel(self):
#        _LOGGER.debug('media_channel')
#        return 'media_channel'

#    @property
#    def media_playlist(self):
#        _LOGGER.debug('media_playlist')
#        return 'media_playlist'

#    @property
#    def media_content_id(self):
#        _LOGGER.debug('media_content_id')
#        return 'media_content_id'

    @property
    def media_content_type(self):
        # _LOGGER.debug('media_content_type')
        return MediaType.VIDEO

#    @property
#    def media_track(self):
#        _LOGGER.debug('media_track')
#        return 'media_track'

#    @property
#    def media_artist(self):
#        _LOGGER.debug('media_artist')
#        return self._media_artist

#    @property
#    def media_album_name(self):
#        _LOGGER.debug('media_album_name')
#        return 'media_album_name'

#    @property
#    def media_album_artist(self):
#        _LOGGER.debug('media_album_artist')
#        return 'media_album_artist'

#    @property
#    def media_image_url(self):
#        _LOGGER.debug('media_image_url')
#        return self._image_url

#    @property
#    def app_id(self):
#        _LOGGER.debug('app_id')
#        return 'app_id'

#    @property
#    def app_name(self):
#        _LOGGER.debug('app_name')
#        return 'app_name'


if __name__ == '__main__':
    dunehd = DuneHDDevice('dunehd', '192.168.1.4', 20)

    # dunehd.send_command('status')
    dunehd.update()
    print(dunehd.state)
    print(dunehd.device_state_attributes)
    print(dir(dunehd))
    # dunehd.set_volume_level(1)
    dunehd.mute_volume(0)
