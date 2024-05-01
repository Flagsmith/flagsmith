import { FC } from 'react'

type BreadcrumbSeparatorType = {}

const BreadcrumbSeparator: FC<BreadcrumbSeparatorType> = ({}) => {
  return <span className='text-muted'>/</span>
}

export default BreadcrumbSeparator
