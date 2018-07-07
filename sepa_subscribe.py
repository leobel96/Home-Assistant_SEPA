import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.components.sepa import sepa_subscribe
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

SEPA_SUBSCRIBE_ALL = 'select * where {?s ?p ?o}'
CONF_SUBSCRIBE_OBJECT = 'subscribe_object'
CONF_SUBSCRIBE_PREDICATE = 'subscribe_predicate'
CONF_SUBSCRIBE_SUBJECT = 'subscribe_subject'
CONF_SUBSCRIBE_URL = 'subscribe_url'
CONF_SUBSCRIPTIONS = 'subscriptions'

_SUBSCRIPTION_SCHEME = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_SUBSCRIBE_URL): cv.string,
    vol.Optional(CONF_SUBSCRIBE_SUBJECT): cv.string,
    vol.Optional(CONF_SUBSCRIBE_PREDICATE): cv.string,
    vol.Optional(CONF_SUBSCRIBE_OBJECT): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SUBSCRIPTIONS): [_SUBSCRIPTION_SCHEME],    
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the SEPA_subscribe sensor platform."""

    subscription_url = config.get(CONF_SUBSCRIBE_URL, None)
    subscriptions = []
    
    for subscription in config.get(CONF_SUBSCRIPTIONS):
        name = subscription.get(CONF_NAME)
        url = subscription.get(CONF_SUBSCRIBE_URL)
        subject = subscription.get(CONF_SUBSCRIBE_SUBJECT)
        predicate = subscription.get(CONF_SUBSCRIBE_PREDICATE)
        _object = subscription.get(CONF_SUBSCRIBE_OBJECT)

        sensor = SEPASubscribeSensor(
            name, url, subject, predicate, _object)
        subscriptions.append(sensor)

    add_devices(subscriptions, True)

class SEPASubscribeSensor(Entity):
    """Representation of an SEPA subscribe sensor."""

    def __init__(self, name, subscribe_url, subject, predicate, _object):
        """Initialize the SEPA Subscribe sensor."""
        self._name = name
        self._subscription_url = subscribe_url
        self._state = None
        self._attributes = None
        self._sparql = SEPA_SUBSCRIBE_ALL
        if subject is not None:
            self._sparql = self._sparql.replace('?s' ,subject)
        if predicate is not None:
            self._sparql = self._sparql.replace('?p' ,predicate)
        if _object is not None:
            self._sparql = self._sparql.replace('?o' ,_object)
        self._ws = sepa_subscribe(self._subscription_url, self._sparql)

    @property
    def name(self):
        """Return the name of the subscription."""
        return self._name

    @property
    def state(self):
        """Return the query's current state."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def update(self):
        """Retrieve sensor data from the query."""
        result = self._ws.message
        if result is not None:
            self._state = result['notification']['addedResults']['results']['bindings'][0]['o']['value']