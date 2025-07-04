import jsonschema
from jsonschema import validate

# Define the JSON schema
schema = {
    "type": "object",
    "properties": {
        "marine_region_id": {"type": "string"},
        "marine_region": {"type": "string"},
        "observatories": {"type": "array", "items": {"type": "string"}},
        "depth": {
            "type": "object",
            "properties": {"value": {"type": "number"}, "operator": {"type": "string"}},
            "required": ["value", "operator"],
        },
        "contact": {"type": "array", "items": {"type": "string"}},
        "datetime_begin": {"type": "string", "format": "date-time"},
        "datetime_end": {"type": "string", "format": "date-time"},
        "sampling_method": {"type": "string"},
        "species_name": {"type": "string"},
        "taxon_rank": {"type": "string"},
        "taxon_id": {"type": "string"},
        "sampling_id": {"type": "string"},
        "sampling_type": {"type": "string"},
        "abundance_threshold": {"type": "number"},
        "property_filters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "property": {"type": "string"},
                    "value": {},
                    "operator": {"type": "string"},
                    "value_type": {"type": "string"},
                },
                "required": ["property", "value", "operator", "value_type"],
            },
        },
    },
    "required": [
        "marine_region_id",
        "marine_region",
        "datetime_begin",
        "datetime_end",
        "sampling_method",
        "species_name",
        "taxon_rank",
        "taxon_id",
        "sampling_id",
        "sampling_type",
    ],
}


# Function to validate JSON
def validate_json(data):
    try:
        validate(instance=data, schema=schema)
        return True, "JSON is valid."
    except jsonschema.exceptions.ValidationError as err:
        return False, f"JSON validation error: {err.message}"


# Example usage
if __name__ == "__main__":
    sample_json = {
        "marine_region_id": "123",
        "marine_region": "Atlantic",
        "datetime_begin": "2025-01-01T00:00:00Z",
        "datetime_end": "2025-12-31T23:59:59Z",
        "sampling_method": "net",
        "species_name": "Homo sapiens",
        "taxon_rank": "species",
        "taxon_id": "9606",
        "sampling_id": "S123",
        "sampling_type": "biological",
    }
    is_valid, message = validate_json(sample_json)
    print(message)
