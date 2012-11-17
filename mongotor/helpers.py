# Copyright 2009-2010 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bson
import struct
from mongotor.errors import (DatabaseError,
    InterfaceError, TimeoutError)


def _unpack_response(response, cursor_id=None, as_class=dict, tz_aware=False):
    """Unpack a response from the database.

    Check the response for errors and unpack, returning a dictionary
    containing the response data.

    :Parameters:
      - `response`: byte string as returned from the database
      - `cursor_id` (optional): cursor_id we sent to get this response -
        used for raising an informative exception when we get cursor id not
        valid at server response
      - `as_class` (optional): class to use for resulting documents
    """
    response_flag = struct.unpack("<i", response[:4])[0]
    if response_flag & 1:
        # Shouldn't get this response if we aren't doing a getMore
        assert cursor_id is not None

        raise InterfaceError("cursor id '%s' not valid at server" %
                               cursor_id)
    elif response_flag & 2:
        error_object = bson.BSON(response[20:]).decode()
        if error_object["$err"] == "not master":
            raise DatabaseError("master has changed")
        raise DatabaseError("database error: %s" %
                               error_object["$err"])

    result = {}
    result["cursor_id"] = struct.unpack("<q", response[4:12])[0]
    result["starting_from"] = struct.unpack("<i", response[12:16])[0]
    result["number_returned"] = struct.unpack("<i", response[16:20])[0]
    result["data"] = bson.decode_all(response[20:], as_class, tz_aware)
    assert len(result["data"]) == result["number_returned"]
    return result


def _check_command_response(response, msg="%s", allowable_errors=[]):

    if not response["ok"]:
        if "wtimeout" in response and response["wtimeout"]:
            raise TimeoutError(msg % response["errmsg"])

        details = response
        # Mongos returns the error details in a 'raw' object
        # for some errors.
        if "raw" in response:
            for shard in response["raw"].itervalues():
                if not shard.get("ok"):
                    # Just grab the first error...
                    details = shard
                    break

        if not details["errmsg"] in allowable_errors:
            if details["errmsg"] == "db assertion failure":
                ex_msg = ("db assertion failure, assertion: '%s'" %
                          details.get("assertion", ""))
                if "assertionCode" in details:
                    ex_msg += (", assertionCode: %d" %
                               (details["assertionCode"],))
                raise DatabaseError(ex_msg, details.get("assertionCode"))
            raise DatabaseError(msg % details["errmsg"])


def _fields_list_to_dict(fields):
    """Takes a list of field names and returns a matching dictionary.

    ["a", "b"] becomes {"a": 1, "b": 1}

    and

    ["a.b.c", "d", "a.c"] becomes {"a.b.c": 1, "d": 1, "a.c": 1}
    """
    as_dict = {}
    for field in fields:
        if not isinstance(field, basestring):
            raise TypeError("fields must be a list of key names, "
                            "each an instance of %s" % (basestring.__name__,))
        as_dict[field] = 1
    return as_dict
