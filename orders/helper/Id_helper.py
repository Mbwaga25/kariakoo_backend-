import base64
import binascii

def decode_global_id(global_id: str) -> str:
    """
    Decode Relay-style global ID (Base64 "TypeName:ID") if it's valid.
    Otherwise return the original ID (number or UUID).
    """
    try:
        decoded = base64.b64decode(global_id).decode("utf-8")
        if ":" in decoded:
            return decoded.split(":")[1]  # Return the actual ID (number or UUID)
        return global_id
    except (binascii.Error, UnicodeDecodeError):
        # Not Base64 or improperly encoded — just return as-is
        return global_id
