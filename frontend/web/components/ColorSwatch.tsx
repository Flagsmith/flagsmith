import React, { FC } from 'react'
import classNames from 'classnames'

type ColorSwatchSize = 'sm' | 'md' | 'lg'

type ColorSwatchProps = {
  color: string
  size?: ColorSwatchSize
  className?: string
}

const SIZE_MAP: Record<ColorSwatchSize, number> = {
  lg: 16,
  md: 12,
  sm: 8,
}

const ColorSwatch: FC<ColorSwatchProps> = ({
  className,
  color,
  size = 'md',
}) => (
  <span
    aria-hidden='true'
    className={classNames('d-inline-block flex-shrink-0 rounded-xs', className)}
    style={{
      backgroundColor: color,
      height: SIZE_MAP[size],
      width: SIZE_MAP[size],
    }}
  />
)

ColorSwatch.displayName = 'ColorSwatch'
export default ColorSwatch
