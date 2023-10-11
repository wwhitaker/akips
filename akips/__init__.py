''' Base module '''
__version__ = '0.1.5'

import re
import logging
from datetime import datetime
import requests
import pytz

from akips.exceptions import AkipsError

# Logging configuration
logger = logging.getLogger(__name__)


class AKIPS:
    ''' Class to handle interactions with AKiPS API '''
    server_timezone = 'America/New_York'

    def __init__(self, server, username='api-ro', password=None, verify=True):
        ''' Connect to the AKiPS instance '''
        self.server = server
        self.username = username
        self.password = password
        self.verify = verify
        self.session = requests.Session()

        if not verify:
            requests.packages.urllib3.disable_warnings()    # pylint: disable=no-member

    def get_devices(self):
        ''' Pull a list of key attributes for all devices in akips '''
        attributes = [
            'ip4addr',
            'SNMPv2-MIB.sysName',
            'SNMPv2-MIB.sysDescr',
            'SNMPv2-MIB.sysLocation'
        ]
        cmd_attributes = "|".join(attributes)
        params = {
            'cmds': f'mget text * sys /{cmd_attributes}/',
        }
        text = self._get(params=params)
        if text:
            data = {}
            # Data comes back as 'plain/text' type so we have to parse it
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\S+)\s(\S+)\s(\S+)\s=\s(.*)$', line)
                if match:
                    if match.group(1) not in data:
                        # Populate a default entry for all desired fields
                        data[match.group(1)] = dict.fromkeys(attributes)
                    # Save this attribute value to data
                    data[match.group(1)][match.group(3)] = match.group(4)
            logger.debug("Found {} devices in akips".format(len(data.keys())))
            return data
        return None

    def get_device(self, name):
        ''' Pull the entire configuration for a single device '''
        params = {
            'cmds': f'mget * {name} * *'
        }
        text = self._get(params=params)
        if text:
            data = {}
            # Data comes back as 'plain/text' type so we have to parse it.  Example:
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\S+)\s(\S+)\s(\S+)\s=(\s(.*))?$', line)
                if match:
                    name = match.group(1)
                    if match.group(2) not in data:
                        # initialize the dict of attributes
                        data[ match.group(2) ] = {}
                    if match.group(5):
                        # Save this attribute value to data
                        data[ match.group(2) ][ match.group(3) ] = match.group(5)
                    else:
                        # save a blank string if there was nothing after equals
                        data[ match.group(2) ][ match.group(3) ] = ''
            if name:
                data['name'] = name
            logger.debug("Found device {} in akips".format( data ))
            return data
        return None

    def get_device_by_ip(self, ipaddr, use_cache=True):
        ''' Search for a device by an alternate IP address
        This makes use of a special site script and not the normal api '''
        # params = {
        #     'function': 'web_find_device_by_ip',
        #     'ipaddr': ipaddr
        # }
        # section = '/api-script/'
        pass

    def get_unreachable(self):
        ''' Pull a list of unreachable IPv4 ping devices '''
        params = {
            'cmds': 'mget * * * /PING.icmpState|SNMP.snmpState/ value /down/',
        }
        text = self._get(params=params)
        data = {}
        if text:
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\S+)\s(\S+)\s(\S+)\s=\s(\S+),(\S+),(\S+),(\S+),(\S+)?$', line)
                if match:
                    # epoch fields are in the server's timezone
                    name = match.group(1)
                    attribute = match.group(3)
                    event_start = datetime.fromtimestamp(int( match.group(7) ), tz=pytz.timezone(self.server_timezone))
                    if name not in data:
                        # populate a starting point for this device
                        data[name] = {
                            'name': name,
                            'ping_state': 'n/a',
                            'snmp_state': 'n/a',
                            'event_start': event_start  # epoch in local timezone
                        }
                    if attribute == 'PING.icmpState':
                        data[name]['child'] = match.group(2),
                        data[name]['ping_state'] =  match.group(5)
                        data[name]['index'] = match.group(4)
                        data[name]['device_added'] = datetime.fromtimestamp(int( match.group(6) ), tz=pytz.timezone(self.server_timezone))
                        data[name]['event_start'] = datetime.fromtimestamp(int( match.group(7) ), tz=pytz.timezone(self.server_timezone))
                        data[name]['ip4addr'] = match.group(8)
                    elif attribute == 'SNMP.snmpState':
                        data[name]['child'] = match.group(2),
                        data[name]['snmp_state'] =  match.group(5)
                        data[name]['index'] = match.group(4)
                        data[name]['device_added'] = datetime.fromtimestamp(int( match.group(6) ), tz=pytz.timezone(self.server_timezone))
                        data[name]['event_start'] = datetime.fromtimestamp(int( match.group(7) ), tz=pytz.timezone(self.server_timezone))
                        data[name]['ip4addr'] = None
                    if event_start < data[name]['event_start']:
                        data[name]['event_start'] = event_start
            logger.debug("Found {} devices in akips".format( len( data )))
            logger.debug("data: {}".format(data))

        # for name in data:
        #     # Fill in the unreported gaps so we have ping4 and snmp up/down data
        #     if data[name]['ping_state'] == 'n/a':
        #         ping_status = self.get_status(device=name, child='ping4', attribute='PING.icmpState')

        #     if data[name]['snmp_state'] == 'n/a':
        #         snmp_status = self.get_status(device=name, child='sys', attribute='SNMP.snmpState')

        # ideal data return based on unreachable device report
        # Device, Ping4 (state,IPv4), SNMP (state,IP), Last Change (... ago), Location, Description

        return data

    def get_group_membership(self):
        ''' Pull a list of device to group memberships '''
        params = {
            'cmds': 'mgroup device *',
        }
        text = self._get(params=params)
        if text:
            data = {}
            # Data comes back as 'plain/text' type so we have to parse it
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\S+)\s=\s(.*)$', line)
                if match:
                    if match.group(1) not in data:
                        # Populate a default entry for all desired fields
                        data[ match.group(1) ] = match.group(2).split(',')
            logger.debug("Found {} device and group mappings in akips".format( len( data.keys() )))
            return data
        return None

    def get_maintenance_mode(self):
        ''' Pull a list of devices in maintenance mode '''
        # params = {
        #     'cmds': 'mget * * any group maintenance_mode',
        # }
        pass

    def set_maintenance_mode(self, device_name, mode='True'):
        ''' Set maintenance mode on or off for a device '''
        # params = {
        #     'function': 'web_manual_grouping',
        #     'type': 'device',
        #     'group': 'maintenance_mode',
        #     'device': device_name
        # }
        pass

    def get_status(self, device='*', child='*', attribute='*'):
        ''' Pull the status values we are most interested in '''
        pass

    def get_events(self, event_type='all', period='last1h'):
        ''' Pull a list of events.  Command syntax:
            mget event {all,critical,enum,threshold,uptime}
            time {time filter} [{parent regex} {child regex}
            {attribute regex}] [profile {profile name}]
            [any|all|not group {group name} ...] '''

        params = {
            'cmds': f'mget event {event_type} time {period}'
        }
        text = self._get(params=params)
        if text:
            data = []
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\S+)\s(\S+)\s(\S+)\s(\S+)\s(\S+)\s(\S+)\s(.*)$', line)
                if match:
                    entry = {
                        'epoch': match.group(1),
                        'parent': match.group(2),
                        'child': match.group(3),
                        'attribute': match.group(4),
                        'type': match.group(5),
                        'flags': match.group(6),
                        'details': match.group(7),
                    }
                    data.append(entry)
            logger.debug("Found {} events of type {} in akips".format(len(data), type))
            return data
        return None

    def _get(self, section='/api-db/', params=None, timeout=30):
        ''' Call HTTP GET against the AKiPS server '''
        server_url = 'https://' + self.server + section
        params['username'] = self.username
        params['password'] = self.password

        try:
            r = self.session.get(server_url, params=params, verify=self.verify, timeout=timeout)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logger.error(errh)
            raise
        except requests.exceptions.ConnectionError as errc:
            logger.error(errc)
            raise
        except requests.exceptions.Timeout as errt:
            logger.error(errt)
            raise
        except requests.exceptions.RequestException as err:
            logger.error(err)
            raise

        # AKiPS can return a raw error message if something fails
        if re.match(r'^ERROR:', r.text):
            logger.error("Web API request failed: {}".format(r.text))
            raise AkipsError(message=r.text)
        else:
            return r.text
