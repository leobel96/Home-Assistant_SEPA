import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.components.sepa import sepa_query
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['xmltodict==0.11.0']

_LOGGER = logging.getLogger(__name__)

SEPA_QUERY_ALL = "select * where {?s ?p ?o }"
CONF_QUERIES = 'queries'
CONF_QUERY_OBJECT = 'query_object'
CONF_QUERY_PREDICATE = 'query_predicate'
CONF_QUERY_SUBJECT = 'query_subject'
CONF_QUERY_URL = 'query_url'

_QUERY_SCHEME = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_QUERY_URL): cv.string,
    vol.Optional(CONF_QUERY_SUBJECT): cv.string,
    vol.Optional(CONF_QUERY_PREDICATE): cv.string,
    vol.Optional(CONF_QUERY_OBJECT): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_QUERIES): [_QUERY_SCHEME],    
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the SEPA_query sensor platform."""
    
    query_url = config.get(CONF_QUERY_URL, None)
    queries = []

    for query in config.get(CONF_QUERIES):
        name = query.get(CONF_NAME)
        url = query.get(CONF_QUERY_URL)
        subject = query.get(CONF_QUERY_SUBJECT)
        predicate = query.get(CONF_QUERY_PREDICATE)
        _object = query.get(CONF_QUERY_OBJECT)

        sensor = SEPAQuerySensor(
            name, url, subject, predicate, _object)
        queries.append(sensor)

    add_devices(queries, True)

class SEPAQuerySensor(Entity):
    """Representation of an SQL sensor."""

    def __init__(self, name, url, subject, predicate, _object):
        """Initialize the SEPA Query sensor."""
        self._name = name
        self._url = url
        self._state = None
        self._attributes = None
        self._sparql = SEPA_QUERY_ALL
        if subject is not None:
            self._sparql = self._sparql.replace('?s' ,subject)
        if predicate is not None:
            self._sparql = self._sparql.replace('?p' ,predicate)
        if _object is not None:
            self._sparql = self._sparql.replace('?o' ,_object)

    @property
    def name(self):
        """Return the name of the query."""
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
        result = sepa_query(self._url, self._sparql)
        if result is not None:
            self._state = result['results']['bindings'][0]['o']['value']