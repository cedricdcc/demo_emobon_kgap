import udal.specification as udal


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
