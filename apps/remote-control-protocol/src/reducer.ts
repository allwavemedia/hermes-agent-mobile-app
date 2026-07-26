import type { RemoteControlEvent } from './types.js'

export const MAX_REPLAY_IDENTITIES = 4_096

export interface ReplaySnapshot<Projection> {
  epoch: string
  snapshotSeq: number
  projection: Projection
}

interface AppliedEventIdentity {
  eventId: string
  seq: number
}

export interface ReplayState<Projection> extends ReplaySnapshot<Projection> {
  seq: number
  appliedEvents: readonly AppliedEventIdentity[]
}

export type ReplayResult<Projection> =
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

const freezeState = <Projection>(
  state: ReplayState<Projection>
): ReplayState<Projection> =>
  Object.freeze({
    ...state,
    appliedEvents: Object.freeze([...state.appliedEvents]),
  })

export const createReplayState = <Projection>(
  snapshot: ReplaySnapshot<Projection>
): ReplayState<Projection> =>
  freezeState({
    ...snapshot,
    seq: snapshot.snapshotSeq,
    appliedEvents: [],
  })

export const resetReplayState = <Projection>(
  _state: ReplayState<Projection>,
  snapshot: ReplaySnapshot<Projection>
): ReplayState<Projection> => createReplayState(snapshot)

export const applyReplayEvent = <Projection, Data>(
  state: ReplayState<Projection>,
  incoming: {
    epoch: string
    event: RemoteControlEvent<Data>
  },
  reduce: (
    projection: Projection,
    event: RemoteControlEvent<Data>
  ) => Projection
): ReplayResult<Projection> => {
  if (incoming.epoch !== state.epoch) {
    return {
      status: 'reset-required',
      state,
      expectedEpoch: state.epoch,
      receivedEpoch: incoming.epoch,
    }
  }

  const { event } = incoming

  const identityAtSequence = state.appliedEvents.find(
    (identity) => identity.seq === event.seq
  )

  const identityForEvent = state.appliedEvents.find(
    (identity) => identity.eventId === event.eventId
  )

  if (event.seq <= state.seq) {
    const isKnownDuplicate =
      identityAtSequence?.eventId === event.eventId &&
      identityForEvent?.seq === event.seq

    const isCoveredBySnapshot =
      event.seq <= state.snapshotSeq &&
      identityAtSequence === undefined &&
      identityForEvent === undefined

    if (isKnownDuplicate || isCoveredBySnapshot) {
      return { status: 'duplicate', state }
    }

    return { status: 'conflict', state, seq: event.seq }
  }

  if (identityForEvent) {
    return { status: 'conflict', state, seq: event.seq }
  }

  const expectedSeq = state.seq + 1

  if (event.seq !== expectedSeq || event.prevSeq !== state.seq) {
    return {
      status: 'gap',
      state,
      expectedSeq,
      receivedSeq: event.seq,
    }
  }

  return {
    status: 'applied',
    state: freezeState({
      ...state,
      seq: event.seq,
      projection: reduce(state.projection, event),
      appliedEvents: [
        ...state.appliedEvents,
        { eventId: event.eventId, seq: event.seq },
      ].slice(-MAX_REPLAY_IDENTITIES),
    }),
  }
}
