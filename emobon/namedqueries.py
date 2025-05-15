# implementation of the named queries
# based on https://vliz.atlassian.net/wiki/spaces/VMDCOS/pages/204374034/First+set+of+queries+to+run+on+3store+of+emo+bon+data

from udal.specification import NamedQueryInfo
import udal.specification as udal
from typing import Tuple, Literal
import typing


QueryName = Literal[
    "urn:embrc.eu:emobon:observatory-overview",
    "urn:embrc.eu:emobon:observatory-overview-totals",
    "urn:embrc.eu:emobon:measured-values",
    "urn:embrc.eu:emobon:sop-usage",
    "urn:embrc.eu:emobon:instrument-usage",
    "urn:embrc.eu:emobon:all-samples",
]
"""Type to help development restricting query names to existing ones."""

QUERY_NAMES: Tuple[QueryName, ...] = typing.get_args(QueryName)
"""List of the supported query names."""

# Ordered alphabetically
QUERY_REGISTER: dict[QueryName, NamedQueryInfo] = {
    "urn:embrc.eu:emobon:observatory-overview": NamedQueryInfo(
        "urn:embrc.eu:emobon:observatory-overview"
    ),
    "urn:embrc.eu:emobon:observatory-overview-totals": NamedQueryInfo(
        "urn:embrc.eu:emobon:observatory-overview-totals"
    ),
    "urn:embrc.eu:emobon:measured-values": NamedQueryInfo(
        "urn:embrc.eu:emobon:measured-values",
        {
            "observatory_id": ["str", udal.tlist("str")],
        },
    ),
    "urn:embrc.eu:emobon:sop-usage": NamedQueryInfo("urn:embrc.eu:emobon:sop-usage"),
    "urn:embrc.eu:emobon:instrument-usage": NamedQueryInfo(
        "urn:embrc.eu:emobon:instrument-usage"
    ),
    "urn:embrc.eu:emobon:all-samples": NamedQueryInfo(
        "urn:embrc.eu:emobon:all-samples"
    ),
}
