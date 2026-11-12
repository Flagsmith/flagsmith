import Color from 'color'

// Not tokens: the Projects and Organisations pages colour tiles from this list.
export const PROJECT_PALETTE = [
  '#906AF6',
  '#FAE392',
  '#42D0EB',
  '#56CCAD',
  '#FFBE71',
  '#F57C78',
]

// Skips the last colour. Kept as is, since fixing it would recolour every
// existing tile.
export const getProjectColour = (index: number) =>
  PROJECT_PALETTE[index % (PROJECT_PALETTE.length - 1)]

// Pass projects sorted by name, as the Projects page lists them.
export const getProjectColourMap = (projects: { id: number }[]) =>
  new Map(
    projects.map((project, index) => [project.id, getProjectColour(index)]),
  )

type ContrastColour = 'black' | 'white'

export const getContrastColour = (
  backgroundColor: string | null | undefined,
): ContrastColour => {
  if (!backgroundColor) return 'white'
  try {
    return Color(backgroundColor).luminosity() > 0.179 ? 'black' : 'white'
  } catch {
    return 'white'
  }
}
