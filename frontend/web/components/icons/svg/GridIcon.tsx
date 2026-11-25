import { FC } from 'react'
import { IconProps } from './types'

const GridIcon: FC<IconProps> = ({
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
      d='M4.75 3H8.25C10 3 10 3 10 4.75V8.25C10 10 10 10 8.25 10H4.75C3 10 3 10 3 8.25V4.75C3 3 3 3 4.75 3Z'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M15.75 3H19.25C21 3 21 3 21 4.75V8.25C21 10 21 10 19.25 10H15.75C14 10 14 10 14 8.25V4.75C14 3 14 3 15.75 3Z'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M4.75 14H8.25C10 14 10 14 10 15.75V19.25C10 21 10 21 8.25 21H4.75C3 21 3 21 3 19.25V15.75C3 14 3 14 4.75 14Z'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M15.75 14H19.25C21 14 21 14 21 15.75V19.25C21 21 21 21 19.25 21H15.75C14 21 14 21 14 19.25V15.75C14 14 14 14 15.75 14Z'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
  </svg>
)

export default GridIcon
