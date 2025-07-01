# demo_graphdb_ollama
a small demo that uses graphdb and ollama for natural language querying of RDF data

# Installation

run the following commands

```bash	
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
docker-compose up 
python demo.py
```

In demo.py change DEMO_QUESTION to get a different query.
The quality of the query depends on the quality of the data in the RDF graph and the quality of the OLLAMA model.

### Extra query for getting MR info in sembench
    
    ```yaml
     - subjects:
      SPARQL: >
        SELECT DISTINCT ?mr 
        WHERE  {
          ?observatory a <https://data.emobon.embrc.eu/ns/core#Observatory> .
            ?observatory <https://data.emobon.embrc.eu/ns/core#marineRegion> ?mr .
        }
    paths:
      - "*"
    ```

This is not used since the base URi is incorrect in graphDB

## docker compose

```code
docker compose --profile cpu pull
docker compose create && docker compose --profile cpu up
```

## rocrates

[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/4e90af9a-1aed-48e5-b6d1-9a5582bf3298)
