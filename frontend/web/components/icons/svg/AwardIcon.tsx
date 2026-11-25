import { FC } from 'react'
import { IconProps } from './types'

const AwardIcon: FC<IconProps> = ({
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
      d='M16.2426 4.75736C18.5858 7.10051 18.5858 10.8995 16.2426 13.2426C13.8995 15.5858 10.1005 15.5858 7.75736 13.2426C5.41421 10.8995 5.41421 7.1005 7.75736 4.75736C10.1005 2.41421 13.8995 2.41421 16.2426 4.75736'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M8 13.4629V20.9999L12 18.9999L16 20.9999V13.4629'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
  </svg>
)

export default AwardIcon
