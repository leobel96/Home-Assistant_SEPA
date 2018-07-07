"""

"""
import logging
import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_EFFECT, ATTR_HS_COLOR,
    ATTR_WHITE_VALUE, SUPPORT_BRIGHTNESS, SUPPORT_COLOR_TEMP, SUPPORT_EFFECT,
    SUPPORT_COLOR, SUPPORT_WHITE_VALUE, Light, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, CONF_PAYLOAD_OFF, CONF_PAYLOAD_ON)

from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util
from homeassistant.components.sepa import sepa_update

_LOGGER = logging.getLogger(__name__)

SEPA_UPDATE = "delete {?s ?p ?c } insert {?s ?p ?o} where {OPTIONAL{?s ?p ?c }}"
SEPA_NAMESPACE = '<http://www.home-assistant.io/?x>'
CONF_BRIGHTNESS_PREDICATE = 'brightness_predicate'
CONF_BRIGHTNESS_SCALE = 'brightness_scale'
CONF_COLOR_TEMP_PREDICATE = 'color_temp_predicate'
CONF_EFFECT_PREDICATE = 'effect_predicate'
CONF_EFFECT_LIST = 'effect_list'
CONF_RGB_PREDICATE = 'rgb_predicate'
CONF_STATE_PREDICATE = 'state_predicate'
CONF_UPDATE_URL = 'update_url'
CONF_XY_PREDICATE = 'xy_predicate'
CONF_WHITE_VALUE_PREDICATE = 'white_value_predicate'
CONF_WHITE_VALUE_SCALE = 'white_value_scale'

DEFAULT_BRIGHTNESS_SCALE = 255
DEFAULT_PAYLOAD_OFF = 'OFF'
DEFAULT_PAYLOAD_ON = 'ON'
DEFAULT_WHITE_VALUE_SCALE = 255


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_UPDATE_URL): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_STATE_PREDICATE): cv.string,
    vol.Optional(CONF_BRIGHTNESS_PREDICATE): cv.string,
    vol.Optional(CONF_BRIGHTNESS_SCALE, default=DEFAULT_BRIGHTNESS_SCALE):
        vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional(CONF_COLOR_TEMP_PREDICATE): cv.string,
    vol.Optional(CONF_EFFECT_PREDICATE): cv.string,
    vol.Optional(CONF_EFFECT_LIST): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_PAYLOAD_ON, default=DEFAULT_PAYLOAD_ON): cv.string,
    vol.Optional(CONF_PAYLOAD_OFF, default=DEFAULT_PAYLOAD_OFF): cv.string,
    vol.Optional(CONF_RGB_PREDICATE): cv.string,
    vol.Optional(CONF_WHITE_VALUE_PREDICATE): cv.string,
    vol.Optional(CONF_WHITE_VALUE_SCALE, default=DEFAULT_WHITE_VALUE_SCALE):
        vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional(CONF_XY_PREDICATE): cv.string,
})

    
async def async_setup_platform(hass, config, async_add_devices,
                               discovery_info=None):
    """Set up a SEPA Light."""

    async_add_devices([SepaLight(
        config.get(CONF_NAME),
        config.get(CONF_UPDATE_URL),
        config.get(CONF_EFFECT_LIST),
        {
            key: config.get(key) for key in (
                CONF_BRIGHTNESS_PREDICATE,
                CONF_COLOR_TEMP_PREDICATE,
                CONF_STATE_PREDICATE,
                CONF_EFFECT_PREDICATE,
                CONF_RGB_PREDICATE,
                CONF_WHITE_VALUE_PREDICATE,
                CONF_XY_PREDICATE,
            )
        },
        {
            'on': config.get(CONF_PAYLOAD_ON),
            'off': config.get(CONF_PAYLOAD_OFF),
        },
        config.get(CONF_BRIGHTNESS_SCALE),
        config.get(CONF_WHITE_VALUE_SCALE),
)])

