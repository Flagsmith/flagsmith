import {
  getContrastColour,
  getProjectColourMap,
  getProjectColour,
  PROJECT_PALETTE,
} from 'common/utils/paletteColour'

describe('getProjectColour', () => {
  it('picks by position', () => {
    expect(getProjectColour(0)).toBe(PROJECT_PALETTE[0])
    expect(getProjectColour(1)).toBe(PROJECT_PALETTE[1])
  })

  it('wraps before the last colour', () => {
    expect(getProjectColour(PROJECT_PALETTE.length - 1)).toBe(
      PROJECT_PALETTE[0],
    )
  })
})

describe('getContrastColour', () => {
  it.each([
    ['#FAE392', 'black'],
    ['#1A2634', 'white'],
    ['#000000', 'white'],
    ['#FFFFFF', 'black'],
    ['not a colour', 'white'],
    [null, 'white'],
    [undefined, 'white'],
  ])('%s needs %s text', (background, expected) => {
    expect(getContrastColour(background)).toBe(expected)
  })
})

describe('getProjectColourMap', () => {
  it('colours each project by its position in the list', () => {
    const colours = getProjectColourMap([{ id: 30 }, { id: 10 }, { id: 20 }])
    expect(colours.get(30)).toBe(PROJECT_PALETTE[0])
    expect(colours.get(10)).toBe(PROJECT_PALETTE[1])
    expect(colours.get(20)).toBe(PROJECT_PALETTE[2])
  })

  it('has no colour for an unknown project', () => {
    expect(getProjectColourMap([{ id: 1 }]).get(2)).toBeUndefined()
  })
})
