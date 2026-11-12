import { FC } from 'react'
import classNames from 'classnames'
import ColorSwatch, { ColorSwatchSize } from 'components/ColorSwatch'
import { getContrastColour } from 'common/utils/paletteColour'
import './ProjectInitial.scss'

type ProjectInitialSize = 'sm' | 'md'

const SWATCH_SIZE: Record<ProjectInitialSize, ColorSwatchSize> = {
  md: 'xl',
  sm: 'lg',
}

type ProjectInitialProps = {
  name: string
  // From getProjectColourMap, so it matches the tile on the Projects page.
  colour: string
  size?: ProjectInitialSize
}

// A small version of the Projects page tile, so a project reads the same here.
const ProjectInitial: FC<ProjectInitialProps> = ({
  colour,
  name,
  size = 'sm',
}) => (
  <ColorSwatch
    color={colour}
    size={SWATCH_SIZE[size]}
    className={classNames(
      'project-initial fs-captionXSmall fw-semibold text-uppercase',
      { 'project-initial--on-light': getContrastColour(colour) === 'black' },
    )}
  >
    {name[0]}
  </ColorSwatch>
)

export default ProjectInitial
