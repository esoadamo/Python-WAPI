import json
from datetime import datetime
from hashlib import sha1
from typing import Optional, Dict, Any, Iterator, List

import requests as req

from .models import WAPIRequest, WAPIResponse, WAPIDomainRecordType, WAPIDomainRecord, WAPIDomainStatus


class WAPIError(Exception):
    pass


class WAPI:
    """
    Manipulator with WEDOS API
    """
    date_format = '%Y-%m-%d %H:%M:%S'

    def __init__(self, user: str, key: str):
        """
        Initializes Wedos API with user and key
        :param user: user
        :param key: secret key
        """
        self.__key = key
        self.__user = user
        self.__test_mode = False

    def set_test_mode(self, enabled: bool) -> None:
        """
        Enables/disables test mode
        :param enabled: True if to enable test mode
        :return: None
        """
        self.__test_mode = enabled

    def __get_auth(self) -> str:
        """
        Computes authorization secret
        :return: current authorization secret
        """
        return sha1(
            (self.__user + sha1(self.__key.encode('utf8')).hexdigest() + datetime.now().strftime('%H')).encode('utf8')
        ).hexdigest()

    def make_request(self,
                     command: str,
                     data: Optional[Dict[str, Any]] = None,
                     command_id: Optional[str] = None) -> WAPIResponse:
        """
        Makes a single request to the WEDOS API
        :param command: command to run
        :param data: data passed to the command
        :param command_id: command id for later identification
        :return: reponse
        """
        request: WAPIRequest = WAPIRequest(
            command=command,
            auth=self.__get_auth(),
            user=self.__user,
            test=self.__test_mode,
            data=data,
            command_id=command_id
        )

        resp: dict = req.post(
            'https://api.wedos.com/wapi/json',
            data={'request': json.dumps({'request': {
                'command': request.command,
                'auth': request.auth,
                'user': request.user,
                'test': 1 if request.test else 0,
                'data': request.data,
                'clTRID': request.command
            }})}
        ).json()['response']

        if str(resp.get('code', '3000')).startswith('1'):
            return WAPIResponse(
                code=resp['code'],
                result=resp['result'],
                timestamp=resp['timestamp'],
                command_id=resp['clTRID'],
                server_command_id=resp['svTRID'],
                command=resp['command'],
                data=resp.get('data'),
                test=int(resp.get('test', 0)) == 1
            )
        raise WAPIError(f"WAPI error: {json.dumps(resp)}")

    def ping(self) -> bool:
        """
        Tries to ping the server, returns True on success, False on WAPIError
        :return: returns True on success, False on WAPIError
        """
        try:
            self.make_request('ping')
            return True
        except WAPIError:
            return False

    def open_domain(self, domain: str) -> "WAPIDomain":
        """
        Creates new WAPIDomain for given domain
        :param domain: domain to be operated
        :return: WAPIDomain instance
        """
        return WAPIDomain(domain, self)

    @property
    def domains(self) -> Iterator["WAPIDomain"]:
        """
        Iterates over all domains
        :return: domain instances
        """
        request_data = self.make_request('dns-domains-list').data
        if not request_data:
            return []
        domains_dict: Dict[str, dict] = request_data['domain']
        if not domains_dict:
            return []
        for domain_dict in domains_dict.values():
            yield WAPIDomain(domain_dict['name'],
                             self,
                             is_primary=domain_dict['type'] == 'primary',
                             status=self.__str_to_domain_status(domain_dict['status'])
                             )

    @property
    def domains_as_dict(self) -> Dict[str, List[Dict]]:
        """
        Returns all domains in dictionary format
        domain: records
        :return: all domains in dictionary
        """
        return {domain.domain_name: list(domain.records_as_dict) for domain in self.domains}

    @staticmethod
    def __str_to_domain_status(domain_status_str: str) -> WAPIDomainStatus:
        domain_status_str = domain_status_str.upper()
        for v, t in WAPIDomainStatus.__members__.items():
            if v == domain_status_str:
                return t
        raise WAPIError(f"Unknown record type '{domain_status_str}'")


class WAPIDomain:
    """
    Single user owned domain
    """
    def __init__(self,
                 domain: str,
                 api: WAPI,
                 is_primary: Optional[bool] = None,
                 status: Optional[WAPIDomainStatus] = None,
                 ) -> None:
        """
        Initializes domain
        :param domain: example.com
        :param api: controlling WAPI instance
        """
        self.__api = api
        self.__domain = domain
        self.__is_primary = is_primary
        self.__status = status

    @property
    def domain_name(self) -> str:
        """
        Gets domain name
        :return: domain name
        """
        return self.__domain

    @property
    def records(self) -> Iterator[WAPIDomainRecord]:
        """
        Loads all record rows from this domain and returns it
        :return: all record rows from this domain
        """
        request_data = self.__api.make_request('dns-rows-list', {'domain': self.__domain}).data
        if not request_data:
            return []
        records_str: List[dict] = request_data['row']
        if not records_str:
            return []
        return map(WAPIDomain.__row_dict_to_row, records_str)

    @property
    def records_as_dict(self) -> Iterator[Dict]:
        """
        Loads all record rows from this domain and returns it as dictionary
        :return: all record rows from this domain
        """
        for x in self.records:
            d = dict(x._asdict())
            d['record_type'] = d['record_type'].value
            d['changed'] = d['changed'].strftime(WAPI.date_format)
            yield d

    def add_record(self,
                   name: str,
                   record_type: WAPIDomainRecordType,
                   content: str,
                   ttl: int = 1800
                   ) -> None:
        """
        Adds new record
        :param name: name (subdomain) of the record
        :param record_type: type of the record
        :param content: content of the record
        :param ttl: time to live in seconds
        :return: None
        """
        self.__api.make_request('dns-row-add', {
            'domain': self.__domain,
            'name': name,
            'ttl': ttl,
            'type': record_type.value,
            'rdata': content
        })

    def remove_record(self, record: WAPIDomainRecord) -> None:
        """
        Removes single row record from this domain
        :param record: record to remove
        :return: None
        """
        self.__api.make_request('dns-row-delete', {
            'domain': self.__domain,
            'row_id': record.id
        })

    def commit(self) -> None:
        """
        Immediately commits changes
        :return: None
        """
        self.__api.make_request('dns-domain-commit', {'name': self.__domain})

    def __str__(self) -> str:
        r = f"Domain<{self.__domain}"
        if self.__is_primary is not None:
            r += ", " + ("PRIMARY" if self.__is_primary else "SECONDARY")
        if self.__status is not None:
            r += f", {self.__status.value}"
        r += ">"
        return r

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def __str_to_record_type(record_type_str: str) -> WAPIDomainRecordType:
        record_type_str = record_type_str.upper()
        for v, t in WAPIDomainRecordType.__members__.items():
            if v == record_type_str:
                return t
        raise WAPIError(f"Unknown record type '{record_type_str}'")

    @staticmethod
    def __row_dict_to_row(row_dict: dict) -> WAPIDomainRecord:
        return WAPIDomainRecord(
            id=int(row_dict['ID']),
            name=row_dict['name'],
            ttl=int(row_dict['ttl']),
            record_type=WAPIDomain.__str_to_record_type(row_dict['rdtype']),
            content=row_dict['rdata'],
            changed=datetime.strptime(row_dict['changed_date'], WAPI.date_format),
            author_comment=row_dict['author_comment']
        )

