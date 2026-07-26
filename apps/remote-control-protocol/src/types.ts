export type RemoteControlSchemaName =
  | 'capability'
  | 'command'
  | 'envelope'
  | 'event'
  | 'pairing'
  | 'snapshot'

export interface ValidationIssue {
  instancePath: string
  keyword: string
  message: string
  schemaPath: string
}

export interface ValidationResult {
  valid: boolean
  errors: readonly ValidationIssue[]
}

export interface RemoteControlEnvelope<Payload = Record<string, unknown>> {
  protocol: 'hermes.remote-control/1.0'
  envelopeId: string
  kind:
    | 'control'
    | 'pairing'
    | 'presence'
    | 'subscription'
    | 'state'
    | 'command'
    | 'receipt'
    | 'device'
  type: string
  critical?: boolean
  computerId: string
  deviceId?: string
  sessionId?: string
  epoch?: string
  issuedAt: string
  expiresAt: string
  jti: string
  idempotencyKey?: string
  expectedSessionRevision?: number
  capabilityHash?: string
  payload: Payload
  signature: string
}

export interface RemoteControlEvent<Data = Record<string, unknown>> {
  seq: number
  prevSeq: number
  eventId: string
  occurredAt: string
  eventType: string
  causedByCommandId?: string
  data: Data
}

export interface CapabilityMethod {
  risk: 'low' | 'medium' | 'high'
  offline: boolean
  biometric: boolean
  maxBytes?: number
}

export interface CapabilitySnapshot {
  capabilityVersion: 1
  computerId: string
  sessionId: string
  sessionRevision: number
  issuedAt: string
  expiresAt: string
  methods: Record<string, CapabilityMethod>
  constraints: {
    attachmentMaxBytes?: number
    terminalRead?: boolean
    terminalWrite?: boolean
    reasoningVisible?: boolean
  }
  signature: string
}

export interface SessionSnapshot {
  epoch: string
  snapshotSeq: number
  sessionRevision: number
  generatedAt: string
  session: {
    id: string
    title: string
    project?: string
    cwdLabel?: string
    model?: string
    status:
      | 'idle'
      | 'running'
      | 'waiting'
      | 'interrupted'
      | 'completed'
      | 'failed'
    activeRunId?: string | null
  }
  transcript: readonly Record<string, unknown>[]
  activities: readonly Record<string, unknown>[]
  pendingRequests: readonly Record<string, unknown>[]
  terminals: readonly Record<string, unknown>[]
  attachments: readonly Record<string, unknown>[]
  capabilityHash: string
}

export type RemoteControlCommand =
  | {
      commandType: 'prompt.submit'
      text: string
      queueIfOffline: boolean
    }
  | {
      commandType: 'approval.respond'
      requestId: string
      approvalId: string
      toolCallId: string
      activeRunId: string
      decision: 'approve_once' | 'deny'
      actionDigest: string
      displayDigest: string
      requestEventSeq: number
      biometricSignature?: string
    }
  | {
      commandType: 'clarify.respond'
      requestId: string
      activeRunId: string
      requestEventSeq: number
      answer: string
    }
  | {
      commandType: 'session.interrupt' | 'session.steer'
      activeRunId: string
      text?: string
    }
  | {
      commandType: 'session.create'
      projectId: string
      modelId?: string
      title?: string
      remoteEnable?: boolean
    }

export interface CommandReceipt {
  commandId: string
  idempotencyKey: string
  status: 'accepted' | 'rejected' | 'expired' | 'duplicate'
  sessionRevision: number
  reason?: string
}
