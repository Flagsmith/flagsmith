import { FC } from 'react'
import { IconProps } from './types'

const SunIcon: FC<IconProps> = ({
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
      d='M8 12C8 14.2091 9.79086 16 12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12Z'
      strokeWidth='1.5'
      strokeLinecap='round'
      stroke={fill}
    />
    <path d='M12 5V3' strokeWidth='1.5' strokeLinecap='round' stroke={fill} />
    <path d='M12 21V19' strokeWidth='1.5' strokeLinecap='round' stroke={fill} />
    <path
      d='M16.95 7.0502L18.3643 5.63599'
      strokeWidth='1.5'
      strokeLinecap='round'
      stroke={fill}
    />
    <path
      d='M5.63559 18.3639L7.0498 16.9497'
      strokeWidth='1.5'
      strokeLinecap='round'
      stroke={fill}
    />
    <path
      d='M7.04996 7.0502L5.63574 5.63599'
      strokeWidth='1.5'
      strokeLinecap='round'
      stroke={fill}
    />
    <path
      d='M18.3644 18.3639L16.9502 16.9497'
      strokeWidth='1.5'
      strokeLinecap='round'
      stroke={fill}
    />
    <path
      d='M19 12L21 12'
      strokeWidth='1.5'
      strokeLinecap='round'
      stroke={fill}
    />
    <path
      d='M3 12L5 12'
      strokeWidth='1.5'
      strokeLinecap='round'
      stroke={fill}
    />
  </svg>
)

export default SunIcon
