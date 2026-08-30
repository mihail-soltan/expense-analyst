sql_function = {
    "type": "function",
    "name": "execute_query",
    "description": "Returns the query results from the expenses table",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "A valid SQLITE query for the provided schema"}
        }
    }
}