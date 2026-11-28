import { configuredActionsLabel } from 'components/integrations/configuredActionsLabel'

describe('configuredActionsLabel', () => {
  it.each`
    title        | index | count | expected
    ${'Grafana'} | ${0}  | ${1}  | ${'Actions for Grafana'}
    ${'Grafana'} | ${1}  | ${3}  | ${'Actions for Grafana, 2 of 3'}
    ${undefined} | ${0}  | ${1}  | ${'Actions for integration'}
    ${undefined} | ${0}  | ${2}  | ${'Actions for integration, 1 of 2'}
  `(
    '$title, $index of $count: $expected',
    ({ count, expected, index, title }) => {
      expect(configuredActionsLabel(title, index, count)).toBe(expected)
    },
  )
})
