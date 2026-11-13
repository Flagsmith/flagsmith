import {
  getContrastColour,
  getEnvironmentColour,
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

describe('getEnvironmentColour', () => {
  it('picks by id and uses the whole palette', () => {
    expect(getEnvironmentColour(0)).toBe(PROJECT_PALETTE[0])
    expect(getEnvironmentColour(PROJECT_PALETTE.length - 1)).toBe(
      PROJECT_PALETTE[PROJECT_PALETTE.length - 1],
    )
    expect(getEnvironmentColour(PROJECT_PALETTE.length)).toBe(
      PROJECT_PALETTE[0],
    )
  })
})

describe('getProjectColourMap', () => {
  it('colours each project by its position when sorted by name', () => {
    const colours = getProjectColourMap([
      { id: 30, name: 'Charlie' },
      { id: 10, name: 'Alpha' },
      { id: 20, name: 'Bravo' },
    ])
    expect(colours.get(10)).toBe(PROJECT_PALETTE[0])
    expect(colours.get(20)).toBe(PROJECT_PALETTE[1])
    expect(colours.get(30)).toBe(PROJECT_PALETTE[2])
  })

  it('puts capitalised names first, as the Projects page does', () => {
    const colours = getProjectColourMap([
      { id: 1, name: 'alpha' },
      { id: 2, name: 'Bravo' },
    ])
    expect(colours.get(2)).toBe(PROJECT_PALETTE[0])
    expect(colours.get(1)).toBe(PROJECT_PALETTE[1])
  })

  it('has no colour for an unknown project', () => {
    expect(
      getProjectColourMap([{ id: 1, name: 'Alpha' }]).get(2),
    ).toBeUndefined()
  })
})
