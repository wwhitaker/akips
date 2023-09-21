import re
import logging
import requests

# Logging configuration
logger = logging.getLogger(__name__)

class AKIPS:
    # Class to handle interactions with AKiPS API

    def __init__(self, server, username='api-ro', password=None, verify=True):
        # Connect to AKiPS instance
        self.server = server
        self.username = username
        self.password = password
        self.verify = verify
        self.session = requests.Session()

    def get_devices(self):
        pass

    def get_events(self, type='all', period='last1h'):
        ''' Pull a list of events.  Command syntax:
            mget event {all,critical,enum,threshold,uptime}
            time {time filter} [{parent regex} {child regex}
            {attribute regex}] [profile {profile name}]
            [any|all|not group {group name} ...] '''

        params = {
            'cmds': 'mget event {} time {}'.format(type,period)
        }
        text = self.get(params=params)
        if text:
            data = []
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(?P<epoch>\S+)\s(?P<parent>\S+)\s(?P<child>\S+)\s(?P<attribute>\S+)\s(?P<type>\S+)\s(?P<flags>\S+)\s(?P<details>.*)$', line)
                if match:
                    entry = {
                        'epoch': match.group('epoch'),
                        'parent': match.group('parent'),
                        'child': match.group('child'),
                        'attribute': match.group('attribute'),
                        'type': match.group('type'),
                        'flags': match.group('flags'),
                        'details': match.group('details'),
                    }
                    data.append(entry)
            logger.debug("Found {} events of type {} in akips".format( len( data ), type))
            return data
        return None

    def get(self, section='/api-db/', params=None):
        ''' Search and Read Objects: GET Method '''
        url = 'https://' + self.server + section
        params['username'] = self.username
        params['password'] = self.password
        # GET requests have 2 args: URL, HEADERS
        r = self.session.get(url, params=params, verify=self.verify)

        # Return Status/Errors
        # 200	Normal return. Referenced object or result of search in body.
        if r.status_code != 200:
            # Errors come back in the page text and look like below:
            # ERROR: api-db invalid username/password
            logger.warning('WAPI request finished with error, response code: %i %s'
                        % (r.status_code, r.reason))
            #json_object = r.json()
            #logger.warning('Error message: %s' % json_object['Error'])
            return None
        else:
            logger.debug('API request finished successfully, response code: %i %s'
                        % (r.status_code, r.reason))
            if re.match(r'^ERROR:',r.text):
                logger.warn("AKIPS API failed with {}".format(r.text))
                return r.text
            else:
                return r.text