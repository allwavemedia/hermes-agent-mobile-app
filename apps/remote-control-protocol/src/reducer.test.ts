import fc from 'fast-check'
import { describe, expect, it } from 'vitest'

import type { RemoteControlEvent } from './types.js'

interface ReplaySnapshot<Projection> {
  epoch: string
  snapshotSeq: number
  projection: Projection
}

interface ReplayState<Projection> extends ReplaySnapshot<Projection> {
  seq: number
  appliedEvents: readonly { eventId: string; seq: number }[]
}

type ReplayResult<Projection> =
  | { status: 'applied'; state: ReplayState<Projection> }
  | { status: 'duplicate'; state: ReplayState<Projection> }
  | {
      status: 'gap'
      state: ReplayState<Projection>
      expectedSeq: number
      receivedSeq: number
    }
  | {
      status: 'conflict'
      state: ReplayState<Projection>
      seq: number
    }
  | {
      status: 'reset-required'
      state: ReplayState<Projection>
      expectedEpoch: string
      receivedEpoch: string
    }

interface ReducerModule {
  MAX_REPLAY_IDENTITIES?: number
  createReplayState<Projection>(
    snapshot: ReplaySnapshot<Projection>
  ): ReplayState<Projection>
  resetReplayState<Projection>(
    state: ReplayState<Projection>,
    snapshot: ReplaySnapshot<Projection>
  ): ReplayState<Projection>
  applyReplayEvent<Projection, Data>(
    state: ReplayState<Projection>,
    incoming: {
      epoch: string
      event: RemoteControlEvent<Data>
    },
    reduce: (
      projection: Projection,
      event: RemoteControlEvent<Data>
    ) => Projection
  ): ReplayResult<Projection>
}

