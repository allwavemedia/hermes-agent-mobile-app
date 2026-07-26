import { createHash } from 'node:crypto'

import type { JWK } from 'jose'
import { compactVerify, decodeProtectedHeader, importJWK } from 'jose'
import { describe, expect, it } from 'vitest'

import vectors from '../fixtures/v1/security-vectors.json'

type VerificationReason =
  | 'expired'
  | 'issued-in-future'
  | 'invalid-signature'
  | 'payload-mismatch'
  | 'target-mismatch'
  | 'wrong-algorithm'

interface CanonicalizeModule {
  canonicalizeRemoteDocument(value: unknown): Uint8Array
  remoteDocumentHash(value: unknown, crypto: TestCryptoProvider): Promise<string>
  verifySignedDocument(input: {
    document: Record<string, unknown>
    signature: string
    publicJwk: JWK
    crypto: TestCryptoProvider
    now: Date
    expected: {
      computerId: string
      deviceId?: string
      sessionId?: string
    }
  }): Promise<
    | { valid: true }
    | {
        valid: false
        reason: VerificationReason
      }
  >
}

interface TestCryptoProvider {
  sha256Base64Url(value: Uint8Array): Promise<string>
  verifyEs256Compact(input: {
    signature: string
    publicJwk: JWK
    requiredType: string
  }): Promise<
    | { verified: true; payload: Uint8Array }
    | {
        verified: false
        reason: 'invalid-signature' | 'wrong-algorithm'
      }
  >
}

const nodeCryptoProvider: TestCryptoProvider = {
  async sha256Base64Url(value) {
    return createHash('sha256').update(value).digest('base64url')
  },
  async verifyEs256Compact({ signature, publicJwk, requiredType }) {
    let header: ReturnType<typeof decodeProtectedHeader>

    try {
      header = decodeProtectedHeader(signature)
    } catch {
      return { verified: false, reason: 'invalid-signature' }
    }

    if (header.alg !== 'ES256') {
      return { verified: false, reason: 'wrong-algorithm' }
    }

    if (header.typ !== requiredType) {
      return { verified: false, reason: 'invalid-signature' }
    }

    try {
      const key = await importJWK(publicJwk, 'ES256')

      const { payload } = await compactVerify(signature, key, {
        algorithms: ['ES256'],
      })

      return { verified: true, payload }
    } catch {
      return { verified: false, reason: 'invalid-signature' }
    }
  },
}

const loadCanonicalizeModule =
  async (): Promise<CanonicalizeModule | undefined> => {
    const modulePath = './canonicalize.js'

    try {
      return (await import(/* @vite-ignore */ modulePath)) as CanonicalizeModule
    } catch (error) {
      if (
        error instanceof Error &&
        (error.message.includes('Cannot find module') ||
          error.message.includes('Failed to load url'))
      ) {
        return undefined
      }

      throw error
    }
  }

const wrongAlgorithmSignature = (signature: string): string => {
  const [, payload, proof] = signature.split('.')

  const protectedHeader = Buffer.from(
    JSON.stringify({
      alg: 'ES384',
      typ: 'hermes-remote-control+jws',
    })
  ).toString('base64url')

  return `${protectedHeader}.${payload}.${proof}`
}

describe('RFC 8785 canonicalization and signed-document verification', () => {
  it('matches the cross-runtime canonical bytes and capability hash', async () => {
    const security = await loadCanonicalizeModule()

    expect(security, 'the canonicalization module must exist').toBeDefined()

    if (!security) {
      return
    }

    expect(
      Buffer.from(
        security.canonicalizeRemoteDocument(vectors.signedEnvelope.document)
      ).toString('utf8')
    ).toBe(vectors.signedEnvelope.canonical)
    expect(
      Buffer.from(
        security.canonicalizeRemoteDocument(vectors.capability.document)
      ).toString('utf8')
    ).toBe(vectors.capability.canonical)
    await expect(
      security.remoteDocumentHash(
        vectors.capability.document,
        nodeCryptoProvider
      )
    ).resolves.toBe(vectors.capability.hash)
  })

  it('verifies an ES256 proof only for the intended target and time window', async () => {
    const security = await loadCanonicalizeModule()

    expect(security, 'the signature verifier must exist').toBeDefined()

    if (!security) {
      return
    }

    const verify = (
      overrides: Partial<Parameters<typeof security.verifySignedDocument>[0]> = {}
    ) =>
      security.verifySignedDocument({
        document: vectors.signedEnvelope.document,
        signature: vectors.signedEnvelope.signature,
        publicJwk: vectors.signedEnvelope.publicJwk,
        crypto: nodeCryptoProvider,
        now: new Date('2026-07-26T08:01:00Z'),
        expected: {
          computerId: 'cmp_vector_0001',
          deviceId: 'dev_vector_0001',
          sessionId: 'ses_vector_0001',
        },
        ...overrides,
      })

    await expect(verify()).resolves.toEqual({ valid: true })
    await expect(
      verify({
        expected: {
          computerId: 'cmp_different_0001',
          deviceId: 'dev_vector_0001',
          sessionId: 'ses_vector_0001',
        },
      })
    ).resolves.toEqual({ valid: false, reason: 'target-mismatch' })
    await expect(
      verify({
        expected: {
          computerId: 'cmp_vector_0001',
        },
      })
    ).resolves.toEqual({ valid: false, reason: 'target-mismatch' })
    await expect(
      verify({ now: new Date('2026-07-26T08:05:00.001Z') })
    ).resolves.toEqual({ valid: false, reason: 'expired' })
    await expect(verify({ now: new Date('not-a-date') })).resolves.toEqual({
      valid: false,
      reason: 'invalid-signature',
    })
  })

  it('fails closed on altered payloads and non-ES256 protected headers', async () => {
    const security = await loadCanonicalizeModule()

    expect(security, 'the signature verifier must exist').toBeDefined()

    if (!security) {
      return
    }

    const common = {
      publicJwk: vectors.signedEnvelope.publicJwk,
      crypto: nodeCryptoProvider,
      now: new Date('2026-07-26T08:01:00Z'),
      expected: {
        computerId: 'cmp_vector_0001',
        deviceId: 'dev_vector_0001',
        sessionId: 'ses_vector_0001',
      },
    }

    await expect(
      security.verifySignedDocument({
        ...common,
        document: {
          ...vectors.signedEnvelope.document,
          payload: { queueIfOffline: true, text: 'Continue safely.' },
        },
        signature: vectors.signedEnvelope.signature,
      })
    ).resolves.toEqual({ valid: false, reason: 'payload-mismatch' })
    await expect(
      security.verifySignedDocument({
        ...common,
        document: vectors.signedEnvelope.document,
        signature: wrongAlgorithmSignature(vectors.signedEnvelope.signature),
      })
    ).resolves.toEqual({ valid: false, reason: 'wrong-algorithm' })
    await expect(
      security.verifySignedDocument({
        ...common,
        document: vectors.signedEnvelope.document,
        signature: vectors.signedEnvelope.signature,
        crypto: {
          ...nodeCryptoProvider,
          async verifyEs256Compact() {
            return {
              verified: true,
              payload: {} as Uint8Array,
            }
          },
        },
      })
    ).resolves.toEqual({ valid: false, reason: 'invalid-signature' })
  })
})
