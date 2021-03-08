# Copyright 2016 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Contains all the units for the spec.

This file loads swagger and JSON schema files and parses out the useful bits
and returns them as Units for use in Batesian.

For the actual conversion of data -> RST (including templates), see the sections
file instead.
"""
from batesian.units import Units
from collections import OrderedDict
import logging
import json
import os
import os.path
import re
import subprocess
import sys
import yaml
from functools import reduce
from six.moves.urllib.parse import urlencode, quote

matrix_doc_dir=reduce(lambda acc,_: os.path.dirname(acc),
                      range(1, 5), os.path.abspath(__file__))

HTTP_APIS = {
    os.path.join(matrix_doc_dir, "api/application-service"): "as",
    os.path.join(matrix_doc_dir, "api/client-server"): "cs",
    os.path.join(matrix_doc_dir, "api/identity"): "is",
    os.path.join(matrix_doc_dir, "api/push-gateway"): "push",
    os.path.join(matrix_doc_dir, "api/server-server"): "ss",
    os.path.join(matrix_doc_dir, "api/widgets"): "widgets",
}
SWAGGER_DEFINITIONS = {
    os.path.join(matrix_doc_dir, "api/application-service/definitions"): "as",
    os.path.join(matrix_doc_dir, "api/client-server/definitions"): "cs",
    os.path.join(matrix_doc_dir, "api/identity/definitions"): "is",
    os.path.join(matrix_doc_dir, "api/push-gateway/definitions"): "push",
    os.path.join(matrix_doc_dir, "api/server-server/definitions"): "ss",
    os.path.join(matrix_doc_dir, "api/widgets/definitions"): "widgets",
}
EVENT_EXAMPLES = os.path.join(matrix_doc_dir, "event-schemas/examples")
EVENT_SCHEMA = os.path.join(matrix_doc_dir, "event-schemas/schema")
CORE_EVENT_SCHEMA = os.path.join(matrix_doc_dir, "event-schemas/schema/core-event-schema")
CHANGELOG_DIR = os.path.join(matrix_doc_dir, "changelogs")
TARGETS = os.path.join(matrix_doc_dir, "specification/targets.yaml")

ROOM_EVENT = "core-event-schema/room_event.yaml"
STATE_EVENT = "core-event-schema/state_event.yaml"

SAS_EMOJI_JSON = os.path.join(matrix_doc_dir, "data-definitions/sas-emoji.json")

logger = logging.getLogger(__name__)

# a yaml Loader which loads mappings into OrderedDicts instead of regular
# dicts, so that we preserve the ordering of properties from the api files.
#
# with thanks to http://stackoverflow.com/a/21912744/637864
class OrderedLoader(yaml.Loader):
    pass
def construct_mapping(loader, node):
    loader.flatten_mapping(node)
    pairs = loader.construct_pairs(node)
    return OrderedDict(pairs)
OrderedLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_mapping)


class TypeTable(object):
    """Describes a table documenting an object type

    Attributes:
        title(str|None): Title of the table - normally the object type
        desc(str|None): description of the object
        rows(list[TypeTableRow]): the rows in the table
    """
    def __init__(self, title=None, desc=None, rows=[]):
        self.title=title
        self.desc=desc
        self._rows = []
        for row in rows:
            self.add_row(row)

    def add_row(self, row):
        if not isinstance(row, TypeTableRow):
            raise ValueError("Can only add TypeTableRows to TypeTable")

        self._rows.append(row)

    def __getattr__(self, item):
        if item == 'rows':
            return list(self._rows)
        return super(TypeTable, self).__getattr__(item)

    def __repr__(self):
        return "TypeTable[%s, rows=%s]" % (self.title, self._rows)


class TypeTableRow(object):
    """Describes an object field defined in the json schema
    """
    def __init__(self, key, title, desc, required=False):
        self.key = key
        self.title = title
        self.desc = desc
        self.required = required

    def __repr__(self):
        return "TypeTableRow[%s: %s]" % (self.key, self.desc)


def resolve_references(path, schema):
    if isinstance(schema, dict):
        # do $ref first
        if '$ref' in schema:
            value = schema['$ref']
            path = os.path.join(os.path.dirname(path), value)
            with open(path, encoding="utf-8") as f:
                ref = yaml.load(f, OrderedLoader)
            result = resolve_references(path, ref)
            del schema['$ref']
        else:
            result = OrderedDict()

        for key, value in schema.items():
            result[key] = resolve_references(path, value)
        return result
    elif isinstance(schema, list):
        return [resolve_references(path, value) for value in schema]
    else:
        return schema


def inherit_parents(obj):
    """
    Recurse through the 'allOf' declarations in the object
    """
    logger.debug("inherit_parents %r" % obj)

    parents = obj.get("allOf", [])
    if not parents:
        return obj

    result = {}

    # settings defined in the child take priority over the parents, so we
    # iterate through the parents first, and then overwrite with the settings
    # from the child.
    for p in list(map(inherit_parents, parents)) + [obj]:
        # child blats out type, title and description
        for key in ('type', 'title', 'description'):
            if p.get(key):
                result[key] = p[key]

        # other fields get merged
        for key in ('required', ):
            if p.get(key):
                result.setdefault(key, []).extend(p[key])

        for key in ('properties', 'additionalProperties', 'patternProperties'):
            if p.get(key):
                result.setdefault(key, OrderedDict()).update(p[key])

    return result


def get_json_schema_object_fields(obj, enforce_title=False):
    """Parse a JSON schema object definition

    Args:
        obj(dict): definition from the JSON schema file. $refs should already
            have been resolved.
        enforce_title (bool): if True, and the definition has no "title",
            the 'title' result will be set to 'NO_TITLE' (otherwise it will be
            set to None)

    Returns:
        dict: with the following fields:
          - title (str): title (normally the type name) for the object
          - tables (list[TypeTable]): list of the tables for the type
                definition
    """
    # Algorithm:
    # f.e. property => add field info (if field is object then recurse)
    if obj.get("type") != "object":
        raise Exception(
            "get_json_schema_object_fields: Object %s isn't an object." % obj
        )

    obj_title = obj.get("title")

    logger.debug("Processing object with title '%s'", obj_title)

    additionalProps = obj.get("additionalProperties")

    # When 'additionalProps: true` is defined, it should be treated as a freeform object
    if additionalProps == True:
        additionalProps = dict(type="object", title="value")

    props = obj.get("properties")
    if additionalProps and not props:
        # not "really" an object, just a KV store
        logger.debug("%s is a pseudo-object", obj_title)

        key_type = additionalProps.get("x-pattern", "string")
        res = process_data_type(additionalProps)
        tables = res["tables"]
        val_title = res["title"]
        gen_title = "{%s: %s}" % (key_type, val_title)
        if res.get("enum_desc") and val_title != "enum":
            # A map to enum needs another table with enum description
            tables.append(TypeTable(
                title=val_title,
                rows=[TypeTableRow(key="(mapped value)", title="enum", desc=res["desc"])]
            ))
        return {
            "title": obj_title if obj_title else gen_title,
            "tables": tables,
        }

    if not props:
        props = obj.get("patternProperties")
        if props:
            # try to replace horrible regex key names with pretty x-pattern ones
            for key_name in props.keys():
                pretty_key = props[key_name].get("x-pattern")
                if pretty_key:
                    props[pretty_key] = props[key_name]
                    del props[key_name]



    # Sometimes you just want to specify that a thing is an object without
    # doing all the keys.
    if not props:
        return {
            "title": obj_title if obj_title else 'object',
            "tables": [],
        }

    if enforce_title and not obj_title:
        # Force a default titile of "NO_TITLE" to make it obvious in the
        # specification output which parts of the schema are missing a title
        obj_title = 'NO_TITLE'

    required_keys = set(obj.get("required", []))

    first_table_rows = []
    tables = []

    for key_name in props:
        try:
            logger.debug("Processing property %s.%s", obj_title, key_name)
            required = key_name in required_keys
            res = process_data_type(props[key_name], required)

            first_table_rows.append(TypeTableRow(
                key=key_name,
                title=res["title"],
                required=required,
                desc=res["desc"],
            ))
            tables.extend(res["tables"])
            logger.debug("Done property %s" % key_name)

        except Exception as e:
            e2 = Exception("Error reading property %s.%s: %s" %
                           (obj_title, key_name, str(e)))
            # throw the new exception with the old stack trace, so that
            # we don't lose information about where the error occurred.
            raise e2.with_traceback(sys.exc_info()[2])

    tables.insert(0, TypeTable(title=obj_title, rows=first_table_rows))

    for table in tables:
        assert isinstance(table, TypeTable)

    return {
        "title": obj_title,
        "tables": tables,
    }


# process a data type definition. returns a dictionary with the keys:
# title:     stringified type name
# desc:     description
# enum_desc: description of permissible enum fields
# is_object: true if the data type is an object
# tables:   list of additional table definitions
def process_data_type(prop, required=False, enforce_title=True):
    prop = inherit_parents(prop)

    prop_type = prop.get('oneOf', prop.get('type', []))
    assert prop_type

    tables = []
    enum_desc = None
    is_object = False

    if prop_type == "object":
        res = get_json_schema_object_fields(
            prop,
            enforce_title=enforce_title,
        )
        prop_title = res["title"]
        tables = res["tables"]
        is_object = True

    elif prop_type == "array":
        items = prop["items"]
        # Items can be a list of schemas or a schema itself
        # http://json-schema.org/latest/json-schema-validation.html#rfc.section.6.4
        if isinstance(items, list):
            nested_titles = []
            for i in items:
                nested = process_data_type(i)
                tables.extend(nested['tables'])
                nested_titles.append(nested['title'])
            prop_title = "[%s]" % (", ".join(nested_titles), )
        else:
            nested = process_data_type(prop["items"])
            prop_title = "[%s]" % nested["title"]
            tables = nested["tables"]
            enum_desc = nested["enum_desc"]

    elif isinstance(prop_type, list):
        prop_title = []
        for t in prop_type:
            if isinstance(t, dict):
                nested = process_data_type(t)
                tables.extend(nested['tables'])
                prop_title.append(nested['title'])
                # Assuming there's at most one enum among type options
                enum_desc = nested['enum_desc']
                if enum_desc:
                    enum_desc = "%s if the type is enum" % enum_desc
            else:
                prop_title.append(t)
    else:
        prop_title = prop_type

    if prop.get("enum"):
        prop_title = prop.get("title", "enum")
        if len(prop["enum"]) > 1:
            enum_desc = (
                "One of: %s" % json.dumps(prop["enum"])
            )
        else:
            enum_desc = (
                "Must be '%s'." % prop["enum"][0]
            )

    if isinstance(prop_title, list):
        prop_title = " or ".join(prop_title)

    rq = "**Required.**" if required else None
    desc = " ".join(x for x in [rq, prop.get("description"), enum_desc] if x)

    for table in tables:
        assert isinstance(table, TypeTable)

    return {
        "title": prop_title,
        "desc": desc,
        "enum_desc": enum_desc,
        "is_object": is_object,
        "tables": tables,
    }

def deduplicate_tables(tables):
    # the result may contain duplicates, if objects are referred to more than
    # once. Filter them out.
    #
    # Go through the tables backwards so that we end up with a breadth-first
    # rather than depth-first ordering.

    titles = set()
    filtered = []
    for table in reversed(tables):
        if table.title in titles:
            continue

        titles.add(table.title)
        filtered.append(table)
    filtered.reverse()

    return filtered

def get_tables_for_schema(schema):
    pv = process_data_type(schema, enforce_title=False)
    return deduplicate_tables(pv["tables"])

def get_tables_for_response(schema):
    pv = process_data_type(schema, enforce_title=False)
    tables = deduplicate_tables(pv["tables"])

    # make up the first table, with just the 'body' row in, unless the response
    # is an object, in which case there's little point in having one.
    if not pv["is_object"]:
        first_table_row = TypeTableRow(
            key="<body>", title=pv["title"], desc=pv["desc"],
        )
        tables.insert(0, TypeTable(None, rows=[first_table_row]))

    logger.debug("response: %r" % tables)

    return tables

def get_example_for_schema(schema):
    """Returns a python object representing a suitable example for this object"""
    schema = inherit_parents(schema)

    if 'example' in schema:
        example = schema['example']
        return example

    proptype = schema['type']

    if proptype == 'object':
        if 'properties' not in schema:
            raise Exception('"object" property has neither properties nor example')
        res = OrderedDict()
        for prop_name, prop in schema['properties'].items():
            logger.debug("Parsing property %r" % prop_name)
            prop_example = get_example_for_schema(prop)
            res[prop_name] = prop_example
        return res

    if proptype == 'array':
        if 'items' not in schema:
            raise Exception('"array" property has neither items nor example')
        items = schema['items']
        if isinstance(items, list):
            return [get_example_for_schema(i) for i in items]
        return [get_example_for_schema(items)]

    if proptype == 'integer':
        return 0

    if proptype == 'string':
        return proptype

    raise Exception("Don't know to make an example %s" % proptype)

def get_example_for_param(param):
    """Returns a stringified example for a parameter"""
    if 'x-example' in param:
        return param['x-example']
    schema = param.get('schema')
    if not schema:
        return None

    exampleobj = None
    if 'example' in schema:
        exampleobj = schema['example']

    if exampleobj is None:
        exampleobj = get_example_for_schema(schema)

    return json.dumps(exampleobj, indent=2)

def get_example_for_response(response):
    """Returns a stringified example for a response"""
    exampleobj = None
    if 'examples' in response:
        exampleobj = response["examples"].get("application/json")

    if exampleobj is None:
        schema = response.get('schema')
        if schema:
            if schema['type'] == 'file':
                # no example for 'file' responses
                return None
            exampleobj = get_example_for_schema(schema)

    if exampleobj is None:
        return None

    return json.dumps(exampleobj, indent=2)

class MatrixUnits(Units):
    def _load_swagger_meta(self, api, group_name):
        endpoints = []
        base_path = api.get("basePath", "")

        for path in api["paths"]:
            for method in api["paths"][path]:
                logger.info(" ------- Endpoint: %s %s ------- " % (method, path))

                try:
                    endpoint = self._handle_endpoint(
                        api["paths"][path][method], method,
                        base_path.rstrip("/") + path)

                    endpoints.append(endpoint)
                except Exception as e:
                    logger.error("Error handling endpoint %s %s: %s",
                                 method, path, e)
                    raise
        return {
            "base": api.get("basePath").rstrip("/"),
            "group": group_name,
            "endpoints": endpoints,
        }

    def _handle_endpoint(self, endpoint_swagger, method, path):
        endpoint = {
            "title": endpoint_swagger.get("summary", ""),
            "deprecated": endpoint_swagger.get("deprecated", False),
            "desc": endpoint_swagger.get("description",
                                         endpoint_swagger.get("summary", "")),
            "method": method.upper(),
            "path": path.strip(),
            "requires_auth": "security" in endpoint_swagger,
            "rate_limited": 429 in endpoint_swagger.get("responses", {}),
            "req_param_by_loc": {},
            "req_body_tables": [],
            "res_headers": None,
            "res_tables": [],
            "responses": [],
            "example": {
                "req": "",
            }
        }
        path_template = path
        example_query_params = []
        example_body = ""
        example_mime = "application/json"
        for param in endpoint_swagger.get("parameters", []):
            # even body params should have names, otherwise the active docs don't work.
            param_name = param["name"]

            try:
                param_loc = param["in"]

                if param_loc == "body":
                    self._handle_body_param(param, endpoint)
                    example_body = get_example_for_param(param)
                    continue

                if param_loc == "header":
                    if param["name"] == "Content-Type" and param["x-example"]:
                        example_mime = param["x-example"]

                # description
                desc = param.get("description", "")
                if param.get("required"):
                    desc = "**Required.** " + desc

                # assign value expected for this param
                val_type = param.get("type")  # integer/string

                if val_type == "array":
                    items = param.get("items")
                    if items:
                        if isinstance(items, list):
                            types = ", ".join(i.get("type") for i in items)
                            val_type = "[%s]" % (types,)
                        else:
                            val_type = "[%s]" % items.get("type")

                if param.get("enum"):
                    val_type = "enum"
                    desc += (
                        " One of: %s" % json.dumps(param.get("enum"))
                    )

                endpoint["req_param_by_loc"].setdefault(param_loc, []).append(
                    TypeTableRow(key=param_name, title=val_type, desc=desc),
                )

                example = get_example_for_param(param)
                if example is None:
                    continue

                if param_loc == "path":
                    path_template = path_template.replace(
                        "{%s}" % param_name, quote(example)
                    )
                elif param_loc == "query":
                    if type(example) == list:
                        for value in example:
                            example_query_params.append((param_name, value))
                    else:
                        example_query_params.append((param_name, example))

            except Exception as e:
                raise Exception("Error handling parameter %s" % param_name, e)
        # endfor[param]
        good_response = None
        endpoint_status_codes = endpoint_swagger.get("responses", {}).keys()
        # Check to see if any of the status codes are strings ("4xx") and if
        # so convert everything to a string to avoid comparing ints and strings.
        has_string_status = False
        for code in endpoint_status_codes:
            if isinstance(code, str):
                has_string_status = True
                break
        if has_string_status:
            endpoint_status_codes = [str(i) for i in endpoint_status_codes]
        for code in sorted(endpoint_status_codes):
            # Convert numeric responses to ints, assuming they got converted
            # above.
            if isinstance(code, str) and code.isdigit():
                code = int(code)
            res = endpoint_swagger["responses"][code]
            if not good_response and code == 200:
                good_response = res
            description = res.get("description", "")
            example = get_example_for_response(res)
            endpoint["responses"].append({
                "code": code,
                "description": description,
                "example": example,
            })

        # add response params if this API has any.
        if good_response:
            if "schema" in good_response:
                endpoint["res_tables"] = get_tables_for_response(
                    good_response["schema"]
                )
            if "headers" in good_response:
                headers = TypeTable()
                for (header_name, header) in good_response["headers"].items():
                    headers.add_row(
                        TypeTableRow(key=header_name, title=header["type"],
                                     desc=header["description"]),
                    )
                endpoint["res_headers"] = headers
        query_string = "" if len(
            example_query_params) == 0 else "?" + urlencode(
            example_query_params)
        if example_body:
            endpoint["example"][
                "req"] = "%s %s%s HTTP/1.1\nContent-Type: %s\n\n%s" % (
                method.upper(), path_template, query_string, example_mime, example_body
            )
        else:
            endpoint["example"]["req"] = "%s %s%s HTTP/1.1\n\n" % (
                method.upper(), path_template, query_string
            )
        return endpoint

    def _handle_body_param(self, param, endpoint_data):
        """Update endpoint_data object with the details of the body param
        :param string filepath       path to the yaml
        :param dict   param          the parameter data from the yaml
        :param dict   endpoint_data  dictionary of endpoint data to be updated
        """
        try:
            schema = inherit_parents(param["schema"])
            if schema["type"] != "object":
                logger.warn(
                    "Unsupported body type %s for %s %s", schema["type"],
                    endpoint_data["method"], endpoint_data["path"]
                )
                return

            req_body_tables = get_tables_for_schema(schema)

            if req_body_tables == []:
                # no fields defined for the body.
                return

            # put the top-level parameters into 'req_param_by_loc', and the others
            # into 'req_body_tables'
            body_params = endpoint_data['req_param_by_loc'].setdefault("JSON body",[])
            body_params.extend(req_body_tables[0].rows)

            body_tables = req_body_tables[1:]
            endpoint_data['req_body_tables'].extend(body_tables)

        except Exception as e:
            e2 = Exception(
                "Error decoding body of API endpoint %s %s: %s" %
                (endpoint_data["method"], endpoint_data["path"], e)
            )
            raise e2.with_traceback(sys.exc_info()[2])


    def load_swagger_apis(self):
        apis = {}
        for path, suffix in HTTP_APIS.items():
            for filename in os.listdir(path):
                if not filename.endswith(".yaml"):
                    continue
                filepath = os.path.join(path, filename)
                logger.info("Reading swagger API: %s" % filepath)
                with open(filepath, "r", encoding="utf-8") as f:
                    # strip .yaml
                    group_name = filename[:-5].replace("-", "_")
                    group_name = "%s_%s" % (group_name, suffix)
                    api = yaml.load(f, OrderedLoader)
                    api = resolve_references(filepath, api)
                    api["__meta"] = self._load_swagger_meta(
                        api, group_name
                    )
                    apis[group_name] = api
        return apis


    def load_swagger_definitions(self):
        defs = {}
        for path, prefix in SWAGGER_DEFINITIONS.items():
            self._load_swagger_definitions_in_dir(defs, path, prefix)
        return defs

    def _load_swagger_definitions_in_dir(self, defs, path, prefix, recurse=True):
        if not os.path.exists(path):
            return defs
        for filename in os.listdir(path):
            filepath = os.path.join(path, filename)
            if os.path.isdir(filepath) and recurse:
                safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", filename)
                dir_prefix = "_".join([prefix, safe_name])
                # We don't recurse because we have to stop at some point
                self._load_swagger_definitions_in_dir(
                    defs, filepath, dir_prefix, recurse=False)
            if not filename.endswith(".yaml"):
                continue
            filepath = os.path.join(path, filename)
            logger.info("Reading swagger definition: %s" % filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                # strip .yaml
                group_name = re.sub(r"[^a-zA-Z0-9_]", "_", filename[:-5])
                group_name = "%s_%s" % (prefix, group_name)
                definition = yaml.load(f, OrderedLoader)
                definition = resolve_references(filepath, definition)
                if 'type' not in definition:
                    continue
                try:
                    example = get_example_for_schema(definition)
                except:
                    example = None
                    pass  # do nothing - we don't care
                if 'title' not in definition:
                    definition['title'] = "NO_TITLE"
                definition['tables'] = get_tables_for_schema(definition)
                defs[group_name] = {
                    "definition": definition,
                    "examples": [example] if example is not None else [],
                }
        return defs

    def load_common_event_fields(self):
        """Parse the core event schema files

        Returns:
            dict: with the following properties:
                "title": Event title (from the 'title' field of the schema)
                "desc": desc
                "tables": list[TypeTable]
        """
        path = CORE_EVENT_SCHEMA
        event_types = {}

        for filename in os.listdir(path):
            if not filename.endswith(".yaml"):
                continue

            filepath = os.path.join(path, filename)

            event_type = filename[:-5]  # strip the ".yaml"
            logger.info("Reading event schema: %s" % filepath)

            with open(filepath, encoding="utf-8") as f:
                event_schema = yaml.load(f, OrderedLoader)
                event_schema = resolve_references(filepath, event_schema)

            schema_info = process_data_type(
                event_schema,
                enforce_title=True,
            )
            event_types[event_type] = schema_info
        return event_types

    def load_apis(self, substitutions):
        cs_ver = substitutions.get("%CLIENT_RELEASE_LABEL%", "unstable")
        fed_ver = substitutions.get("%SERVER_RELEASE_LABEL%", "unstable")
        is_ver = substitutions.get("%IDENTITY_RELEASE_LABEL%", "unstable")
        as_ver = substitutions.get("%APPSERVICE_RELEASE_LABEL%", "unstable")
        push_gw_ver = substitutions.get("%PUSH_GATEWAY_RELEASE_LABEL%", "unstable")
        widget_ver = substitutions.get("%WIDGET_RELEASE_LABEL%", "unstable")

        # we abuse the typetable to return this info to the templates
        return TypeTable(rows=[
            TypeTableRow(
                "`Client-Server API <client_server/"+cs_ver+".html>`_",
                cs_ver,
                "Interaction between clients and servers",
            ), TypeTableRow(
                "`Server-Server API <server_server/"+fed_ver+".html>`_",
                fed_ver,
                "Federation between servers",
            ), TypeTableRow(
                "`Application Service API <application_service/"+as_ver+".html>`_",
                as_ver,
                "Privileged server plugins",
            ), TypeTableRow(
                "`Identity Service API <identity_service/"+is_ver+".html>`_",
                is_ver,
                "Mapping of third party IDs to Matrix IDs",
            ), TypeTableRow(
                "`Push Gateway API <push_gateway/"+push_gw_ver+".html>`_",
                push_gw_ver,
                "Push notifications for Matrix events",
            ), TypeTableRow(
                "`Widgets <widgets/"+widget_ver+".html>`_",
                widget_ver,
                "Client-side embedded applications",
            ),
        ])

    def load_event_examples(self):
        path = EVENT_EXAMPLES
        examples = {}
        for filename in os.listdir(path):
            if not filename.startswith("m."):
                continue

            event_name = filename.split("$")[0]
            filepath = os.path.join(path, filename)
            logger.info("Reading event example: %s" % filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    example = resolve_references(filepath, json.load(f))
                    examples[filename] = examples.get(filename, [])
                    examples[filename].append(example)
                    if filename != event_name:
                        examples[event_name] = examples.get(event_name, [])
                        examples[event_name].append(example)
            except Exception as e:
                e2 = Exception("Error reading event example "+filepath+": "+
                               str(e))
                # throw the new exception with the old stack trace, so that
                # we don't lose information about where the error occurred.
                raise e2.with_traceback(sys.exc_info()[2])

        return examples

    def load_event_schemas(self):
        path = EVENT_SCHEMA
        schemata = {}

        for filename in os.listdir(path):
            if not filename.startswith("m."):
                continue
            filepath = os.path.join(path, filename)
            try:
                schemata[filename] = self.read_event_schema(filepath)
            except Exception as e:
                e2 = Exception("Error reading event schema "+filepath+": "+
                               str(e))
                # throw the new exception with the old stack trace, so that
                # we don't lose information about where the error occurred.
                raise e2.with_traceback(sys.exc_info()[2])

        return schemata

    def read_event_schema(self, filepath):
        logger.info("Reading %s" % filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            json_schema = yaml.load(f, OrderedLoader)

        schema = {
            # one of "Message Event" or "State Event"
            "typeof": "",
            "typeof_info": "",

            # event type, eg "m.room.member". Note *not* the type of the
            # event object (which should always be 'object').
            "type": None,
            "title": None,
            "desc": None,
            "msgtype": None,
            "type_with_msgtype": None, # for the template's sake
            "content_fields": [
                # <TypeTable>
            ]
        }

        # before we resolve the references, see if the first reference is to
        # the message event or state event schemas, and add typeof info if so.
        base_defs = {
            ROOM_EVENT: "Message Event",
            STATE_EVENT: "State Event"
        }
        if type(json_schema.get("allOf")) == list:
            firstRef = json_schema["allOf"][0]["$ref"]
            if firstRef in base_defs:
                schema["typeof"] = base_defs[firstRef]

        json_schema = resolve_references(filepath, json_schema)

        # add type
        schema["type"] = Units.prop(
            json_schema, "properties/type/enum"
        )[0]

        # add summary and desc
        schema["title"] = json_schema.get("title")
        schema["desc"] = json_schema.get("description", "")

        # walk the object for field info
        schema["content_fields"] = get_tables_for_schema(
            Units.prop(json_schema, "properties/content")
        )

        # Include UnsignedData if it is present on the object
        unsigned = Units.prop(json_schema, "properties/unsigned")
        if unsigned:
            tbls = get_tables_for_schema(unsigned)
            for tbl in tbls:
                schema["content_fields"].append(tbl)

        # grab msgtype if it is the right kind of event
        msgtype = Units.prop(
            json_schema, "properties/content/properties/msgtype/enum"
        )
        if msgtype:
            schema["msgtype"] = msgtype[0]  # enum prop
            schema["type_with_msgtype"] = schema["type"] + " (" + msgtype[0] + ")"

        # link to msgtypes for m.room.message
        if schema["type"] == "m.room.message" and not msgtype:
            schema["desc"] += (
                " For more information on ``msgtypes``, see "+
                "`m.room.message msgtypes`_."
            )

        # method types for m.key.verification.start
        if schema["type"] == "m.key.verification.start":
            methods = Units.prop(
                json_schema, "properties/content/properties/method/enum"
            )
            if methods:
                schema["type_with_msgtype"] = schema["type"] + " (" + methods[0] + ")"

        # Assign state key info if it has some
        if schema["typeof"] == "State Event":
            skey_desc = Units.prop(
                json_schema, "properties/state_key/description"
            )
            if not skey_desc:
                raise Exception("Missing description for state_key")
            schema["typeof_info"] = "``state_key``: %s" % skey_desc

        return schema

    def load_changelogs(self, substitutions):
        """Loads the changelog unit for later rendering in a section.

        Args:
            substitutions: dict of variable name to value. Provided by the gendoc script.

        Returns:
            A dict of API name ("client_server", for example) to changelog.
        """
        changelogs = {}

        # The APIs and versions we'll prepare changelogs for. We use the substitutions
        # to ensure that we pick up the right version for generated documentation. This
        # defaults to "unstable" as a version for incremental generated documentation (CI).
        prepare_versions = {
            "server_server": substitutions.get("%SERVER_RELEASE_LABEL%", "unstable"),
            "client_server": substitutions.get("%CLIENT_RELEASE_LABEL%", "unstable"),
            "identity_service": substitutions.get("%IDENTITY_RELEASE_LABEL%", "unstable"),
            "push_gateway": substitutions.get("%PUSH_GATEWAY_RELEASE_LABEL%", "unstable"),
            "widgets": substitutions.get("%WIDGETS_RELEASE_LABEL%", "unstable"),
            "application_service": substitutions.get("%APPSERVICE_RELEASE_LABEL%", "unstable"),
        }

        # Changelogs are split into two places: towncrier for the unstable changelog and
        # the RST file for historical versions. If the prepare_versions dict above has
        # a version other than "unstable" specified for an API, we'll use the historical
        # changelog and otherwise generate the towncrier log in-memory.

        for api_name, target_version in prepare_versions.items():
            logger.info("Generating changelog for %s at %s" % (api_name, target_version,))
            changelog_lines = []
            if target_version == 'unstable':
                # generate towncrier log
                changelog_lines = self._read_towncrier_changelog(api_name)
            else:
                # read in the existing RST changelog
                changelog_lines = self._read_rst_changelog(api_name)

            # Parse the changelog lines to find the header we're looking for and therefore
            # the changelog body.
            prev_line = None
            title_part = None
            changelog_body_lines = []
            for line in changelog_lines:
                if prev_line is None:
                    prev_line = line
                    continue
                if re.match("^[=]{3,}$", line.strip()):
                    # the last line was a header - use that as our new title_part
                    title_part = prev_line.strip()
                    # take off the last line from the changelog_body_lines because it's the title
                    if len(changelog_body_lines) > 0:
                        changelog_body_lines = changelog_body_lines[:len(changelog_body_lines) - 1]
                    continue
                if re.match("^[-]{3,}$", line.strip()):
                    # the last line is a subheading - drop this line because it's the underline
                    # and that causes problems with rendering. We'll keep the header text though.
                    continue
                if line.strip().startswith(".. "):
                    # skip comments
                    continue
                if title_part == target_version:
                    # if we made it this far, append the line to the changelog body. We indent it so
                    # that it renders correctly in the section. We also add newlines so that there's
                    # intentionally blank lines that make rst2html happy.
                    changelog_body_lines.append("    " + line + '\n')
                prev_line = line

            if len(changelog_body_lines) > 0:
                changelogs[api_name] = "".join(changelog_body_lines)
            else:
                raise ValueError("No changelog for %s at %s" % (api_name, target_version,))

        # return our `dict[api_name] => changelog` as the last step.
        return changelogs

    def _read_towncrier_changelog(self, api_name):
        tc_path = os.path.join(CHANGELOG_DIR, api_name)
        if os.path.isdir(tc_path):
            logger.info("Generating towncrier changelog for: %s" % api_name)
            p = subprocess.Popen(
                ['towncrier', '--version', 'unstable', '--name', api_name, '--draft'],
                cwd=tc_path,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                # Something broke - dump as much information as we can
                logger.error("Towncrier exited with code %s" % p.returncode)
                logger.error(stdout.decode('UTF-8'))
                logger.error(stderr.decode('UTF-8'))
                raw_log = ""
            else:
                raw_log = stdout.decode('UTF-8')

                # This is a bit of a hack, but it does mean that the log at least gets *something*
                # to tell us it broke
                if not raw_log.startswith("unstable"):
                    logger.error("Towncrier appears to have failed to generate a changelog")
                    logger.error(raw_log)
                    raw_log = ""
            return raw_log.splitlines()
        return []

    def _read_rst_changelog(self, api_name):
        logger.info("Reading changelog RST for %s" % api_name)
        rst_path = os.path.join(CHANGELOG_DIR, "%s.rst" % api_name)
        with open(rst_path, 'r', encoding="utf-8") as f:
            return f.readlines()

    def load_unstable_warnings(self, substitutions):
        warning = """
