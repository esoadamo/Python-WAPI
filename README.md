# WEDOS API

A Python client for wedos.com API

## Installation

```shell
pip install git+https://github.com/esoadamo/Python-WAPI.git
```

## Sample Usage

```python
from wedos_api import WAPI
from os import environ
dns_user, dns_secret = environ.get('DNS_USER'), environ.get('DNS_KEY')
assert dns_user and dns_secret
api = WAPI(dns_user, dns_secret)
print(list(api.domains))
```
