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

## docker compose

```code
docker compose --profile cpu pull
docker compose create && docker compose --profile cpu up
```

## rocrates

[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/1b6199bb-29bf-4f60-9205-f072a5a5e321)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/ba5d8b5e-7973-4916-9fea-74120726cec6)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/b090a944-8403-4897-a86f-68faa46b6b6b)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/192947f3-cfea-40a1-8200-f2ff1e7d2ef9)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/d3fd90c1-1f32-473c-bc10-82365100fe29)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/af4cf395-c59f-4e9a-b625-1aad98ce7315)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/63b799f6-28c4-4f29-940d-7899a7b98a57)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/b14dbdb5-1b88-4e79-ae51-a64ae2005a57)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/75ffe19d-83f6-4f42-8e3d-9a593ebb25cc)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/5a235e1c-ef27-4936-af3a-3b0e777d74db)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/30ec7b1a-603c-4aae-84d7-8b3556d267e1)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/bb3db95b-65ee-4e41-b0dd-c51c99bc9df4)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/50d9cedf-6df7-4c8d-b09b-e478274f4c4b)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/bd362263-9768-48fb-b4e5-28b2495fda7e)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/364b0c91-b7c6-4a7c-8700-9e05cf3e5f10)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/b306d099-1e82-44a2-a56e-5cf157ca02ac)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/db8ede13-b665-4a07-bad1-9db4fb7d7c98)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/0bb598b7-c226-4d8d-bd38-6aa98fe50589)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/6ba2933e-1526-4850-8eed-968636a5c2f2)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/7f348f1c-b01a-4d40-858e-9d39927631c4)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/972bc440-0a52-4179-8287-b1e858ed9332)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/1f7d9d88-533c-4493-9496-38d4abacbc36)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/8c56a59f-eb95-4096-a696-fb3e084eb1a2)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/e281c1fd-f22f-4059-9a44-432a6c9a95e7)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/7178a386-e570-48d8-bc0f-6cd88d248ec6)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/b05c6fe1-29bc-4546-8555-6c3c7e1d9d4c)


[![ROHub Crate](https://img.shields.io/badge/ROHub-Crate-blue)](https://rohub.org/4735313e-25ba-404e-9984-1f6c3f44a3f3)