.. WARNING::
    You are viewing an unstable version of this specification. Unstable
    specifications may change at any time without notice. To view the
    current specification, please `click here <latest.html>`_.
"""
        warnings = {}
        for var in substitutions.keys():
            key = var[1:-1] # take off the surrounding %-signs
            if substitutions.get(var, "unstable") == "unstable":
                warnings[key] = warning
            else:
                warnings[key] = ""
        return warnings


    def load_spec_targets(self):
        with open(TARGETS, "r") as f:
            return yaml.load(f.read())


    def load_git_version(self):
        null = open(os.devnull, 'w')
        cwd = os.path.dirname(os.path.abspath(__file__))
        try:
            git_branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                stderr=null,
                cwd=cwd,
            ).strip().decode('UTF-8')
        except subprocess.CalledProcessError:
            git_branch = ""
        try:
            git_tag = subprocess.check_output(
                ['git', 'describe', '--exact-match'],
                stderr=null,
                cwd=cwd,
            ).strip().decode('UTF-8')
            git_tag = "tag=" + git_tag
        except subprocess.CalledProcessError:
            git_tag = ""
        try:
            git_commit = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stderr=null,
                cwd=cwd,
            ).strip().decode('UTF-8')
        except subprocess.CalledProcessError:
            git_commit = ""
        try:
            dirty_string = "-this_is_a_dirty_checkout"
            is_dirty = subprocess.check_output(
                ['git', 'describe', '--dirty=' + dirty_string, "--all"],
                stderr=null,
                cwd=cwd,
            ).strip().decode('UTF-8').endswith(dirty_string)
            git_dirty = "dirty" if is_dirty else ""
        except subprocess.CalledProcessError:
            git_dirty = ""

        git_version = "Unknown"
        if git_branch or git_tag or git_commit or git_dirty:
            git_version = ",".join(
                s for s in
                (git_branch, git_tag, git_commit, git_dirty,)
                if s
            ).encode("ascii").decode('ascii')
        return {
            "string": git_version,
            "revision": git_commit
        }

    def load_sas_emoji(self):
        with open(SAS_EMOJI_JSON, 'r', encoding='utf-8') as sas_json:
            emoji = json.load(sas_json)

            # Verify the emoji matches the unicode
            for c in emoji:
                e = c['emoji']
                logger.info("Checking emoji %s (%s)", e, c['description'])
                u = re.sub(r'U\+([0-9a-fA-F]+)', lambda m: chr(int(m.group(1), 16)), c['unicode'])
                if e != u:
                    raise Exception("Emoji %s should be %s not %s" % (
                        c['description'],
                        repr(e),
                        c['unicode'],
                    ))

            return emoji
