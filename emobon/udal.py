import udal.specification as udal
from .namedqueries import QUERY_NAMES, QueryName
from .result import Result
from .brokers.triplestore import TriplestoreBroker


class MyResult(udal.Result[str]):
    """A result containing a string."""

    def data(self, type: type[str] | None = None):
        if type is None or type is str:
            return self._data
        else:
            raise Exception(f"cannot return the data as {type}")


class MyUDAL(udal.UDAL):

    def __init__(self):
        pass

    @property
    def query_names(self):
        return ["urn:example.com:example"]

    @property
    def queries(self):
        return {
            "urn:example.com:example": udal.NamedQueryInfo(
                "urn:example.com:example", {}
            )
        }

    def execute(self, name, params={}):
        match name:
            case "urn:example.com:example":
                return MyResult(self.queries[name], "example data")
            case _:
                raise Exception(f'query "{name}" not supported')


class UDAL(udal.UDAL):
    """Uniform Data Access Layer"""

    def __init__(self, config: udal.Config = udal.Config()):
        self._config = config
        self._broker = TriplestoreBroker()

    def execute(self, name: str, params: dict | None = None) -> Result:
        """Find and execute the query with the given name."""
        if name in QUERY_NAMES:
            return self._broker.execute(name, params)
        else:
            raise Exception(f"query {name} not supported")

    @property
    def queries(self) -> dict[str, udal.NamedQueryInfo]:
        return self._broker.queries
