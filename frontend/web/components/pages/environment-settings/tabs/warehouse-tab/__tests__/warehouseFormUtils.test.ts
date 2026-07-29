import { getTestFailureWarning } from 'components/pages/environment-settings/tabs/warehouse-tab/warehouseFormUtils'

describe('getTestFailureWarning', () => {
  it.each([
    ['Authentication failed.', ': Authentication failed. You can save anyway'],
    ['Connection refused', ': Connection refused. You can save anyway'],
    ['Timed out!', ': Timed out! You can save anyway'],
    [null, '. You can save anyway'],
  ])('formats detail %p with a single sentence break', (detail, expected) => {
    expect(getTestFailureWarning(detail)).toContain(expected)
  })

  it('does not claim a failed connection when only the events table is missing', () => {
    const detail =
      'Events table not found in the configured database. Run the setup SQL to create it.'

    const warning = getTestFailureWarning(detail)

    expect(warning).not.toContain("couldn't establish a connection")
    expect(warning).toContain(detail)
    expect(warning).toContain(
      "events won't be delivered until the table exists",
    )
  })

  it('keeps the sentence boundary when the missing-table detail lacks punctuation', () => {
    expect(getTestFailureWarning('Events table not found')).toContain(
      'Events table not found. You can save anyway',
    )
  })
})
