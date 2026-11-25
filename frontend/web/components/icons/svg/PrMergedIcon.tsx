import { FC } from 'react'
import { IconProps } from './types'

const PrMergedIcon: FC<IconProps> = ({
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
    <circle
      cx='6.49714'
      cy='5.49762'
      r='2.50104'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <circle
      cx='6.49714'
      cy='18.503'
      r='2.50104'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M6.49728 7.99854V16.0019'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <circle
      cx='17.501'
      cy='13.001'
      r='2.50104'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
    <path
      d='M6.49609 7.99854V7.99854C6.49609 10.7611 8.7356 13.0006 11.4982 13.0006H14.9996'
      strokeWidth='1.5'
      strokeLinecap='round'
      strokeLinejoin='round'
      stroke={fill}
    />
  </svg>
)

export default PrMergedIcon
