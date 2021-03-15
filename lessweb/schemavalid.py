import jsonschema


def make_resolver(openapi):
    return jsonschema.RefResolver.from_schema(openapi)


def validate(instance, *, schema, resolver) -> str:
    try:
        jsonschema.validate(instance=instance, schema=schema, resolver=resolver, format_checker=jsonschema.draft7_format_checker)
        return ''
    except jsonschema.ValidationError as e:
        return str(e)


def parse_value(string, schema_type):
    if schema_type == 'integer':
        return int(string)
    elif schema_type == 'number':
        return float(string)
    elif schema_type == 'boolean':
        return bool(string)
    else:
        return string


def check_param_str(param_name, *, param_value, schema, resolver):
    """
    检查通过则return，不通过则返回TypeError
    """
    type_str = schema.get('type', 'string')
    param_value = parse_value(param_value, type_str)
    error_message = validate(param_value, schema=schema, resolver=resolver)
    if error_message:
        raise TypeError(f'{param_name} {error_message}')
    return param_value
