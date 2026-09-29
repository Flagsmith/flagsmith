import React, { FC } from 'react'
import classNames from 'classnames'

type ColorSwatchSize = 'sm' | 'md' | 'lg' | 'xl'
type ColorSwatchShape = 'square' | 'rounded' | 'circle'

type ColorSwatchProps = {
  // Optional, so a utility class can carry the fill and it comes from a token
  // rather than an inline hex.
  color?: string
  size?: ColorSwatchSize
  shape?: ColorSwatchShape
  className?: string
}

const SIZE_MAP: Record<ColorSwatchSize, number> = {
  lg: 16,
  md: 12,
  sm: 8,
  // Big enough to pick from, as in the tag colour picker.
  xl: 44,
}

const SHAPE_CLASS: Record<ColorSwatchShape, string> = {
  circle: 'rounded-circle',
  rounded: 'rounded-lg',
  square: 'rounded-xs',
}

const ColorSwatch: FC<ColorSwatchProps> = ({
  className,
  color,
  shape = 'square',
  size = 'md',
}) => (
  <span
    aria-hidden='true'
    className={classNames(
      'd-inline-block flex-shrink-0',
      SHAPE_CLASS[shape],
      className,
    )}
    style={{
      backgroundColor: color,
      height: SIZE_MAP[size],
      width: SIZE_MAP[size],
    }}
  />
)

ColorSwatch.displayName = 'ColorSwatch'
export default ColorSwatch
