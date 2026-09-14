# WebSocket Transport Framing Specification

**Status:** Authoritative protocol specification  
**Boundary:** `schema/stream/`  
**Reference:** [`Q-009 Stream Payload and Replay Contracts Spec`](../../docs/development/specs/Q-009-stream-payload-and-replay-contracts-spec.md)

---

## 1. Motivation

The Q stream transport uses WebSocket connections to multiplex real-time market data, execution events, and job progress.

Stream entries are logically modeled by the canonical `StreamEnvelope` (`schema/stream/envelope.schema.json`). For columnar market data payloads (`quotes`, `bars.forming`, `bars.completed`), payloads are encoded as Arrow IPC stream batches.

Transmitting binary Arrow IPC batches inside a text JSON envelope requires Base64 encoding. Base64 introduces a ~33% wire size penalty and incurs CPU encode/decode overhead on every quote — the hottest path in the system.

To avoid this inflation and overhead, the WebSocket transport supports two frame types:
1. **Text Frames (`opcode 0x1`):** For structured JSON payloads and control frames.
2. **Binary Frames (`opcode 0x2`):** For Arrow IPC payloads, combining a JSON metadata header with raw Arrow IPC stream bytes.

---

## 2. Frame Types

### 2.1 Text Frames (JSON)

Text WebSocket frames carry UTF-8 encoded JSON. They are used for:
- Client control requests (`SubscribeFrame`).
- Server control frames (`SubscribedFrame`, `CursorExpiredFrame`, `LaggingFrame`, `EpochChangedFrame`, `RejectedFrame`).
- Stream envelopes whose `payload_kind` is `"control"` (e.g. `jobs.progress`, `jobs.terminal`).
- REST replay responses (`HistoryPageResponse`, `HistoryExpiredResponse`, `LatestValuesResponse`, `SnapshotWatermark`).

Every server control frame carries a `type` discriminator: `subscribed`, `rejected`, `cursor_expired`, `lagging`, or `epoch_changed`. Stream envelopes never carry `type` (the envelope schema forbids additional properties). A client therefore classifies a server text frame by one rule: if the parsed object has `type`, it is the control frame that value names; otherwise it is a stream envelope. Clients must not infer a frame's kind from which other keys are present.

### 2.2 Binary Frames (Header + Arrow IPC)

Binary WebSocket frames carry a binary-packed envelope and are used exclusively when `payload_kind` is `"arrow_ipc"`.

#### Wire Layout

```
+-------------------+-----------------------------------+-----------------------------------+
| header_len (4 B)  | header_bytes (header_len B)       | arrow_ipc_bytes (remaining B)     |
| u32 little-endian | UTF-8 JSON (envelope w/o payload) | Raw Arrow IPC stream batch        |
+-------------------+-----------------------------------+-----------------------------------+
0                   4                                   4 + header_len                      Frame End
```

1. **Offset 0..3 (4 bytes): `header_len`**
   - Unsigned 32-bit integer in little-endian byte order (`u32`).
   - Declares the exact byte length of the UTF-8 JSON header that follows immediately.

2. **Offset 4 .. (4 + `header_len`) bytes: `header_bytes`**
   - UTF-8 encoded JSON string representing the stream envelope with the `"payload"` property omitted.
   - Contains all envelope routing and ordering metadata:
     - `topic` (string)
     - `schema_major` (integer >= 1)
     - `seq` (integer >= 0)
     - `epoch` (string)
     - `producer_id` (string)
     - `origin_ts` (RFC 3339 UTC string)
     - `payload_kind` (`"arrow_ipc"`)
     - `payload_schema` (schema identifier, e.g. `"schema/api/arrow/ticks.schema.json"`)
     - `key` (optional routing object, e.g. `{"symbol": "WINZ25"}`)

3. **Offset (4 + `header_len`) .. EOF: `arrow_ipc_bytes`**
   - Raw binary Arrow IPC stream format bytes up to the end of the frame.
   - Contains the RecordBatch conforming to `payload_schema`.
   - Zero-copy decodable by Arrow libraries (e.g. `apache-arrow` in JS/TS or `arrow-rs` in Rust).

---

## 3. Logical Equivalence and Reconstruction

A binary frame is strictly isomorphic to its logical JSON `StreamEnvelope` representation:

$$\text{StreamEnvelope} = \text{Header JSON} \cup \{ \text{"payload"}: \text{Base64}(\text{arrow\_ipc\_bytes}) \}$$

Consumers that require the logical envelope can reconstruct it by taking the parsed header object and setting its `"payload"` property to the Base64-encoded string of `arrow_ipc_bytes`. High-performance consumers typically skip Base64 encoding entirely and feed `arrow_ipc_bytes` directly to an Arrow RecordBatch reader.

---

## 4. Decoding Reference Implementations

### 4.1 TypeScript Reference Decoder

```typescript
import { tableFromIPC } from "apache-arrow";

export interface DecodedBinaryFrame {
  envelope: {
    topic: string;
    schema_major: number;
    seq: number;
    epoch: string;
    producer_id: string;
    origin_ts: string;
    payload_kind: "arrow_ipc";
    payload_schema: string;
    key?: Record<string, string>;
  };
  table: ReturnType<typeof tableFromIPC>;
}

export function decodeBinaryFrame(buffer: ArrayBuffer): DecodedBinaryFrame {
  const view = new DataView(buffer);
  const headerLen = view.getUint32(0, true); // little-endian

  const headerBytes = new Uint8Array(buffer, 4, headerLen);
  const headerText = new TextDecoder("utf-8").decode(headerBytes);
  const envelope = JSON.parse(headerText);

  const ipcBytes = new Uint8Array(buffer, 4 + headerLen);
  const table = tableFromIPC(ipcBytes);

  return { envelope, table };
}
```

### 4.2 Rust Reference Decoder

```rust
use arrow::ipc::reader::StreamReader;
use arrow::record_batch::RecordBatch;
use byteorder::{ByteOrder, LittleEndian};
use serde::Deserialize;
use std::io::Cursor;

#[derive(Debug, Deserialize)]
pub struct FrameHeader {
    pub topic: String,
    pub schema_major: u32,
    pub seq: u64,
    pub epoch: String,
    pub producer_id: String,
    pub origin_ts: String,
    pub payload_kind: String,
    pub payload_schema: String,
    pub key: Option<std::collections::HashMap<String, String>>,
}

pub struct DecodedFrame {
    pub header: FrameHeader,
    pub batches: Vec<RecordBatch>,
}

pub fn decode_binary_frame(bytes: &[u8]) -> Result<DecodedFrame, Box<dyn std::error::Error>> {
    if bytes.len() < 4 {
        return Err("Frame too short for header length prefix".into());
    }

    let header_len = LittleEndian::read_u32(&bytes[0..4]) as usize;
    if bytes.len() < 4 + header_len {
        return Err("Frame truncated before header end".into());
    }

    let header_json = std::str::from_utf8(&bytes[4..4 + header_len])?;
    let header: FrameHeader = serde_json::from_str(header_json)?;

    let ipc_slice = &bytes[4 + header_len..];
    let reader = StreamReader::try_new(Cursor::new(ipc_slice), None)?;
    let mut batches = Vec::new();
    for batch in reader {
        batches.push(batch?);
    }

    Ok(DecodedFrame { header, batches })
}
```
