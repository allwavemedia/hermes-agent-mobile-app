# File Transfer

## Boundary

Remote file transfer is an attachment transport into or out of an already authorized Hermes session. It is not a remote filesystem API. Android never receives an arbitrary host path, directory listing, or write destination. The host adapter maps an accepted manifest to existing Hermes attachment handlers and local workspace/tool policy.

## Upload flow

1. App obtains a `content://` URI from Android system picker.
2. App reads metadata, enforces advertised size/MIME allowlist, and streams SHA-256 calculation without copying into long-lived app storage.
3. App sends `attachment.offer` with generated attachment ID, safe filename, size, MIME, digest, session/revision/capability binding, and 15-minute expiry.
4. Host returns a signed acceptance and transfer method: relay staged, direct stream, or reject.
5. Relay staged mode uses a one-attachment, one-device, short-lived upload grant. Chunks are bounded and resumable by byte range.
6. Relay verifies size/digest after assembly, encrypts each object with per-computer key/AAD, and notifies host.
7. Host downloads to an unpredictable file in a broker-owned `0700`/user-only temporary directory, verifies digest again, and passes the resolved local file only to the existing Hermes attachment handler.
8. Consumption or expiry deletes local and relay temporary data; completion event reports safe metadata.

## Download flow

Hermes may advertise an output attachment only after existing tool/workspace policy produces it. Host creates a manifest with safe filename, size, MIME, SHA-256, source session/event, and expiry. Relay/default or direct transport streams bytes. Android writes through the Storage Access Framework or app cache and verifies digest before exposing “Open/Share.” It never infers a host path from filename.

## Security controls

- default 50 MiB/file and 200 MiB/computer temporary aggregate;
- MIME is advisory; host inspects magic/handler compatibility and can narrow allowlist;
- path separators, control characters, reserved Windows names, leading dots, and excessive length are normalized for display; storage name is generated;
- archive extraction is not performed by relay/broker;
- symlinks/hardlinks are never followed;
- partial files are non-executable and unavailable to Hermes;
- hash mismatch deletes bytes and raises `attachment.hash`;
- upload grant binds device, computer, session, attachment, size, digest, range, expiry;
- step-up applies when host capability classifies a file operation as sensitive;
- logs contain attachment ID, size bucket, MIME category, result, and digest prefix only—never filename/content/path.

## Retention modes

Default temporary mode permits staged relay objects for at most the grant/manifest lifetime; the hourly sweeper is a maximum cleanup delay, not an availability promise. Zero-retention mode disables relay staging. Direct live transfer may be advertised, but if either endpoint disconnects the transfer fails and must restart with a new manifest.

## Resumption

Relay upload tracks verified byte ranges and object ETag/version. Resume request is signed and must match manifest digest/size and unexpired grant. Download resumption validates range plus final digest. Changing metadata creates a new attachment ID; an idempotency key cannot be reused for different bytes.

## Malware/content handling

MVP does not promise malware scanning. Product copy states that attachments are handled by the paired computer and its existing defenses. The host may add a scanner hook later, but “scan unavailable” must not be represented as “safe.” Executable and platform installer MIME/extensions are denied by default for inbound Android attachments unless a later threat review creates an explicit capability.
