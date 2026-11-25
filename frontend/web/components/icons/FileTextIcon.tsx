import { FC } from 'react'
import { IconProps } from './types'

const FileTextIcon: FC<IconProps> = ({
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
      d='M9 10.5H13'
      strokeWidth='1.5'
      strokeLinecap='round'
      stroke={fill}
    />
    <path
      d='M9 14.5H15'
      strokeWidth='1.5'
      strokeLinecap='round'
      stroke={fill}
    />
    <path
      d='M17.7143 5.25L16.3627 3.91951C16.0178 3.58005 15.8454 3.41032 15.6449 3.28899C15.4672 3.18141 15.2738 3.10219 15.0717 3.05416C14.8437 3 14.6017 3 14.1178 3H8.8C7.11984 3 6.27976 3 5.63803 3.32698C5.07354 3.6146 4.6146 4.07354 4.32698 4.63803C4 5.27976 4 6.11984 4 7.8V16.2C4 17.8802 4 18.7202 4.32698 19.362C4.6146 19.9265 5.07354 20.3854 5.63803 20.673C6.27976 21 7.11984 21 8.8 21H15.2C16.8802 21 17.7202 21 18.362 20.673C18.9265 20.3854 19.3854 19.9265 19.673 19.362C20 18.7202 20 17.8802 20 16.2V8.84027C20 8.34579 20 8.09856 19.9436 7.86618C19.8937 7.66017 19.8113 7.46342 19.6995 7.28329C19.5734 7.0801 19.3972 6.90666 19.0449 6.55978L17.7143 5.25Z'
      strokeWidth='1.5'
      stroke={fill}
    />
    <path
      d='M15 3V7C15 7.55228 15.4477 8 16 8H20'
      strokeWidth='1.5'
      stroke={fill}
    />
  </svg>
)

export default FileTextIcon
