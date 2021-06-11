import json

from wedos_api import WAPI

if __name__ == '__main__':
    def main() -> None:
        from os import environ
        dns_user, dns_secret = environ.get('DNS_USER'), environ.get('DNS_KEY')
        assert dns_user and dns_secret
        api = WAPI(dns_user, dns_secret)
        # api.set_test_mode(True)
        print(json.dumps(api.domains_as_dict, indent=1))

    main()
