# implementation of the named queries
# based on https://vliz.atlassian.net/wiki/spaces/VMDCOS/pages/204374034/First+set+of+queries+to+run+on+3store+of+emo+bon+data

from udal.specification import NamedQueryInfo
import udal.specification as udal
from typing import Any, Dict, List, Optional, Tuple, Union, Literal
import typing


QueryName = Literal[
    "urn:embrc.eu:emobon:observatories",
    "urn:embrc.eu:emobon:observations",
    "urn:embrc.eu:emobon:observatory-overview",
    "urn:embrc.eu:emobon:observatory-overview-totals",
    "urn:embrc.eu:emobon:measured-values",
    "urn:embrc.eu:emobon:sop-usage",
    "urn:embrc.eu:emobon:instrument-usage",
    "urn:embrc.eu:emobon:all-samples",
]
