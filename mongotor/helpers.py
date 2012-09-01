import bson
import struct
from mongotor.errors import (DatabaseError, InterfaceError)


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