const loadReducerModule = async (): Promise<ReducerModule | undefined> => {
  const modulePath = './reducer.js'

  try {
    return (await import(/* @vite-ignore */ modulePath)) as ReducerModule
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

const event = (
  seq: number,
  prevSeq: number,
  eventId: string,
  delta: number
): RemoteControlEvent<{ delta: number }> => ({
  seq,
  prevSeq,
  eventId,
  occurredAt: '2026-07-26T08:00:00Z',
  eventType: 'message.delta',
  data: { delta },
})

const addDelta = (
  projection: number,
  nextEvent: RemoteControlEvent<{ delta: number }>
): number => projection + nextEvent.data.delta

describe('ordered replay reducer', () => {
  it('applies every duplicate at most once', async () => {
    const reducer = await loadReducerModule()

    expect(reducer, 'the ordered replay reducer must exist').toBeDefined()

    if (!reducer) {
      return
    }

    fc.assert(
      fc.property(
        fc.nat({ max: 10_000 }),
        fc.uuid(),
        fc.integer(),
        (snapshotSeq, eventId, delta) => {
          const state = reducer.createReplayState({
            epoch: 'epoch-duplicate',
            snapshotSeq,
            projection: 0,
          })

          const nextEvent = event(snapshotSeq + 1, snapshotSeq, eventId, delta)

          const first = reducer.applyReplayEvent(
            state,
            { epoch: state.epoch, event: nextEvent },
            addDelta
          )

          expect(first.status).toBe('applied')

          if (first.status !== 'applied') {
            return
          }

          const duplicate = reducer.applyReplayEvent(
            first.state,
            { epoch: state.epoch, event: nextEvent },
            addDelta
          )

          expect(duplicate.status).toBe('duplicate')
          expect(duplicate.state).toBe(first.state)
          expect(duplicate.state.projection).toBe(delta)
        }
      ),
      { numRuns: 1_000 }
    )
  })

  it('rejects sequence gaps without changing state', async () => {
    const reducer = await loadReducerModule()

    expect(reducer, 'the ordered replay reducer must exist').toBeDefined()

    if (!reducer) {
      return
    }

    fc.assert(
      fc.property(
        fc.nat({ max: 10_000 }),
        fc.integer({ min: 2, max: 1_000 }),
        fc.uuid(),
        fc.boolean(),
        (snapshotSeq, gap, eventId, mismatchPrevSeq) => {
          const state = reducer.createReplayState({
            epoch: 'epoch-gap',
            snapshotSeq,
            projection: 0,
          })

          const receivedSeq = mismatchPrevSeq
            ? snapshotSeq + 1
            : snapshotSeq + gap

          const prevSeq = mismatchPrevSeq ? snapshotSeq + 1 : receivedSeq - 1

          const result = reducer.applyReplayEvent(
            state,
            {
              epoch: state.epoch,
              event: event(receivedSeq, prevSeq, eventId, 1),
            },
            addDelta
          )

          expect(result.status).toBe('gap')

          if (result.status !== 'gap') {
            return
          }

          expect(result.state).toBe(state)
          expect(result.expectedSeq).toBe(snapshotSeq + 1)
          expect(result.receivedSeq).toBe(receivedSeq)
        }
      ),
      { numRuns: 1_000 }
    )
  })

  it('treats a conflicting event at the same sequence as a security error', async () => {
    const reducer = await loadReducerModule()

    expect(reducer, 'the ordered replay reducer must exist').toBeDefined()

    if (!reducer) {
      return
    }

    fc.assert(
      fc.property(
        fc.uuid(),
        fc.uuid(),
        fc.integer(),
        (firstId, secondId, delta) => {
          fc.pre(firstId !== secondId)

          const state = reducer.createReplayState({
            epoch: 'epoch-conflict',
            snapshotSeq: 0,
            projection: 0,
          })

          const first = reducer.applyReplayEvent(
            state,
            { epoch: state.epoch, event: event(1, 0, firstId, delta) },
            addDelta
          )

          expect(first.status).toBe('applied')

          if (first.status !== 'applied') {
            return
          }

          const conflict = reducer.applyReplayEvent(
            first.state,
            { epoch: state.epoch, event: event(1, 0, secondId, delta) },
            addDelta
          )

          expect(conflict.status).toBe('conflict')
          expect(conflict.state).toBe(first.state)
        }
      ),
      { numRuns: 1_000 }
    )
  })

  it('clears replay identity only when a snapshot resets the epoch', async () => {
    const reducer = await loadReducerModule()

    expect(reducer, 'the ordered replay reducer must exist').toBeDefined()

    if (!reducer) {
      return
    }

    fc.assert(
      fc.property(
        fc.uuid(),
        fc.nat({ max: 10_000 }),
        fc.integer(),
        (eventId, snapshotSeq, delta) => {
          const oldState = reducer.createReplayState({
            epoch: 'epoch-old',
            snapshotSeq: 0,
            projection: 0,
          })

          const oldResult = reducer.applyReplayEvent(
            oldState,
            { epoch: oldState.epoch, event: event(1, 0, eventId, delta) },
            addDelta
          )

          expect(oldResult.status).toBe('applied')

          if (oldResult.status !== 'applied') {
            return
          }

          const resetState = reducer.resetReplayState(oldResult.state, {
            epoch: 'epoch-new',
            snapshotSeq,
            projection: 100,
          })

          const nextEvent = event(
            snapshotSeq + 1,
            snapshotSeq,
            eventId,
            delta
          )

          const staleEpoch = reducer.applyReplayEvent(
            resetState,
            { epoch: oldState.epoch, event: nextEvent },
            addDelta
          )

          expect(staleEpoch.status).toBe('reset-required')
          expect(staleEpoch.state).toBe(resetState)

          const currentEpoch = reducer.applyReplayEvent(
            resetState,
            { epoch: resetState.epoch, event: nextEvent },
            addDelta
          )

          expect(currentEpoch.status).toBe('applied')
          expect(currentEpoch.state.projection).toBe(100 + delta)
        }
      ),
      { numRuns: 1_000 }
    )
  })

  it('bounds replay identity history independently of session duration', async () => {
    const reducer = await loadReducerModule()

    expect(reducer, 'the ordered replay reducer must exist').toBeDefined()

    if (!reducer) {
      return
    }

    expect(
      reducer.MAX_REPLAY_IDENTITIES,
      'the replay identity window must be explicitly bounded'
    ).toBeDefined()

    if (reducer.MAX_REPLAY_IDENTITIES === undefined) {
      return
    }

    expect(reducer.MAX_REPLAY_IDENTITIES).toBeGreaterThan(0)
    expect(Number.isSafeInteger(reducer.MAX_REPLAY_IDENTITIES)).toBe(true)

    let state = reducer.createReplayState({
      epoch: 'epoch-bounded',
      snapshotSeq: 0,
      projection: 0,
    })

    const eventCount = reducer.MAX_REPLAY_IDENTITIES + 1

    for (let seq = 1; seq <= eventCount; seq += 1) {
      const result = reducer.applyReplayEvent(
        state,
        {
          epoch: state.epoch,
          event: event(seq, seq - 1, `event_${seq.toString().padStart(8, '0')}`, 1),
        },
        addDelta
      )

      expect(result.status).toBe('applied')

      if (result.status !== 'applied') {
        return
      }

      state = result.state
    }

    expect(state.appliedEvents).toHaveLength(reducer.MAX_REPLAY_IDENTITIES)
    expect(state.projection).toBe(eventCount)
  })
})
