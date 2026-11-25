import { FC } from 'react'
import { IconProps } from './types'

const SettingsIcon: FC<IconProps> = ({
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
      d='M9.08156 20H14.9184C16.0485 20 17.0927 19.4131 17.6578 18.4604L20.5762 13.5396C21.1413 12.5869 21.1413 11.4131 20.5762 10.4604L17.6578 5.5396C17.0927 4.58689 16.0485 4 14.9184 4L9.08156 4C7.95149 4 6.90726 4.58689 6.34222 5.5396L3.42378 10.4604C2.85874 11.4131 2.85874 12.5869 3.42378 13.5396L6.34222 18.4604C6.90726 19.4131 7.95149 20 9.08156 20Z'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <circle
      cx='12'
      cy='12'
      r='3'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
  </svg>
)

export default SettingsIcon
