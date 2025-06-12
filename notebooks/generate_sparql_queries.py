from conneg_functions import generate_sparql

import pandas as pd
import numpy as np
from sema.query import GraphSource as KGSource, QueryResult
import os
from pandas import DataFrame

# some paramter setup for the triplestore
# SPARQL EndPoint to use - wrapped as Knowledge-Graph 'source'
GDB_BASE: str = os.getenv("GDB_BASE", "http://emobon-kb.web.vliz.be:7200/")
# print(f"{os.getenv('GDB_BASE')=}")
# print(f"{GDB_BASE=}")
GDB_REPO: str = os.getenv("GDB_REPO", "kgap")
GDB_ENDPOINT: str = f"{GDB_BASE}repositories/{GDB_REPO}"
print(f"{GDB_ENDPOINT=}")
GDB: KGSource = KGSource.build(GDB_ENDPOINT)

marine_regions_names_query = """
PREFIX emobon-sampling: <https://data.emobon.embrc.eu/ns/sampling#>
PREFIX emobon: <https://data.emobon.embrc.eu/ns/core#>
SELECT DISTINCT
  ?marine_region_name
WHERE {
    ?observatory a emobon:Observatory .
    ?observatory emobon:marineRegionName ?marine_region_name .
    }
"""
# Execute the query to get marine regions names
result_marine_regions: QueryResult = GDB.query(sparql=marine_regions_names_query)
df_marine_regions: DataFrame = result_marine_regions.to_dataframe()

# same for the marine regions ids
marine_regions_ids_query = """
PREFIX emobon-sampling: <https://data.emobon.embrc.eu/ns/sampling#>
PREFIX emobon: <https://data.emobon.embrc.eu/ns/core#>
SELECT DISTINCT
  ?marine_region_id
WHERE {
    ?observatory a emobon:Observatory .
    ?observatory emobon:marineRegion ?marine_region_id .
    }
"""
# Execute the query to get marine regions ids
result_marine_regions_ids: QueryResult = GDB.query(sparql=marine_regions_ids_query)
df_marine_regions_ids: DataFrame = result_marine_regions_ids.to_dataframe()

# get all the species names that are present in emobon
species_names_query = """
prefix prod: <https://data.emobon.embrc.eu/ns/product#> 
prefix dct: <http://purl.org/dc/terms/>
select distinct ?sname where { 
	?annotation a prod:TaxonomicAnnotation .
    ?annotation dct:identifier ?id .
    ?id dct:scientificName ?sname .
}
"""
# Execute the query to get species names
result_species_names: QueryResult = GDB.query(sparql=species_names_query)
df_species_names: DataFrame = result_species_names.to_dataframe()

# same for the taxonomic ranks
taxonomic_ranks_query = """
prefix prod: <https://data.emobon.embrc.eu/ns/product#>
prefix dct: <http://purl.org/dc/terms/>
select distinct ?rank where { 
  ?annotation a prod:TaxonomicAnnotation .
    ?annotation dct:identifier ?id .
    ?id dct:taxonRank ?rank .
}
"""
# Execute the query to get taxonomic ranks
result_taxonomic_ranks: QueryResult = GDB.query(sparql=taxonomic_ranks_query)
df_taxonomic_ranks: DataFrame = result_taxonomic_ranks.to_dataframe()

# same for the taxon ids
taxonomic_ids_query = """
prefix prod: <https://data.emobon.embrc.eu/ns/product#>
prefix dct: <http://purl.org/dc/terms/>
select distinct ?id where { 
  ?annotation a prod:TaxonomicAnnotation .
    ?annotation dct:identifier ?id .
}
"""
# Execute the query to get taxonomic ids
result_taxonomic_ids: QueryResult = GDB.query(sparql=taxonomic_ids_query)
df_taxonomic_ids: DataFrame = result_taxonomic_ids.to_dataframe()

properties_query = """
PREFIX owl: <http://www.w3.org/2002/07/owl#> 
PREFIX sosa: <http://www.w3.org/ns/sosa/>
SELECT distinct ?propertyLabel
WHERE {
    ?observations a sosa:Observation .
    ?observations sosa:observedProperty ?property .
    ?property rdfs:label ?propertyLabel .
}
"""
# Execute the query to get properties
result_properties: QueryResult = GDB.query(sparql=properties_query)
df_properties: DataFrame = result_properties.to_dataframe()

# observatories
observatories_query = """
PREFIX emobon-sampling: <https://data.emobon.embrc.eu/ns/sampling#>
PREFIX emobon: <https://data.emobon.embrc.eu/ns/core#>
SELECT DISTINCT
  ?observatory_id
WHERE {
    ?observatory a emobon:Observatory .
    ?observatory emobon:observatoryId ?observatory_id .
    }
"""
# Execute the query to get observatories
result_observatories: QueryResult = GDB.query(sparql=observatories_query)
df_observatories: DataFrame = result_observatories.to_dataframe()

# variable for the datetime range
datetime_minimum = "2022-01-01"
datetime_maximum = "2025-12-31"


