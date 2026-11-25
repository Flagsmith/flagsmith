import { FC } from 'react'
import { IconProps } from './types'

const PieChartIcon: FC<IconProps> = ({
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
      d='M18.8612 16.75C18.2093 17.8791 17.3064 18.8431 16.2223 19.5675C15.1383 20.2918 13.9021 20.7571 12.6095 20.9273C11.3168 21.0975 10.0024 20.968 8.76777 20.5489C7.53316 20.1298 6.41152 19.4323 5.48959 18.5104C4.56767 17.5885 3.87019 16.4668 3.45109 15.2322C3.032 13.9976 2.90254 12.6832 3.07272 11.3905C3.2429 10.0979 3.70816 8.86172 4.43251 7.77765C5.15686 6.69359 6.12088 5.79068 7.25 5.13878M10.3 3.28963C11.7413 2.90346 13.2587 2.90346 14.7 3.28963C16.1412 3.6758 17.4554 4.43455 18.5104 5.48959C19.5655 6.54464 20.3242 7.85882 20.7104 9.30004C21.0965 10.7413 21.0965 12.2587 20.7104 13.7L12.5 11.5L10.3 3.28963Z'
      strokeWidth='1.6875'
      strokeLinecap='square'
      strokeLinejoin='round'
      stroke={fill}
    />
  </svg>
)

export default PieChartIcon
