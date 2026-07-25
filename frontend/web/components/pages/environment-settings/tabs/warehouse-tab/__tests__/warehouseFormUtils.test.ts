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
})
