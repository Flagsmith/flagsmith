import { orgNameFromEmail } from 'components/pages/onboarding/hooks/useSmartDefaults'

describe('orgNameFromEmail', () => {
  it.each`
    email                    | firstName  | expected
    ${'alice@acme.com'}      | ${'Alice'} | ${'Acme'}
    ${'alice@acme-corp.com'} | ${'Alice'} | ${'Acme Corp'}
    ${'alice@flagsmith.com'} | ${'Bob'}   | ${'Flagsmith'}
    ${'alice@gmail.com'}     | ${'Alice'} | ${"Alice's Org"}
    ${'alice@gmail.com'}     | ${''}      | ${''}
    ${''}                    | ${'Alice'} | ${"Alice's Org"}
    ${'notanemail'}          | ${'Alice'} | ${"Alice's Org"}
    ${''}                    | ${''}      | ${''}
  `(
    'orgNameFromEmail($email, $firstName) returns $expected',
    ({ email, expected, firstName }) => {
      expect(orgNameFromEmail(email, firstName)).toBe(expected)
    },
  )
})
