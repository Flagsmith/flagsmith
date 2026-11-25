import { FC } from 'react'
import { IconProps } from './types'

const ArrowLeftIcon: FC<IconProps> = ({
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
      d='M16.1719 12H6.17188M10.1719 7L7.43462 9.73726C6.64258 10.5293 6.24657 10.9253 6.09819 11.382C5.96767 11.7837 5.96767 12.2163 6.09819 12.618C6.24657 13.0747 6.64258 13.4707 7.43462 14.2627L10.1719 17'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
  </svg>
)

export default ArrowLeftIcon
