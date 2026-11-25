import { FC } from 'react'
import { IconProps } from './types'

const DotsIcon: FC<IconProps> = ({
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
    <circle cx='12' cy='5' r='2' fill={fill} />
    <circle cx='12' cy='12' r='2' fill={fill} />
    <circle cx='12' cy='19' r='2' fill={fill} />
  </svg>
)

export default DotsIcon
