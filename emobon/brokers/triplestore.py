import pandas as pd
from sema.query import DefaultSparqlBuilder, GraphSource as KGSource, QueryResult
from typing import Any
from pathlib import Path
import os

from ..broker import Broker
from ..namedqueries import QUERY_REGISTER, NamedQueryInfo, QueryName, QUERY_NAMES
from ..result import Result

triplestoreBrokerQueryNames: list[QueryName] = list(QUERY_NAMES)
"""List of the supported query names."""

triplestoreBrokerQueries: dict[QueryName, NamedQueryInfo] = {
    k: v for k, v in QUERY_REGISTER.items() if k in triplestoreBrokerQueryNames
}

# SPARQL EndPoint to use - wrapped as Knowledge-Graph 'source'
GDB_BASE: str = os.getenv("GDB_BASE", "http://emobon-kb.web.vliz.be:7200/")
# print(f"{os.getenv('GDB_BASE')=}")
# print(f"{GDB_BASE=}")
GDB_REPO: str = os.getenv("GDB_REPO", "kgap")
GDB_ENDPOINT: str = f"{GDB_BASE}repositories/{GDB_REPO}"
# print(f"{GDB_ENDPOINT=}")
GDB: KGSource = KGSource.build(GDB_ENDPOINT)

# print(f"{GDB_ENDPOINT=}")

TEMPLATES_FOLDER = str(Path(__file__).parent / "queries")
GENERATOR = DefaultSparqlBuilder(templates_folder=TEMPLATES_FOLDER)


def generate_sparql(name: str, **vars) -> str:
    """Simply build the sparql by using the named query and applying the vars"""
    return GENERATOR.build_syntax(name, **vars)


def execute_to_df(name: str, **vars) -> pd.DataFrame:
    """Builds the sparql and executes, returning the result as a dataframe."""
    sparql = generate_sparql(name, **vars)
    result: QueryResult = GDB.query(sparql=sparql)
    return result.to_dataframe()


class TriplestoreBroker(Broker):
    """A broker that uses a triplestore to execute queries."""

    _query_names: list[QueryName] = triplestoreBrokerQueryNames
    """List of the supported query names."""

    _queries: dict[QueryName, NamedQueryInfo] = triplestoreBrokerQueries
    """List of the supported queries."""

    def __init__(self, store_url: str):
        self.store_url = store_url
        # Initialize the RDF graph

    @property
    def queryNames(self) -> list[str]:
        return list(TriplestoreBroker._query_names)

    @property
    def queries(self):
        return {k: v.as_dict() for k, v in TriplestoreBroker._queries.items()}

    # functions here to execute the queries
    def _execute_query_observatories(self, params: dict) -> dict:
        return {}

    def _execute_query_observations(self, params: dict) -> dict:
        return {}

    def _execute_query_observatory_overview(self, params: dict) -> dict:
        return {}

    def _execute_query_observatory_overview_totals(self, params: dict) -> dict:
        return {}

    def _execute_query_measured_values(self, params: dict) -> dict:
        return {}

    def _execute_query_sop_usage(self, params: dict) -> dict:
        return {}

    def _execute_query_instrument_usage(self, params: dict) -> dict:
        return {}

    def _execute_query_all_samples(self, params: dict) -> dict:
        return {}

    def execute(self, name: QueryName, params: dict | None = None) -> Result:
        if name not in TriplestoreBroker._queries:
            raise ValueError(f"Unsupported query name: {name}")
        query = TriplestoreBroker._queries[name]
        queryParams = params if params is not None else {}
        queryFunction = getattr(self, f"_execute_query_{name.split(':')[-1]}")
        queryResult = queryFunction(queryParams)
        return Result(query, queryResult)
