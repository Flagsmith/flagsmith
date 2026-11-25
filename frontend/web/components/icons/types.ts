import { FC, SVGProps } from 'react'

export type IconProps = Omit<SVGProps<SVGSVGElement>, 'fill'> & {
  // Colours the strokes and fills
  fill?: string
}

export type IconComponent = FC<IconProps>
