import json

def get_id_from_name(p4info, name, entity_type):
    if entity_type == "table":
        for table in p4info.tables:
            if table.preamble.name == name:
                return table.preamble.id
    elif entity_type == "action":
        for action in p4info.actions:
            if action.preamble.name == name:
                return action.preamble.id
    elif entity_type == "match":
        for table in p4info.tables:
            for match_field in table.match_fields:
                if match_field.name == name:
                    return match_field.id
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")

    raise ValueError(f"Could not find {entity_type} named {name!r}")

def get_match_field_id(p4info, table_name, field_name):
    for table in p4info.tables:
        if table.preamble.name == table_name:
            for match_field in table.match_fields:
                if match_field.name == field_name:
                    return match_field.id
            raise ValueError(
                f"Table {table_name!r} has no match field named {field_name!r}"
            )
    raise ValueError(f"Could not find table named {table_name!r}")


