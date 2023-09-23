from akips import AKIPS


def test_placeholder():
    test_server = '127.0.0.1'
    api = AKIPS(test_server)
    assert api.username == 'api-ro', False
