import { createHash } from 'node:crypto'

import { describe, expect, it } from 'vitest'

import vectors from '../fixtures/v1/security-vectors.json'

interface RiskModule {
  authorizeRemoteAction(input: {
    capability: typeof vectors.capability.document
    capabilityHash: string
    crypto: TestHashProvider
    method: string
    online: boolean
    queueIfOffline: boolean
    foreground: boolean
    unlocked: boolean
    unlockAgeMs: number
    biometricProofVerified?: boolean
  }): Promise<
    | { authorized: true; risk: 'low' | 'medium' | 'high' }
    | {
        authorized: false
        reason:
          | 'app-background'
          | 'app-locked'
          | 'capability-stale'
          | 'crypto-unavailable'
          | 'method-unsupported'
          | 'offline-queue-disallowed'
          | 'step-up-required'
      }
  >
  unknownMessageDisposition(input: {
    kind: 'command' | 'event' | 'security'
    critical: boolean
  }): 'reject' | 'retain-opaque'
}

interface TestHashProvider {
  sha256Base64Url(value: Uint8Array): Promise<string>
}

const nodeHashProvider: TestHashProvider = {
  async sha256Base64Url(value) {
    return createHash('sha256').update(value).digest('base64url')
  },
}

const loadRiskModule = async (): Promise<RiskModule | undefined> => {
  const modulePath = './risk.js'

  try {
    return (await import(/* @vite-ignore */ modulePath)) as RiskModule
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

describe('capability-bound risk authorization', () => {
  it('rejects stale capabilities and unsupported methods', async () => {
    const risk = await loadRiskModule()

    expect(risk, 'the risk policy module must exist').toBeDefined()

    if (!risk) {
      return
    }

    const base = {
      capability: vectors.capability.document,
      capabilityHash: vectors.capability.hash,
      crypto: nodeHashProvider,
      method: 'prompt.submit',
      online: true,
      queueIfOffline: false,
      foreground: true,
      unlocked: true,
      unlockAgeMs: 0,
    }

    await expect(
      risk.authorizeRemoteAction({
        ...base,
        capabilityHash: 'sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
      })
    ).resolves.toEqual({ authorized: false, reason: 'capability-stale' })
    await expect(
      risk.authorizeRemoteAction({
        ...base,
        crypto: {
          async sha256Base64Url() {
            throw new Error('native crypto unavailable')
          },
        },
      })
    ).resolves.toEqual({ authorized: false, reason: 'crypto-unavailable' })
    await expect(
      risk.authorizeRemoteAction({
        ...base,
        capabilityHash: 'sha256-short',
        crypto: {
          async sha256Base64Url() {
            return 'short'
          },
        },
      })
    ).resolves.toEqual({ authorized: false, reason: 'crypto-unavailable' })
    await expect(
      risk.authorizeRemoteAction({ ...base, method: 'terminal.execute' })
    ).resolves.toEqual({ authorized: false, reason: 'method-unsupported' })
    await expect(
      risk.authorizeRemoteAction({
        ...base,
        capability: {
          ...vectors.capability.document,
          methods: {
            ...vectors.capability.document.methods,
            'prompt.submit': {
              risk: 'unknown',
              offline: true,
              biometric: false,
            },
          },
        } as typeof vectors.capability.document,
        capabilityHash:
          'sha256-fJjH90ReOcHUOsvmepSPlrVtCNF78ZH72E_ImDCqUCc',
      })
    ).resolves.toEqual({ authorized: false, reason: 'method-unsupported' })
  })

  it('allows only explicitly offline-capable low-risk prompts to queue', async () => {
    const risk = await loadRiskModule()

    expect(risk, 'the risk policy module must exist').toBeDefined()

    if (!risk) {
      return
    }

    const base = {
      capability: vectors.capability.document,
      capabilityHash: vectors.capability.hash,
      crypto: nodeHashProvider,
      online: false,
      queueIfOffline: true,
      foreground: true,
      unlocked: true,
      unlockAgeMs: 0,
    }

    await expect(
      risk.authorizeRemoteAction({ ...base, method: 'prompt.submit' })
    ).resolves.toEqual({ authorized: true, risk: 'low' })
    await expect(
      risk.authorizeRemoteAction({ ...base, method: 'approval.respond' })
    ).resolves.toEqual({
      authorized: false,
      reason: 'offline-queue-disallowed',
    })
  })

  it('enforces foreground unlock and risk-based step-up', async () => {
    const risk = await loadRiskModule()

    expect(risk, 'the risk policy module must exist').toBeDefined()

    if (!risk) {
      return
    }

    const base = {
      capability: vectors.capability.document,
      capabilityHash: vectors.capability.hash,
      crypto: nodeHashProvider,
      online: true,
      queueIfOffline: false,
      foreground: true,
      unlocked: true,
      unlockAgeMs: 0,
    }

    await expect(
      risk.authorizeRemoteAction({
        ...base,
        method: 'prompt.submit',
        foreground: false,
      })
    ).resolves.toEqual({ authorized: false, reason: 'app-background' })
    await expect(
      risk.authorizeRemoteAction({
        ...base,
        method: 'interrupt.request',
        unlockAgeMs: 300_001,
      })
    ).resolves.toEqual({ authorized: false, reason: 'step-up-required' })
    await expect(
      risk.authorizeRemoteAction({ ...base, method: 'approval.respond' })
    ).resolves.toEqual({ authorized: false, reason: 'step-up-required' })
    await expect(
      risk.authorizeRemoteAction({
        ...base,
        method: 'approval.respond',
        biometricProofVerified: true,
      })
    ).resolves.toEqual({ authorized: true, risk: 'high' })
  })

  it('retains only unknown non-critical events as opaque telemetry', async () => {
    const risk = await loadRiskModule()

    expect(risk, 'the risk policy module must exist').toBeDefined()

    if (!risk) {
      return
    }

    expect(
      risk.unknownMessageDisposition({ kind: 'event', critical: false })
    ).toBe('retain-opaque')
    expect(
      risk.unknownMessageDisposition({ kind: 'event', critical: true })
    ).toBe('reject')
    expect(
      risk.unknownMessageDisposition({ kind: 'command', critical: false })
    ).toBe('reject')
    expect(
      risk.unknownMessageDisposition({ kind: 'security', critical: false })
    ).toBe('reject')
  })
})
