import os
import logging
from unittest.mock import MagicMock, patch
from akips import AKIPS

akips_server = os.getenv('AKIPS_SERVER', '')
akips_username = os.getenv('AKIPS_USERNAME', '')
akips_password = os.getenv('AKIPS_PASSWORD', '')

# Example code
# api = AKIPS(akips_server,username=akips_username,password=akips_password,verify=False)
# devices = api.get_devices()
# for device in devices:
#     print("device: {}".format(device))

# def test_placeholder():
#     assert True

# def test_auth_failure():
#     r_text = "ERROR: api-db invalid username/password"

#     assert True

# @patch("requests.Session")
# def test_something(session_mock: MagicMock):
#     r_text = "ERROR: api-db invalid username/password"

#     # Setup mocks
#     session_mock.get.return_value = response(ok=True, return_code=200, r_text)

#     # Run tests
#     akips = AKIPS()
#     response = akips.get_devices()
    
#     # assert we got the right things
#     assert response['foo'] == 'bar'

#     # Assert the right HTTP call got made
#     sesison_mock.get.assert_called_with("foo", ...)