# use random to generate a random datetime within the range
def generate_random_datetime_range(min_date: str, max_date: str) -> dict:
    min_timestamp = pd.to_datetime(min_date).timestamp()
    max_timestamp = pd.to_datetime(max_date).timestamp()
    begin_timestamp = np.random.uniform(min_timestamp, max_timestamp)
    end_timestamp = np.random.uniform(begin_timestamp, max_timestamp)
    datetime_begin = pd.to_datetime(begin_timestamp, unit="s").strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    datetime_end = pd.to_datetime(end_timestamp, unit="s").strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return {"datetime_begin": datetime_begin, "datetime_end": datetime_end}


# a function to generate a dict for a property filter
def generate_property_filter(property_name: str, value: str, operator: str) -> dict:
    return {"property": property_name, "value": value, "operator": operator}


# a function to generate a dict for a depth filter
def generate_depth_filter(value: str, operator: str) -> dict:
    return {"value": value, "operator": operator}


# a function that will use the random library to generate set of parameters for the SPARQL query generation
import random


def generate_random_parameters():
    # select a random number of parameters between 1 and 7
    num_parameters = random.randint(1, 7)
    parameters = {}
    # for each parameter, select a random value from the available options
    # make sure to not select the same parameter twice
    # if properties_filter is selected, select a random property from the properties dataframe
    # if species_name is selected, select a random species name from the species_names dataframe
    # if marine_region is selected, select a random marine region from the marine_regions dataframe
    # if marine_region_id is selected, select a random marine region id from the marine_regions_ids dataframe
    # if observatories is selected, select a random observatory from the observatories dataframe between 1 and 3 and make a list from it
    # if taxon_rank is selected, select a random taxonomic rank from the taxonomic_ranks dataframe
    # if depth is selected, select a random depth value between 0 and 1000 and a random operator from the list ['<', '<=', '>', '>=']
    # if datetime_range is selected, select a random datetime between the datetime_minimum and datetime_maximum
    # if abundance_threshold is selected, select a random value between 0 and 100
    # if sampling_type is selected, select a random value from the list ['metagenomic', 'molecular', 'biological', 'chemical', 'physical']
    selected_parameters = random.sample(
        [
            "datetime_range",
            "marine_region",
            "marine_region_id",
            "taxon_rank",
            "species_name",
            "abundance_threshold",
            "sampling_type",
            "observatories",
            "depth",
            "property_filters",
        ],
        num_parameters,
    )

    for parameter in selected_parameters:
        if parameter == "datetime_range":
            datetime_dict = generate_random_datetime_range(
                datetime_minimum, datetime_maximum
            )
            parameters["datetime_begin"] = datetime_dict["datetime_begin"]
            parameters["datetime_end"] = datetime_dict["datetime_end"]
        elif parameter == "marine_region":
            parameters[parameter] = random.choice(
                df_marine_regions["marine_region_name"].tolist()
            )
        elif parameter == "marine_region_id":
            parameters[parameter] = random.choice(
                df_marine_regions_ids["marine_region_id"].tolist()
            )
        elif parameter == "taxon_rank":
            parameters[parameter] = random.choice(df_taxonomic_ranks["rank"].tolist())
        elif parameter == "species_name":
            parameters[parameter] = random.choice(df_species_names["sname"].tolist())
        elif parameter == "abundance_threshold":
            parameters[parameter] = str(random.uniform(0, 100))
        elif parameter == "sampling_type":
            parameters[parameter] = random.choice(
                ["metagenomic", "molecular", "biological", "chemical", "physical"]
            )
        elif parameter == "observatories":
            parameters[parameter] = random.sample(
                df_observatories["observatory_id"].tolist(), random.randint(1, 3)
            )
        elif parameter == "depth":
            parameters[parameter] = generate_depth_filter(
                str(random.uniform(0, 1000)), random.choice(["<", "<=", ">", ">="])
            )
        elif parameter == "property_filters":
            num_filters = random.randint(1, 3)
            available_properties = df_properties["propertyLabel"].tolist()
            chosen_properties = random.sample(
                available_properties, min(num_filters, len(available_properties))
            )
            filters = []
            for property_name in chosen_properties:
                value = str(random.uniform(0, 100))  # Assuming the value is a float
                operator = random.choice(["<", "<=", ">", ">="])
                filters.append(generate_property_filter(property_name, value, operator))
            parameters[parameter] = filters
    return parameters


# make a new folded called generated_sparql_queries and save the query to a file
import os

if not os.path.exists("generated_sparql_queries"):
    os.makedirs("generated_sparql_queries")

# run the generate random parameters function 1000 times and save the queries to files
for i in range(1000):
    parameters = generate_random_parameters()
    sparql_query = generate_sparql("metagenomic_sampling_subset.sparql", **parameters)
    with open(f"generated_sparql_queries/query_{i}.sparql", "w") as f:
        f.write(sparql_query)
    print(f"Generated query {i} with parameters: {parameters}")
