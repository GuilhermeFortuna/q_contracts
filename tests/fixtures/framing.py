import base64
import json
import struct


def decode_binary_frame(frame: bytes) -> dict:
    """Decode a binary WebSocket frame into its logical stream envelope.

    Layout:
      offset 0..3: u32 little-endian header length
      offset 4..4+header_len: UTF-8 JSON envelope metadata (payload omitted)
      offset 4+header_len..EOF: raw Arrow IPC bytes
    """
    if len(frame) < 4:
        raise ValueError(f"Frame too short: {len(frame)} bytes, expected at least 4")

    header_len = struct.unpack("<I", frame[:4])[0]
    if len(frame) < 4 + header_len:
        raise ValueError(
            f"Frame truncated: total length {len(frame)} < 4 + header_len {header_len}"
        )

    header_json = frame[4 : 4 + header_len].decode("utf-8")
    envelope = json.loads(header_json)

    ipc_bytes = frame[4 + header_len :]
    payload_b64 = base64.b64encode(ipc_bytes).decode("ascii")

    envelope["payload"] = payload_b64
    return envelope


def encode_binary_frame(envelope: dict) -> bytes:
    """Encode a logical stream envelope into a binary WebSocket frame.

    Extracts the base64 payload into raw binary IPC bytes, serializes the
    remaining envelope metadata to JSON, and prefixes with a 4-byte LE length.
    """
    env_copy = dict(envelope)
    payload_b64 = env_copy.pop("payload")
    ipc_bytes = base64.b64decode(payload_b64)

    header_bytes = json.dumps(env_copy, indent=2).encode("utf-8")
    header_len = len(header_bytes)

    return struct.pack("<I", header_len) + header_bytes + ipc_bytes
