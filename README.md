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
