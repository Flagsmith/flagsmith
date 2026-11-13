import React, { FC, ReactNode } from 'react'
import classNames from 'classnames'

export type ColorSwatchSize = 'sm' | 'md' | 'lg' | 'xl'
type ColorSwatchShape = 'square' | 'circle'

type ColorSwatchProps = {
  color: string
  size?: ColorSwatchSize
  shape?: ColorSwatchShape
  className?: string
  // Centred inside, e.g. an initial.
  children?: ReactNode
}

const SIZE_MAP: Record<ColorSwatchSize, number> = {
  lg: 16,
  md: 12,
  sm: 8,
  xl: 24,
}

const getShapeClass = (shape: ColorSwatchShape, size: ColorSwatchSize) => {
  if (shape === 'circle') return 'rounded-circle'
  return size === 'xl' ? 'rounded-md' : 'rounded-xs'
}

const ColorSwatch: FC<ColorSwatchProps> = ({
  children,
  className,
  color,
  shape = 'square',
  size = 'md',
}) => (
  <span
    aria-hidden='true'
    className={classNames(
      'flex-shrink-0',
      children
        ? 'd-inline-flex align-items-center justify-content-center'
        : 'd-inline-block',
      getShapeClass(shape, size),
      className,
    )}
    style={{
      backgroundColor: color,
      height: SIZE_MAP[size],
      width: SIZE_MAP[size],
    }}
  >
    {children}
  </span>
)

ColorSwatch.displayName = 'ColorSwatch'
export default ColorSwatch
