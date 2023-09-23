[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/akips.svg)](https://img.shields.io/pypi/pyversions/akips)
[![PyPI](https://img.shields.io/pypi/v/akips.svg)](https://pypi.python.org/pypi/akips)
[![Downloads](https://static.pepy.tech/badge/akips)](https://pepy.tech/project/akips)
[![GitHub contributors](https://img.shields.io/github/contributors/wwhitaker/akips.svg)](https://GitHub.com/wwhitaker/akips/graphs/contributors/)

akips
=======
This akips module provides a simple way for python scripts to interact with 
the [AKiPS Network Monitoring Software](http://akips.com) API interface.

## Installation

To install akips, simply us pip:

```
$ pip install akips
```

## Usage Example

```py
from akips import AKIPS

api = AKIPS('akips.example.com',username='api-ro',password='something')

devices = api.get_devices()
for name, fields in devices.items():
    print("Device: {} {}".format(name,fields))

```

## Bugs/Requests

Please use the [GitHub issue tracker](https://github.com/wwhitaker/akips/issues) 
to submit bugs or request features.
