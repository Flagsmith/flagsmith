import {
  buildEventOptions,
  isUnknownEvent,
} from 'components/experiments/EventNameSelect/utils'

describe('buildEventOptions', () => {
  it.each([
    ['undefined', undefined, []],
    ['empty list', [], []],
    [
      'events',
      ['checkout_completed', 'page_view'],
      [
        { label: 'checkout_completed', value: 'checkout_completed' },
        { label: 'page_view', value: 'page_view' },
      ],
    ],
  ])('%s → options', (_, events, expected) => {
    expect(buildEventOptions(events)).toEqual(expected)
  })
})

describe('isUnknownEvent', () => {
  it.each([
    ['empty value', '', ['page_view'], false],
    ['known value', 'page_view', ['page_view'], false],
    ['unknown value', 'checkout', ['page_view'], true],
    ['no fetched list', 'checkout', undefined, false],
    ['empty fetched list', 'checkout', [], true],
  ])('%s', (_, value, events, expected) => {
    expect(isUnknownEvent(value, events)).toBe(expected)
  })
})
