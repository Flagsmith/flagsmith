import React, { FC } from 'react'
import classNames from 'classnames'

type ColorSwatchSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl'
type ColorSwatchShape = 'square' | 'rounded' | 'circle'

type ColorSwatchProps = {
  color?: string
  size?: ColorSwatchSize
  shape?: ColorSwatchShape
  className?: string
}

/* eslint-disable sort-keys-fix/sort-keys-fix -- a scale reads in size order */
const SIZE_MAP: Record<ColorSwatchSize, number> = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 32,
  '2xl': 44,
}
/* eslint-enable sort-keys-fix/sort-keys-fix */

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
