import { FC } from 'react'
import { IconProps } from './types'

const TagIcon: FC<IconProps> = ({
  fill = 'currentColor',
  height,
  width = 24,
  ...rest
}) => (
  <svg
    width={width}
    height={height ?? width}
    viewBox='0 0 24 24'
    fill='none'
    xmlns='http://www.w3.org/2000/svg'
    {...rest}
  >
    <path
      d='M3 12.5V5C3 3.9 3.9 3 5 3H12.5C13 3 13.5 3.2 13.9 3.6L20.4 10.1C21.2 10.9 21.2 12.1 20.4 12.9L12.9 20.4C12.1 21.2 10.9 21.2 10.1 20.4L3.6 13.9C3.2 13.5 3 13 3 12.5Z'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <circle
      cx='8'
      cy='8'
      r='1.5'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
  </svg>
)

export default TagIcon
