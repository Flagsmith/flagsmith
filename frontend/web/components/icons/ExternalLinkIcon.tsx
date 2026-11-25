import { FC } from 'react'
import { IconProps } from './types'

const ExternalLinkIcon: FC<IconProps> = ({
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
      d='M16 3H21V8'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M14 10L21 3'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M19 14V19C19 20.105 18.105 21 17 21H5C3.895 21 3 20.105 3 19V7C3 5.895 3.895 5 5 5H10'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
  </svg>
)

export default ExternalLinkIcon
