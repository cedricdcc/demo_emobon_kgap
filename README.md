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

in demo.py change DEMO_QUESTION to get a different query.
