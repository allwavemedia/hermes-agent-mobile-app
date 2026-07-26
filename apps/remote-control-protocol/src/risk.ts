import {
  remoteDocumentHash,
  type RemoteHashProvider,
} from './canonicalize.js'

export type RemoteRisk = 'low' | 'medium' | 'high'

interface RiskCapabilityMethod {
  risk: RemoteRisk
  offline: boolean
  biometric: boolean
}

export interface CapabilityDocument {
  methods: Record<string, RiskCapabilityMethod>
  [key: string]: unknown
}

export type AuthorizationDenialReason =
  | 'app-background'
  | 'app-locked'
  | 'capability-stale'
  | 'crypto-unavailable'
  | 'method-unsupported'
  | 'offline-queue-disallowed'
  | 'step-up-required'

export type AuthorizationResult =
  | { authorized: true; risk: RemoteRisk }
  | { authorized: false; reason: AuthorizationDenialReason }

export interface RemoteActionContext {
  capability: CapabilityDocument
  capabilityHash: string
  crypto: RemoteHashProvider
  method: string
  online: boolean
  queueIfOffline: boolean
  foreground: boolean
  unlocked: boolean
  unlockAgeMs: number
  biometricProofVerified?: boolean
}

const MEDIUM_RISK_UNLOCK_MAX_AGE_MS = 5 * 60 * 1_000

const isCapabilityMethod = (
  value: unknown
): value is RiskCapabilityMethod => {
  if (value === null || Array.isArray(value) || typeof value !== 'object') {
    return false
  }

  const candidate = value as Record<string, unknown>

  return (
    (candidate.risk === 'low' ||
      candidate.risk === 'medium' ||
      candidate.risk === 'high') &&
    typeof candidate.offline === 'boolean' &&
    typeof candidate.biometric === 'boolean'
  )
}

export const authorizeRemoteAction = async ({
  capability,
  capabilityHash,
  crypto,
  method,
  online,
  queueIfOffline,
  foreground,
  unlocked,
  unlockAgeMs,
  biometricProofVerified,
}: RemoteActionContext): Promise<AuthorizationResult> => {
  let computedCapabilityHash: string

  try {
    computedCapabilityHash = await remoteDocumentHash(capability, crypto)
  } catch {
    return { authorized: false, reason: 'crypto-unavailable' }
  }

  if (computedCapabilityHash !== capabilityHash) {
    return { authorized: false, reason: 'capability-stale' }
  }

  const methodCapability = capability.methods[method]

  if (!isCapabilityMethod(methodCapability)) {
    return { authorized: false, reason: 'method-unsupported' }
  }

  if (!foreground) {
    return { authorized: false, reason: 'app-background' }
  }

  if (!unlocked) {
    return { authorized: false, reason: 'app-locked' }
  }

  if (
    !online &&
    (!queueIfOffline ||
      method !== 'prompt.submit' ||
      !methodCapability.offline ||
      methodCapability.risk !== 'low')
  ) {
    return { authorized: false, reason: 'offline-queue-disallowed' }
  }

  if (
    methodCapability.risk === 'medium' &&
    (!Number.isFinite(unlockAgeMs) ||
      unlockAgeMs < 0 ||
      unlockAgeMs > MEDIUM_RISK_UNLOCK_MAX_AGE_MS)
  ) {
    return { authorized: false, reason: 'step-up-required' }
  }

  if (
    (methodCapability.risk === 'high' || methodCapability.biometric) &&
    biometricProofVerified !== true
  ) {
    return { authorized: false, reason: 'step-up-required' }
  }

  return { authorized: true, risk: methodCapability.risk }
}

export const unknownMessageDisposition = ({
  kind,
  critical,
}: {
  kind: 'command' | 'event' | 'security'
  critical: boolean
}): 'reject' | 'retain-opaque' =>
  kind === 'event' && !critical ? 'retain-opaque' : 'reject'
