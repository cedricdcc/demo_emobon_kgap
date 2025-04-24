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

[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/430f9644-290a-451c-97a4-ac6b9b91af85)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/046a10d6-e461-4811-acf2-309697ff34db)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/4c2dac41-99d7-433c-a09d-a13530c4d07f)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/2d347e53-b18f-4ba7-8a2c-64c7d7e3e5e9)

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

[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/1b6199bb-29bf-4f60-9205-f072a5a5e321)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/ba5d8b5e-7973-4916-9fea-74120726cec6)
