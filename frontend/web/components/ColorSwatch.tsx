import React, { FC } from 'react'
import classNames from 'classnames'

type ColorSwatchSize = 'sm' | 'md' | 'lg'
type ColorSwatchShape = 'square' | 'circle'

type ColorSwatchProps = {
  color: string
  size?: ColorSwatchSize
  shape?: ColorSwatchShape
  className?: string
}

const SIZE_MAP: Record<ColorSwatchSize, number> = {
  lg: 16,
  md: 12,
  sm: 8,
}

const SHAPE_CLASS: Record<ColorSwatchShape, string> = {
  circle: 'rounded-circle',
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
