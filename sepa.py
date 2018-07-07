import logging
import json
try:
    import thread
except ImportError:
    import _thread as thread
import time

from requests import post
import websocket

_LOGGER = logging.getLogger(__name__)

CONF_QUERY_URL = 'query_url'
CONF_SUBSCRIBE_URL = 'subscribe_url'
CONF_UPDATE_URL = 'update_url'


def sepa_query(url, query):
  
    query_header = {"Content-Type":"application/sparql-query", "Accept":"application/json"}

    try:
        result = post(url, data=query, headers=query_header).json()
    except:
        _LOGGER.error("Couldn't connect using url: %s", url)
        return
  
    if 'error' in result.keys():
        _LOGGER.error("Broker returned error with query: %s", query)
        return
  
    return result
  
def sepa_update(url, update):
  
    update_header = {"Content-Type":"application/sparql-update", "Accept":"application/json"}
  
    try:
        result = post(url, data=update, headers=update_header).json()
    except:
        _LOGGER.error("Couldn't connect using url: %s", url)
        return False
  
    if 'error' in result.keys():
        _LOGGER.error("Broker returned error with update: %s", update)
        return False
  
    return True


class sepa_subscribe:
  
    def __init__(self, url, sparql):
        self._sparql = sparql
        self._subscription_url = url
        self.message = None
        self._request = '{"subscribe":{"sparql":' + "\"" + sparql + "\"" + '}}'
        self._first_message = True
    
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(self._subscription_url,
                on_message = self.on_message,
                on_error = self.on_error,
                on_close = self.on_close)
        ws.on_open = self.on_open
  
        def ws_cycle(*args):
            ws.run_forever()
        thread.start_new_thread(ws_cycle,())
  
    def on_message(self, ws, message):
        self.message = json.loads(message)
        if self._first_message:
            if 'error' in self.message.keys():
                _LOGGER.error("Broker returned an error with subscription: %s", self._request)
                return
            self._first_message = False
        ##print(message)

    def on_error(self, ws, error):
         _LOGGER.error("Broker returned error: %s with subscription: %s" % (error, self._request))

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        def run(*args):
            ws.send(self._request)

        thread.start_new_thread(run, ())
