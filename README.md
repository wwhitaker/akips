# akips
This akips module provides a simple way for python scripts to interact with 
the [AKiPS](http://akips.com) api interface.

## Example

    from akips import AKIPS

    api = AKIPS(akips.example.com,username='api-ro',password='something')

    devices = api.get_devices()

    for device in devices:
        print("Device entry: {}".format(device))

