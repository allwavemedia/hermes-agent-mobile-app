import canonicalize from 'canonicalize'

const JWS_TYPE = 'hermes-remote-control+jws'

export type VerificationReason =
  | 'expired'
  | 'issued-in-future'
  | 'invalid-signature'
  | 'payload-mismatch'
  | 'target-mismatch'
  | 'wrong-algorithm'

export type SignedDocumentVerification =
  | { valid: true }
  | { valid: false; reason: VerificationReason }

export interface SignedDocumentTarget {
  computerId: string
  deviceId?: string
  sessionId?: string
}

export interface VerifySignedDocumentInput {
  document: Record<string, unknown>
  signature: string
  publicJwk: PublicEcJwk
  crypto: RemoteCryptoProvider
  now: Date
  expected: SignedDocumentTarget
}

export interface PublicEcJwk {
  kty: string
  crv: string
  x?: string
  y?: string
  d?: string
  [key: string]: unknown
}

export interface RemoteHashProvider {
  sha256Base64Url(value: Uint8Array): Promise<string>
}

export interface RemoteCryptoProvider extends RemoteHashProvider {
  verifyEs256Compact(input: {
    signature: string
    publicJwk: PublicEcJwk
    requiredType: string
  }): Promise<
    | { verified: true; payload: Uint8Array }
    | {
        verified: false
        reason: 'invalid-signature' | 'wrong-algorithm'
      }
  >
}

const withoutSignature = (value: unknown): unknown => {
  if (
    value === null ||
    Array.isArray(value) ||
    typeof value !== 'object'
  ) {
    return value
  }

  const unsigned = { ...(value as Record<string, unknown>) }
  delete unsigned.signature

  return unsigned
}

export const canonicalizeRemoteDocument = (value: unknown): Uint8Array => {
  const serialized = canonicalize(withoutSignature(value))

  if (serialized === undefined) {
    throw new TypeError('remote-control document is not RFC 8785 serializable')
  }

  return new TextEncoder().encode(serialized)
}

export const remoteDocumentHash = async (
  value: unknown,
  crypto: RemoteHashProvider
): Promise<string> => {
  const digest = await crypto.sha256Base64Url(
    canonicalizeRemoteDocument(value)
  )

  if (!/^[A-Za-z0-9_-]{43}$/.test(digest)) {
    throw new TypeError('crypto provider returned an invalid SHA-256 digest')
  }

  return `sha256-${digest}`
}

const timestamp = (value: unknown): number | undefined => {
  if (typeof value !== 'string') {
    return undefined
  }

  const parsed = Date.parse(value)

  return Number.isFinite(parsed) ? parsed : undefined
}

const targetMatches = (
  document: Record<string, unknown>,
  expected: SignedDocumentTarget
): boolean =>
  document.computerId === expected.computerId &&
  document.deviceId === expected.deviceId &&
  document.sessionId === expected.sessionId

export const verifySignedDocument = async ({
  document,
  signature,
  publicJwk,
  crypto,
  now,
  expected,
}: VerifySignedDocumentInput): Promise<SignedDocumentVerification> => {
  if (
    publicJwk.kty !== 'EC' ||
    publicJwk.crv !== 'P-256' ||
    typeof publicJwk.x !== 'string' ||
    typeof publicJwk.y !== 'string' ||
    Object.hasOwn(publicJwk, 'd')
  ) {
    return { valid: false, reason: 'invalid-signature' }
  }

  let verification: Awaited<
    ReturnType<RemoteCryptoProvider['verifyEs256Compact']>
  >

  try {
    verification = await crypto.verifyEs256Compact({
      signature,
      publicJwk,
      requiredType: JWS_TYPE,
    })
  } catch {
    return { valid: false, reason: 'invalid-signature' }
  }

  if (!verification.verified) {
    return { valid: false, reason: verification.reason }
  }

  if (!(verification.payload instanceof Uint8Array)) {
    return { valid: false, reason: 'invalid-signature' }
  }

  let expectedPayload: Uint8Array

  try {
    expectedPayload = canonicalizeRemoteDocument(document)
  } catch {
    return { valid: false, reason: 'payload-mismatch' }
  }

  if (
    verification.payload.byteLength !== expectedPayload.byteLength ||
    !verification.payload.every(
      (value, index) => value === expectedPayload[index]
    )
  ) {
    return { valid: false, reason: 'payload-mismatch' }
  }

  if (!targetMatches(document, expected)) {
    return { valid: false, reason: 'target-mismatch' }
  }

  const issuedAt = timestamp(document.issuedAt)
  const expiresAt = timestamp(document.expiresAt)
  const currentTime = now.getTime()

  if (
    issuedAt === undefined ||
    expiresAt === undefined ||
    !Number.isFinite(currentTime) ||
    expiresAt <= issuedAt
  ) {
    return { valid: false, reason: 'invalid-signature' }
  }

  if (currentTime < issuedAt) {
    return { valid: false, reason: 'issued-in-future' }
  }

  if (currentTime >= expiresAt) {
    return { valid: false, reason: 'expired' }
  }

  return { valid: true }
}
