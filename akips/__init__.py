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

    ### Entity commands

    def get_devices(self):
        ''' Pull a list of key attributes for all devices '''
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
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\S+)\s(\S+)\s(\S+)\s=\s(.*)$', line)
                if match:
                    device_name = match.group(1)
                    if device_name not in data:
                        data[device_name] = dict.fromkeys(attributes)
                    data[device_name][match.group(3)] = match.group(4)
                else:
                    logger.warning(f'Unable to parse output {line}')
            logger.debug(f'ok: {params["cmds"]}')   # pylint: disable=logging-fstring-interpolation
            return data
        return None

    def get_device(self, device, child='*'):
        ''' Pull the entire configuration for a single device '''
        params = {
            'cmds': f'mget * {device} {child} *'
        }
        text = self._get(params=params)
        if text:
            data = {}
            # Data comes back as 'plain/text' type so we have to parse it.
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\S+)\s(\S+)\s(\S+)\s=(\s(.*))?$', line)
                if match:
                    line_parent = match.group(1)
                    line_child = match.group(2)
                    line_attribute = match.group(3)
                    line_value = match.group(5)
                    if line_child not in data:
                        data[line_child] = {}
                    if line_value:
                        data[line_child][line_attribute] = line_value
                    else:
                        data[line_child][line_attribute] = ''
                elif line == '':
                    logger.debug(f'skipping blank line')
                else:
                    logger.warning(f'Unable to parse output "{line}"')
            logger.debug(f'ok: {params["cmds"]}')   # pylint: disable=logging-fstring-interpolation
            return data
        return None

    def get_device_by_ip(self, ipaddr):
        ''' Search for a device by an alternate IP address
        This makes use of a special site script and not the normal api '''
        params = {
            'function': 'web_find_device_by_ip',
            'ipaddr': ipaddr
        }
        text = self._get(section='/api-script/', params=params)
        if text:
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'IP Address (\S+) is configured on (\S+)', line)
                if match:
                    ip_query = match.group(1)
                    device_name = match.group(2)
                    logger.debug(f'ok: {ip_query} is on {device_name}')  # pylint: disable=logging-fstring-interpolation
                    return device_name
                else:
                    logger.warning(f'Unable to parse output {line}')
        return None

    def get_device_attribute(self, device, child, attribute):
        ''' Retrieve a single device configuration attribute '''
        params = {
            'cmds': f'get {device} {child} {attribute}' 
        }
        text = self._get(params=params)
        if text:
            data = None
            lines = text.split('\n')
            for line in lines:
                if line != '':
                    data = line
            logger.debug(f'ok: {params["cmds"]}')   # pylint: disable=logging-fstring-interpolation
            return data
        return None

    def get_status(self, status_type='ping'):
        ''' Bulk pull specific status values related to reachability '''
        if status_type == 'ups':
            params = { 'cmds': 'mget * * ups UPS-MIB.upsOutputSource' }
        elif status_type == 'ping':
            params = { 'cmds': 'mget * * ping4 PING.icmpState' }
        elif status_type == 'snmp':
            params = { 'cmds': 'mget * * sys SNMP.snmpState' }
        elif status_type == 'battery_test':
            params = { 'cmds': 'mget * * battery LIEBERT-GP-POWER-MIB.lgpPwrBatteryTestResult' }
        else:
            logger.error(f'Invalid get status type {status_type}')    # pylint: disable=logging-fstring-interpolation
            return None

        text = self._get(params=params)
        if text:
            data = []
            lines = text.split('\n')
            for line in lines:
                match = re.match("^(\S+)\s(\S+)\s(\S+)\s=\s(\S*),(\S*),(\S*),(\S*),(\S*)$", line)
                if match:
                    entry = {
                        'device': match.group(1),
                        'child': match.group(2),
                        'attribute':  match.group(3),
                        'index': match.group(4),
                        'state': match.group(5),
                        'device_added': match.group(6), # epoch in local timezone
                        'event_start': match.group(7),  # epoch in local timezone
                        'ipaddr': match.group(8)
                    }
                    data.append( entry )
            logger.debug("Found {} states in akips".format( len( data ) ))
            return data
        return None

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
                    event_start = datetime.fromtimestamp(int(match.group(7)),
                                                         tz=pytz.timezone(self.server_timezone))
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
                        data[name]['ping_state'] = match.group(5)
                        data[name]['index'] = match.group(4)
                        data[name]['device_added'] = datetime.fromtimestamp(int(match.group(6)), tz=pytz.timezone(self.server_timezone))
                        data[name]['event_start'] = datetime.fromtimestamp(int(match.group(7)), tz=pytz.timezone(self.server_timezone))
                        data[name]['ip4addr'] = match.group(8)
                    elif attribute == 'SNMP.snmpState':
                        data[name]['child'] = match.group(2),
                        data[name]['snmp_state'] = match.group(5)
                        data[name]['index'] = match.group(4)
                        data[name]['device_added'] = datetime.fromtimestamp(int(match.group(6)), tz=pytz.timezone(self.server_timezone))
                        data[name]['event_start'] = datetime.fromtimestamp(int(match.group(7)), tz=pytz.timezone(self.server_timezone))
                        data[name]['ip4addr'] = None
                    if event_start < data[name]['event_start']:
                        data[name]['event_start'] = event_start
            logger.debug("Found {} devices in akips".format(len(data)))
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

    ### Group commands

    def get_group_membership(self, device='*'):
        ''' Pull a list of device to group memberships '''
        params = {
            'cmds': f'mgroup device {device}',
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
                        data[match.group(1)] = match.group(2).split(',')
            # logger.debug("Found {} device and group mappings in akips".format(len(data.keys())))
            logger.debug(f'ok: {params["cmds"]}')   # pylint: disable=logging-fstring-interpolation
            return data
        return None

    def get_maintenance_mode(self):
        ''' Pull a list of devices in maintenance mode '''
        params = {
            'cmds': 'mget * * any group maintenance_mode',
        }
        text = self._get(params=params)
        if text:
            data = []
            # Data comes back as 'plain/text' type so we have to parse it
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\S+)$', line)
                if match:
                    data.append( match.group(1) )
            # logger.debug("Found {} devices in maintenance mode".format( len( data )))
            logger.debug(f'ok: {params["cmds"]}')   # pylint: disable=logging-fstring-interpolation
            return data
        return None

    def set_maintenance_mode(self, device_name, mode='True'):
        ''' Set maintenance mode on or off for a device '''
        params = {
            'function': 'web_manual_grouping',
            'type': 'device',
            'group': 'maintenance_mode',
            'device': device_name
        }
        if mode == 'True':
            params['mode'] = 'assign'
        else:
            params['mode'] = 'clear'
        text = self._get(section='/api-script',params=params)
        if text:
            logger.debug("Maintenance mode update result {}".format( text ))    # pylint: disable=logging-fstring-interpolation
            return text
        return None

    ### Event commands

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

    ### Time-series commands

    def get_high_latency(self,period='last1h'):
        ''' List devices with high pint RTT times '''
        # params={
        #     'cmds': f'mget {period} avg above 10000 rtt * /ping/ *'
        # }
        pass

    ### Availability commands

    def get_availability(self, period='last1h', report='ping4,snmp'):
        ''' Retrieve device availability statistics '''
        params = {
            'cmds': f'nm-availability mode device time {period} report {report}'
        }
        text = self._get(params=params)
        if text:
            data = []
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\S+),(\S+),(\S+),(\S+),(\S+),(\S+)$', line)
                if match:
                    entry = {
                        'parent': match.group(1),
                        'child': match.group(2),
                        'attribute': match.group(3),
                        'total_time': match.group(4),
                        'match_time': match.group(5),
                        'group_target': match.group(6),
                    }
                    data.append(entry)
            logger.debug("Found data")
            return data
        return None

    # Base operations

    def _parse_enum(self, values):
        ''' Attributes with a type of enum return five values separated by commas. '''
        match = re.match("^(\S*),(\S*),(\S*),(\S*),(\S*)$", values)
        if match:
            entry = {
                'number': match.group(1),       # list number (from MIB)
                'value': match.group(2),        # text value (from MIB)
                # 'created': match.group(3),      # time created (epoch timestamp)
                # 'modified': match.group(4),     # time modified (epoch timestamp)
                'description': match.group(5)   # child description
            }
            entry['created'] = datetime.fromtimestamp(int(match.group(3)), 
                                                        tz=pytz.timezone(self.server_timezone))
            entry['modified'] = datetime.fromtimestamp(int(match.group(4)), 
                                                        tz=pytz.timezone(self.server_timezone))
            return entry
        else:
            raise AkipsError(message=f'Not a ENUM type value: {values}')

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
