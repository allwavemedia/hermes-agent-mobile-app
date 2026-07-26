import addFormats from 'ajv-formats'
import Ajv2020, { type ErrorObject, type ValidateFunction } from 'ajv/dist/2020.js'

import capabilitySchema from '../../../docs/remote-control/schemas/v1/capability.schema.json'
import commandSchema from '../../../docs/remote-control/schemas/v1/command.schema.json'
import envelopeSchema from '../../../docs/remote-control/schemas/v1/envelope.schema.json'
import eventSchema from '../../../docs/remote-control/schemas/v1/event.schema.json'
import pairingSchema from '../../../docs/remote-control/schemas/v1/pairing.schema.json'
import snapshotSchema from '../../../docs/remote-control/schemas/v1/snapshot.schema.json'

import type {
  RemoteControlSchemaName,
  ValidationIssue,
  ValidationResult,
} from './types.js'

const ajv = new Ajv2020({
  allErrors: true,
  strict: true,
})

addFormats(ajv)

const validators: Readonly<Record<RemoteControlSchemaName, ValidateFunction>> = {
  capability: ajv.compile(capabilitySchema),
  command: ajv.compile(commandSchema),
  envelope: ajv.compile(envelopeSchema),
  event: ajv.compile(eventSchema),
  pairing: ajv.compile(pairingSchema),
  snapshot: ajv.compile(snapshotSchema),
}

const toValidationIssue = (error: ErrorObject): ValidationIssue => ({
  instancePath: error.instancePath,
  keyword: error.keyword,
  message: error.message ?? 'schema validation failed',
  schemaPath: error.schemaPath,
})

const isSchemaName = (schema: string): schema is RemoteControlSchemaName =>
  Object.hasOwn(validators, schema)

export const validateRemoteControlDocument = (
  schema: string,
  value: unknown
): ValidationResult => {
  if (!isSchemaName(schema)) {
    return {
      valid: false,
      errors: [
        {
          instancePath: '',
          keyword: 'schema',
          message: `unknown remote-control schema: ${schema}`,
          schemaPath: '',
        },
      ],
    }
  }

  const validator = validators[schema]
  const valid = validator(value)

  return {
    valid,
    errors: valid ? [] : (validator.errors ?? []).map(toValidationIssue),
  }
}
