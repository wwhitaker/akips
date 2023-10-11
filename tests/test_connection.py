import unittest
from unittest.mock import MagicMock, patch
from akips import AKIPS, AkipsError


class AkipsTest(unittest.TestCase):

    @patch('requests.Session.get')
    def test_akips_error(self, session_mock: MagicMock):
        r_text = "ERROR: api-db invalid username/password"

        session_mock.return_value.ok = True
        session_mock.return_value.status_code = 200
        session_mock.return_value.text = r_text
        self.assertIsInstance(session_mock, MagicMock)

        api = AKIPS('127.0.0.1')

        self.assertFalse(session_mock.called)
        self.assertRaises(AkipsError, api.get_devices)
        self.assertTrue(session_mock.called)

    @patch('requests.Session.get')
    def test_get_devices(self, session_mock: MagicMock):
        r_text = """192.168.1.29 sys ip4addr = 192.168.1.29
192.168.1.29 sys SNMPv2-MIB.sysDescr = VMware ESXi 6.5.0 build-8294253 VMware Inc. x86_64
192.168.1.29 sys SNMPv2-MIB.sysName = server.example.com
192.168.1.30 sys ip4addr = 192.168.1.30
"""

        session_mock.return_value.ok = True
        session_mock.return_value.status_code = 200
        session_mock.return_value.text = r_text

        api = AKIPS('127.0.0.1')
        devices = api.get_devices()
        self.assertEqual(devices['192.168.1.29']['ip4addr'], '192.168.1.29')
        self.assertEqual(devices['192.168.1.29']['SNMPv2-MIB.sysDescr'], 'VMware ESXi 6.5.0 build-8294253 VMware Inc. x86_64')
        self.assertEqual(devices['192.168.1.29']['SNMPv2-MIB.sysName'], 'server.example.com')
        self.assertEqual(devices['192.168.1.30']['ip4addr'], '192.168.1.30')

    @patch('requests.Session.get')
    def test_get_unreachable(self, session_mock: MagicMock):
        r_text = """192.168.248.54 ping4 PING.icmpState = 1,down,1484685257,1657029502,192.168.248.54
192.168.248.54 sys SNMP.snmpState = 1,down,1484685257,1657029499,
CrN-082-AP ping4 PING.icmpState = 1,down,1605595895,1656331597,192.168.94.63
CrN-082-AP ping4 PING.icmpState = 1,down,1641624705,1646101757,192.168.94.112
"""
        session_mock.return_value.ok = True
        session_mock.return_value.status_code = 200
        session_mock.return_value.text = r_text

        api = AKIPS('127.0.0.1')
        devices = api.get_unreachable()