class SepaLight(Light):
    """Representation of a SEPA light."""

    def __init__(self, name, update_url, effect_list, predicates,  payload, brightness_scale,
                 white_value_scale):
        """Initialize SEPA light."""
        
        self._sparql = SEPA_UPDATE
        self._name = name.replace(' ', '_')
        self._subject = SEPA_NAMESPACE.replace('?x' ,self._name)
        self._update_url = update_url
        self._effect_list = effect_list
        self._predicates = predicates
        self._payload = payload
        self._brightness_scale = brightness_scale
        self._white_value_scale = white_value_scale
        self._state = False
        self._brightness = None
        self._hs = None
        self._color_temp = None
        self._effect = None
        self._white_value = None
        self._supported_features = 0
        self._supported_features |= (
            predicates[CONF_RGB_PREDICATE] is not None and SUPPORT_COLOR)
        self._supported_features |= (
            predicates[CONF_BRIGHTNESS_PREDICATE] is not None and
            SUPPORT_BRIGHTNESS)
        self._supported_features |= (
            predicates[CONF_COLOR_TEMP_PREDICATE] is not None and
            SUPPORT_COLOR_TEMP)
        self._supported_features |= (
            False)
        self._supported_features |= (
            predicates[CONF_WHITE_VALUE_PREDICATE] is not None and
            SUPPORT_WHITE_VALUE)
        self._supported_features |= (
            predicates[CONF_XY_PREDICATE] is not None and SUPPORT_COLOR)
        if self._predicates[CONF_WHITE_VALUE_PREDICATE] is not None:
            self._white_value = 255
        if self._predicates[CONF_RGB_PREDICATE] is not None\
                or self._predicates[CONF_XY_PREDICATE] is not None:
            self._hs = (0, 0)
        if self._predicates[CONF_COLOR_TEMP_PREDICATE] is not None:
            self._color_temp = 150
        if self._predicates[CONF_EFFECT_PREDICATE] is not None:
            self._effect = 'none'
            
    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def hs_color(self):
        """Return the hs color value."""
        return self._hs

    @property
    def color_temp(self):
        """Return the color temperature in mired."""
        return self._color_temp

    @property
    def white_value(self):
        """Return the white property."""
        return self._white_value

    @property
    def should_poll(self):
        """No polling needed for a SEPA light."""
        return False

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return self._effect_list

    @property
    def effect(self):
        """Return the current effect."""
        return self._effect

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features

    async def async_turn_on(self, **kwargs):
        """Turn the device on.
        This method is a coroutine.
        """
        should_update = False
        
        pre = SEPA_NAMESPACE.replace('?x' ,self._predicates[CONF_STATE_PREDICATE])
        obj = "\"" + self._payload['on'] + "\""
        data = self._sparql.replace('?s' ,self._subject).replace('?p' ,pre).replace('?o' ,obj)
        
        if not sepa_update(self._update_url, data):
            _LOGGER.error("Failed sepa_update")
        should_update = True

        if ATTR_HS_COLOR in kwargs and \
           self._predicates[CONF_RGB_PREDICATE] is not None:

            hs_color = kwargs[ATTR_HS_COLOR]
            brightness = kwargs.get(
                ATTR_BRIGHTNESS, self._brightness if self._brightness else 255)
            rgb = color_util.color_hsv_to_RGB(
                hs_color[0], hs_color[1], brightness / 255 * 100)
         
            rgb_color_str = '{},{},{}'.format(*rgb)
            rgb_color_str = "\"" + rgb_color_str + "\""
            
            pre = SEPA_NAMESPACE.replace('?x' ,self._predicates[CONF_RGB_PREDICATE])
            obj =  rgb_color_str
            data = self._sparql.replace('?s' ,self._subject).replace('?p' ,pre).replace('?o' ,obj)
            
            if not sepa_update(self._update_url, data):
                _LOGGER.error("Failed sepa_update")

            self._hs = kwargs[ATTR_HS_COLOR]
            should_update = True

        if ATTR_HS_COLOR in kwargs and \
           self._predicates[CONF_XY_PREDICATE] is not None:

            xy_color = color_util.color_hs_to_xy(*kwargs[ATTR_HS_COLOR])
            xy_color_str = '{},{}'.format(*xy_color)
            xy_color_str = "\"" + xy_color_str + "\""
            
            pre = SEPA_NAMESPACE.replace('?x' ,self._predicates[CONF_XY_PREDICATE])
            obj =  xy_color_str
            data = self._sparql.replace('?s' ,self._subject).replace('?p' ,pre).replace('?o' ,obj)
            
            if not sepa_update(self._update_url, data):
                _LOGGER.error("Failed sepa_update")

            self._hs = kwargs[ATTR_HS_COLOR]
            should_update = True

        if ATTR_BRIGHTNESS in kwargs and \
           self._predicates[CONF_BRIGHTNESS_PREDICATE] is not None:
            percent_bright = float(kwargs[ATTR_BRIGHTNESS]) / 255
            device_brightness = int(percent_bright * self._brightness_scale)
            device_brightness_str = "\"" + str(device_brightness) + "\""
            
            pre = SEPA_NAMESPACE.replace('?x' ,self._predicates[CONF_BRIGHTNESS_PREDICATE])
            obj =  device_brightness_str
            data = self._sparql.replace('?s' ,self._subject).replace('?p' ,pre).replace('?o' ,obj)
            
            if not sepa_update(self._update_url, data):
                _LOGGER.error("Failed sepa_update")

            self._brightness = kwargs[ATTR_BRIGHTNESS]
            should_update = True

        if ATTR_COLOR_TEMP in kwargs and \
           self._predicates[CONF_COLOR_TEMP_PREDICATE] is not None:
            color_temp = int(kwargs[ATTR_COLOR_TEMP])
            color_temp_str = "\"" + str(color_temp) + "\""
            
            pre = SEPA_NAMESPACE.replace('?x' ,self._predicates[CONF_COLOR_TEMP_PREDICATE])
            obj =  color_temp_str
            data = self._sparql.replace('?s' ,self._subject).replace('?p' ,pre).replace('?o' ,obj)
            
            if not sepa_update(self._update_url, data):
                _LOGGER.error("Failed sepa_update")

            self._color_temp = kwargs[ATTR_COLOR_TEMP]
            should_update = True

        if ATTR_EFFECT in kwargs and \
           self._predicates[CONF_EFFECT_PREDICATE] is not None:
            effect = kwargs[ATTR_EFFECT]
            if effect in self._effect_list:
                
                pre = SEPA_NAMESPACE.replace('?x' ,self._predicates[CONF_EFFECT_PREDICATE])
                obj =  effect
                data = self._sparql.replace('?s' ,self._subject).replace('?p' ,pre).replace('?o' ,obj)
                
                if not sepa_update(self._update_url, data):
                    _LOGGER.error("Failed sepa_update")

                self._effect = kwargs[ATTR_EFFECT]
                should_update = True

        if ATTR_WHITE_VALUE in kwargs and \
           self._predicates[CONF_WHITE_VALUE_PREDICATE] is not None:
            percent_white = float(kwargs[ATTR_WHITE_VALUE]) / 255
            device_white_value = int(percent_white * self._white_value_scale)
            device_white_value_str = "\"" + str(device_white_value) + "\""
            
            pre = SEPA_NAMESPACE.replace('?x' ,self._predicates[CONF_WHITE_VALUE_PREDICATE])
            obj =  device_white_value_str
            data = self._sparql.replace('?s' ,self._subject).replace('?x' ,pre).replace('?o' ,obj)
            
            if not sepa_update(self._update_url, data):
                _LOGGER.error("Failed sepa_update")

            self._white_value = kwargs[ATTR_WHITE_VALUE]
            should_update = True

        # Optimistically assume that switch has changed state.
        self._state = True
        should_update = True

        if should_update:
            self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the device off.
        This method is a coroutine.
        """
        pre = SEPA_NAMESPACE.replace('?x' ,self._predicates[CONF_STATE_PREDICATE])
        obj =  "\"" + self._payload['off'] + "\""
        data = self._sparql.replace('?s' ,self._subject).replace('?p' ,pre).replace('?o' ,obj)
        
        if not sepa_update(self._update_url, data):
            _LOGGER.error("Failed sepa_update")

        # Optimistically assume that switch has changed state.
        self._state = False
        self.async_schedule_update_ha_state()
