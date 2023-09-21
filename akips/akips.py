import os
import logging
import requests

class AKIPS:
    # Class to handle interactions with the NIT database
    akips_server = os.getenv('AKIPS_SERVER', '')
    akips_username = os.getenv('AKIPS_USERNAME', '')
    akips_password = os.getenv('AKIPS_PASSWORD', '')
    session = requests.Session()

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
        url = 'https://' + self.akips_server + section
        logger.debug("WAPI GET %s" % (url))
        logger.debug("WAPI GET params: " + pprint.pformat(params))
        params['username'] = self.akips_username
        params['password'] = self.akips_password
        # GET requests have 2 args: URL, HEADERS
        # Verify is off because the 'certifi' python module is missing the InCommon interim CA
        r = self.session.get(url, params=params, verify=False)

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