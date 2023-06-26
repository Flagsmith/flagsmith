import { FC } from 'react'

export type IconName = 'plus'
export type IconType = React.DetailedHTMLProps<
  React.HTMLAttributes<SVGSVGElement>,
  SVGSVGElement
> & {
  name: IconName
  width?: number
  height?: number
  fill?: string
  fill2?: string
  className?: string
}

const Icon: FC<IconType> = ({ fill, fill2, height, name, width, ...rest }) => {
  switch (name) {
    case 'plus': {
      return (
        <svg
          xmlns='http://www.w3.org/2000/svg'
          width='21'
          height='20'
          viewBox='0 0 21 20'
          fill='none'
          {...rest}
        >
          <path
            fillRule='evenodd'
            clipRule='evenodd'
            d='M16.4429 9.16658H11.4429V4.16659C11.4429 3.70575 11.0695 3.33325 10.6095 3.33325C10.1495 3.33325 9.7762 3.70575 9.7762 4.16659V9.16658H4.7762C4.3162 9.16658 3.94287 9.53909 3.94287 9.99992C3.94287 10.4608 4.3162 10.8333 4.7762 10.8333H9.7762V15.8333C9.7762 16.2941 10.1495 16.6666 10.6095 16.6666C11.0695 16.6666 11.4429 16.2941 11.4429 15.8333V10.8333H16.4429C16.9029 10.8333 17.2762 10.4608 17.2762 9.99992C17.2762 9.53909 16.9029 9.16658 16.4429 9.16658Z'
            fill={fill || 'white'}
          />
        </svg>
      )
    }
    default:
      return null
  }
}

export default Icon
