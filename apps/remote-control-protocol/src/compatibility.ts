import {
  REMOTE_CONTROL_PROTOCOL_MAJOR,
  REMOTE_CONTROL_PROTOCOL_MINOR,
} from './version.js'

export interface ProtocolRange {
  major: number
  minMinor: number
  maxMinor: number
}

export type ProtocolNegotiation =
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

export const CURRENT_PROTOCOL_RANGE: Readonly<ProtocolRange> = Object.freeze({
  major: REMOTE_CONTROL_PROTOCOL_MAJOR,
  minMinor: REMOTE_CONTROL_PROTOCOL_MINOR,
  maxMinor: REMOTE_CONTROL_PROTOCOL_MINOR,
})

const isValidRange = (range: ProtocolRange): boolean =>
  Number.isSafeInteger(range.major) &&
  range.major >= 0 &&
  Number.isSafeInteger(range.minMinor) &&
  range.minMinor >= 0 &&
  Number.isSafeInteger(range.maxMinor) &&
  range.maxMinor >= range.minMinor

const unsupported = (
  reason: Exclude<ProtocolNegotiation, { supported: true }>['reason']
): ProtocolNegotiation => ({
  supported: false,
  error: 'protocol.unsupported',
  reason,
})

export const negotiateProtocol = (
  local: ProtocolRange,
  remote: ProtocolRange
): ProtocolNegotiation => {
  if (!isValidRange(local) || !isValidRange(remote)) {
    return unsupported('invalid-range')
  }

  if (local.major !== remote.major) {
    return unsupported('major-mismatch')
  }

  const lowestCommonMinor = Math.max(local.minMinor, remote.minMinor)
  const highestCommonMinor = Math.min(local.maxMinor, remote.maxMinor)

  if (highestCommonMinor < lowestCommonMinor) {
    return unsupported('minor-range-disjoint')
  }

  return {
    supported: true,
    major: local.major,
    minor: highestCommonMinor,
  }
}
