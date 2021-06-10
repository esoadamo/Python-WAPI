from typing import Dict, Any, Optional, NamedTuple
from enum import Enum
from datetime import datetime


class WAPIRequest(NamedTuple):
    user: str
    auth: str
    command: str
    command_id: Optional[str]
    data: Optional[Dict[str, Any]]
    test: Optional[bool]


class WAPIResponse(NamedTuple):
    code: int
    result: str
    timestamp: int
    command_id: str
    server_command_id: str
    command: str
    data: Dict[str, Any]
    test: bool


class WAPIDomainStatus(Enum):
    ACTIVE = 'ACTIVE'


class WAPIDomainRecordType(Enum):
    A = 'A'
    AAAA = 'AAAA'
    MX = 'MX'
    SSHFP = 'SSHFP'
    TXT = 'TXT'


class WAPIDomainRecord(NamedTuple):
    id: int
    name: str
    ttl: int
    record_type: WAPIDomainRecordType
    content: str
    changed: datetime
    author_comment: str
