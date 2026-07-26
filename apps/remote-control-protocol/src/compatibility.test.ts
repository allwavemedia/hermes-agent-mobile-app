import fc from 'fast-check'
import { describe, expect, it } from 'vitest'

interface ProtocolRange {
  major: number
  minMinor: number
  maxMinor: number
}

type NegotiationResult =
  | {
      supported: true
      major: number
      minor: number
    }
  | {
      supported: false
      error: 'protocol.unsupported'
      reason: 'invalid-range' | 'major-mismatch' | 'minor-range-disjoint'
    }

interface CompatibilityModule {
  negotiateProtocol(
    local: ProtocolRange,
    remote: ProtocolRange
  ): NegotiationResult
}

const loadCompatibilityModule = async (): Promise<
  CompatibilityModule | undefined
> => {
  const modulePath = './compatibility.js'

  try {
    return (await import(/* @vite-ignore */ modulePath)) as CompatibilityModule
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

describe('protocol compatibility negotiation', () => {
  it('chooses the highest minor shared by both peers', async () => {
    const compatibility = await loadCompatibilityModule()

    expect(
      compatibility,
      'the protocol compatibility negotiator must exist'
    ).toBeDefined()

    if (!compatibility) {
      return
    }

    fc.assert(
      fc.property(
        fc.nat({ max: 100 }),
        fc.nat({ max: 100 }),
        fc.nat({ max: 100 }),
        fc.nat({ max: 100 }),
        fc.nat({ max: 100 }),
        fc.nat({ max: 100 }),
        (
          major,
          pivot,
          localLower,
          remoteLower,
          localUpper,
          remoteUpper
        ) => {
          const local: ProtocolRange = {
            major,
            minMinor: Math.max(0, pivot - localLower),
            maxMinor: pivot + localUpper,
          }

          const remote: ProtocolRange = {
            major,
            minMinor: Math.max(0, pivot - remoteLower),
            maxMinor: pivot + remoteUpper,
          }

          const result = compatibility.negotiateProtocol(local, remote)

          expect(result.supported).toBe(true)

          if (!result.supported) {
            return
          }

          expect(result.major).toBe(major)
          expect(result.minor).toBe(
            Math.min(local.maxMinor, remote.maxMinor)
          )
        }
      ),
      { numRuns: 1_000 }
    )
  })

  it('fails closed when major versions differ', async () => {
    const compatibility = await loadCompatibilityModule()

    expect(
      compatibility,
      'the protocol compatibility negotiator must exist'
    ).toBeDefined()

    if (!compatibility) {
      return
    }

    fc.assert(
      fc.property(fc.nat({ max: 100 }), fc.nat({ max: 100 }), (major, minor) => {
        const result = compatibility.negotiateProtocol(
          { major, minMinor: 0, maxMinor: minor },
          { major: major + 1, minMinor: 0, maxMinor: minor }
        )

        expect(result).toEqual({
          supported: false,
          error: 'protocol.unsupported',
          reason: 'major-mismatch',
        })
      }),
      { numRuns: 1_000 }
    )
  })

  it('fails closed when minor ranges do not overlap', async () => {
    const compatibility = await loadCompatibilityModule()

    expect(
      compatibility,
      'the protocol compatibility negotiator must exist'
    ).toBeDefined()

    if (!compatibility) {
      return
    }

    fc.assert(
      fc.property(
        fc.nat({ max: 100 }),
        fc.nat({ max: 10_000 }),
        fc.integer({ min: 1, max: 1_000 }),
        (major, localMax, distance) => {
          const result = compatibility.negotiateProtocol(
            { major, minMinor: 0, maxMinor: localMax },
            {
              major,
              minMinor: localMax + distance,
              maxMinor: localMax + distance + 10,
            }
          )

          expect(result).toEqual({
            supported: false,
            error: 'protocol.unsupported',
            reason: 'minor-range-disjoint',
          })
        }
      ),
      { numRuns: 1_000 }
    )
  })

  it('rejects malformed version ranges', async () => {
    const compatibility = await loadCompatibilityModule()

    expect(
      compatibility,
      'the protocol compatibility negotiator must exist'
    ).toBeDefined()

    if (!compatibility) {
      return
    }

    expect(
      compatibility.negotiateProtocol(
        { major: 1, minMinor: 2, maxMinor: 1 },
        { major: 1, minMinor: 0, maxMinor: 1 }
      )
    ).toEqual({
      supported: false,
      error: 'protocol.unsupported',
      reason: 'invalid-range',
    })
  })
})
