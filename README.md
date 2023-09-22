# akips
This akips module provides a simple way for python scripts to interact with 
the [AKiPS Network Monitoring Software](http://akips.com) API interface.

## Example

```py
from akips import AKIPS

api = AKIPS('akips.example.com',username='api-ro',password='something')

devices = api.get_devices()
for name, fields in devices.items():
    print("Device: {} {}".format(name,fields))

```

# Bugs/Requests

Please use the [GitHub issue tracker](https://github.com/wwhitaker/akips/issues) 
to submit bugs or request features.
