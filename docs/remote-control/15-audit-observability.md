# Audit and Observability

## Goals

Operators must answer whether hosts are connected, replay/queues are healthy, pairing/revocation works, and security controls fail closed—without collecting session content or secrets.

## Audit schema

Each host/relay security event contains:

- event ID, schema version, UTC time;
- component/version/environment;
- actor kind and opaque ID/key thumbprint prefix;
- target computer/device/session opaque ID;
- operation and risk class;
- result/reason code;
- connection/command/request IDs;
- session revision/capability hash prefix/action digest prefix where needed;
- retention mode;
- duration/size bucket;
- trace ID.

Forbidden fields: prompts, responses, reasoning, tool arguments/output, filenames/paths, terminal content, attachment bytes, pairing capability, credentials/JWS, private/public full JWK, nonces, provider/model secrets, environment, stack traces containing data.

Host audit default retention is local user policy; relay security metadata default is 30 days. Zero retention does not disable content-free abuse/revocation audit.

## Logs

Structured JSON logging uses an allowlist serializer. Exceptions are mapped to stable codes; raw protocol payloads and HTTP/WS frames are never logged. Development frame logging is prohibited rather than merely disabled in production. A CI canary suite sends unique fake secrets/prompts/paths and scans captured logs, crash output, Android Logcat, and support bundle.

Support bundle includes versions, feature flags without secret values, connectivity timings, public thumbprint prefixes, counts, last error codes, and redacted audit. User reviews the generated manifest before sharing.

## Metrics

Counters:

- connections/auth success/failure/revocation;
- pair offers/claims/success/expiry/replay;
- envelopes by safe type/result;
- schema/signature/replay/capability rejection;
- queue enqueue/deliver/expire/reject;
- attachment offer/bytes/result;
- event gap/replay/snapshot reset;
- direct fallback success/pin failure.

Gauges:

- connected hosts/devices;
- active subscriptions;
- queue bytes/oldest age;
- expired rows/objects awaiting deletion;
- event loop/database/blob latency;
- relay process memory/CPU.

Histograms:

- connect/auth/snapshot time;
- host-to-mobile event latency;
- command acknowledge/complete latency;
- queue delivery delay;
- attachment throughput.

Labels are bounded: environment, protocol minor, result code, risk, retention mode. Never label by computer/device/session/attachment IDs.

## Tracing

Trace context uses random trace/span IDs propagated separately from security identity. A trace may connect relay receipt, host verification, gateway invocation, and receipt, but span attributes follow the audit allowlist. Sampling is higher for errors and never changes content capture rules.

## Alerts and SLOs

- authentication/replay/signature rejection spike;
- oldest expired content > one hour;
- queue utilization >80% of per-computer/global budget;
- PostgreSQL/KEK unavailable or readiness false;
- snapshot reset rate >5% of reconnects;
- p95 event latency >1 s or command ack >2 s for 15 minutes;
- relay crash loop/connection churn;
- host secure-store or broker-registration failure;
- attachment hash mismatch (page immediately if clustered).

Availability SLO proposal: 99.5% monthly for authenticated relay connection and command routing in MVP, excluding local host/network/model/tool execution. Correctness and security rejections are not counted as downtime.

## Privacy operations

Operator runbooks cover data inventory, deletion by computer ID, retention-mode transition, backup caveat, key rotation, incident containment, and legal hold conflict. Deletion requests authenticate through paired host/device control; support staff cannot infer pairing capability. Future analytics require a separate privacy review and opt-in.
