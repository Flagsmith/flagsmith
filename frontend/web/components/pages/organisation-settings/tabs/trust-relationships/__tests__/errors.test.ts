import {
  trustRelationshipAlertError,
  trustRelationshipErrorMessage,
  trustRelationshipFieldErrors,
} from 'components/pages/organisation-settings/tabs/trust-relationships/errors'

const FALLBACK = 'Could not save trust relationship'
// What a proxy or a misrouted request returns instead of a DRF body.
const HTML_BODY =
  '<!DOCTYPE html><html><body><h1>404 Not Found</h1></body></html>'

describe('trustRelationshipErrorMessage', () => {
  it.each`
    body                                        | expected
    ${{ detail: 'Nope' }}                       | ${'Nope'}
    ${{ non_field_errors: ['Already exists'] }} | ${'Already exists'}
    ${{ issuer: ['Enter a valid URL.'] }}       | ${'Enter a valid URL.'}
    ${HTML_BODY}                                | ${FALLBACK}
    ${undefined}                                | ${FALLBACK}
    ${{}}                                       | ${FALLBACK}
  `('returns $expected for $body', ({ body, expected }) => {
    // Given / When / Then
    expect(trustRelationshipErrorMessage({ data: body }, FALLBACK)).toBe(
      expected,
    )
  })
})

describe('trustRelationshipFieldErrors', () => {
  it('keys the first message per field', () => {
    // Given
    const error = {
      data: {
        detail: 'Something else',
        issuer: ['Enter a valid URL.'],
        name: 'Already taken',
      },
    }

    // When / Then
    expect(trustRelationshipFieldErrors(error)).toEqual({
      issuer: 'Enter a valid URL.',
      name: 'Already taken',
    })
  })

  it('returns nothing for a body that is not a field map', () => {
    // Given / When / Then
    expect(trustRelationshipFieldErrors({ data: HTML_BODY })).toEqual({})
  })
})

describe('trustRelationshipAlertError', () => {
  it('returns null when every message renders on a field', () => {
    // Given / When / Then
    expect(
      trustRelationshipAlertError({ data: { name: ['Taken'] } }, FALLBACK),
    ).toBeNull()
  })

  it('carries the messages that have no field of their own', () => {
    // Given
    const error = {
      data: { claim_rules: ['Duplicate claim.'], name: ['Taken'] },
    }

    // When / Then
    expect(trustRelationshipAlertError(error, FALLBACK)).toBe(
      'Duplicate claim.',
    )
  })

  it('falls back rather than rendering a body it cannot read', () => {
    // Given / When / Then
    expect(trustRelationshipAlertError({ data: HTML_BODY }, FALLBACK)).toBe(
      FALLBACK,
    )
  })

  it('returns null without an error', () => {
    // Given / When / Then
    expect(trustRelationshipAlertError(undefined, FALLBACK)).toBeNull()
  })
})
