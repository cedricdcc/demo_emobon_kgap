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
GDB_BASE: str = os.getenv("GDB_BASE", "http://localhost:7200/")

# production will be http://emobon-kb.web.vliz.be:7200/
# deveopment will be http://localhost:7200/

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


def execute_to_dict(name: str, **vars) -> dict:
    """Builds the sparql and executes, returning the result as a dict."""
    sparql = generate_sparql(name, **vars)
    print(f"{sparql=}")
    result: QueryResult = GDB.query(sparql=sparql)
    return result.to_dict()


class TriplestoreBroker(Broker):
    """A broker that uses a triplestore to execute queries."""

    _query_names: list[QueryName] = triplestoreBrokerQueryNames
    """List of the supported query names."""

    _queries: dict[QueryName, NamedQueryInfo] = triplestoreBrokerQueries
    """List of the supported queries."""

    def __init__(self):
        pass

    @property
    def queryNames(self) -> list[str]:
        return list(TriplestoreBroker._query_names)

    @property
    def queries(self):
        return {k: v for k, v in TriplestoreBroker._queries.items()}

    # functions here to execute the queries
    def _execute_query_observations(self, params: dict) -> dict:
        return {}

    def _execute_query_observatory_overview(self, params: dict) -> dict:
        _observation_results: dict = execute_to_dict("observatory_overview.sparql")
        return _observation_results

    def _execute_query_observatory_overview_totals(self, params: dict) -> dict:
        _observation_overview_results: dict = execute_to_dict(
            "observatory_overview_totals.sparql"
        )
        return _observation_overview_results

    def _execute_query_measured_values(self, params: dict) -> dict:
        print(f"{params=}")
        if isinstance(params.get("observatory_id"), list):
            params["observatory_id"] = ", ".join(
                f'"{obs}"' for obs in params["observatory_id"]
            )
        _measured_values_results: dict = execute_to_dict(
            "measured_values.sparql", **params
        )

        # make new key in dict called context which is a dict.
        # put observatory_id , sampling_event, sampling_type
        # date, position_depth, position_location , instrument_type
        context = {
            "observatory_id": _measured_values_results.get("observatory_id"),
            "sampling_event": _measured_values_results.get("sampling_event"),
            "sampling_type": _measured_values_results.get("type"),
            "date": _measured_values_results.get("date"),
            "position_depth": _measured_values_results.get("depth"),
            # "position_location": _measured_values_results.get("position_location"),
            "instrument_type": _measured_values_results.get("instrument_type"),
        }
        _measured_values_results["context"] = context
        # remove the keys from the main dict
        _measured_values_results.pop("observatory_id", None)
        _measured_values_results.pop("sampling_event", None)
        _measured_values_results.pop("type", None)
        _measured_values_results.pop("date", None)
        _measured_values_results.pop("depth", None)
        # _measured_values_results.pop("position_location", None)
        _measured_values_results.pop("instrument_type", None)

        return _measured_values_results

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
        queryFunction = getattr(
            self, f"_execute_query_{name.split(':')[-1].replace('-', '_')}"
        )
        queryResult = queryFunction(queryParams)
        return Result(query, queryResult)
