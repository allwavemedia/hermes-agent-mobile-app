import { describe, expect, it } from 'vitest'

import cases from '../fixtures/v1/validation-cases.json'

interface ValidationModule {
  validateRemoteControlDocument(
    schema: string,
    value: unknown
  ): { valid: boolean }
}

const loadValidationModule = async (): Promise<ValidationModule | undefined> => {
  const modulePath = './validate.js'

  try {
    return (await import(/* @vite-ignore */ modulePath)) as ValidationModule
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

describe('remote-control v1 schema validation', () => {
  it.each(cases)('$name', async ({ expected, schema, value }) => {
    const validationModule = await loadValidationModule()

    expect(
      validationModule,
      'the framework-neutral protocol validator must exist'
    ).toBeDefined()

    if (validationModule) {
      expect(validationModule.validateRemoteControlDocument(schema, value).valid).toBe(
        expected
      )
    }
  })
})
