import { toHexColour } from 'common/utils/hexColour'

describe('toHexColour', () => {
  it.each`
    value         | expected
    ${'#ea5a45'}  | ${'#ea5a45'}
    ${'ea5a45'}   | ${'#ea5a45'}
    ${' #EA5A45'} | ${'#EA5A45'}
    ${'#abc'}     | ${null}
    ${'red'}      | ${null}
    ${''}         | ${null}
    ${null}       | ${null}
  `('$value → $expected', ({ expected, value }) => {
    expect(toHexColour(value)).toBe(expected)
  })
})
