import { FC } from 'react'
import { IconProps } from './types'

const FeaturesIcon: FC<IconProps> = ({
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
      d='M6.5 3H17C18.933 3 20.5 4.567 20.5 6.5V6.5C20.5 8.433 18.933 10 17 10H6.5C4.567 10 3 8.433 3 6.5V6.5C3 4.567 4.567 3 6.5 3Z'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M17 21H6.5C4.567 21 3 19.433 3 17.5V17.5C3 15.567 4.567 14 6.5 14H17C18.933 14 20.5 15.567 20.5 17.5V17.5C20.5 19.433 18.933 21 17 21Z'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M16.998 17C16.722 17 16.498 17.224 16.5 17.5C16.5 17.776 16.724 18 17 18C17.276 18 17.5 17.776 17.5 17.5C17.5 17.224 17.276 17 16.998 17'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M6.49801 6C6.22201 6 5.99801 6.224 6.00001 6.5C6.00001 6.776 6.22401 7 6.50001 7C6.77601 7 7.00001 6.776 7.00001 6.5C7.00001 6.224 6.77601 6 6.49801 6'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
  </svg>
)

export default FeaturesIcon
