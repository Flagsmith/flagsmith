import { FC, HTMLAttributes } from 'react'

const TableHeader: FC<HTMLAttributes<HTMLTableSectionElement>> = ({
  children,
  ...rest
}) => <thead {...rest}>{children}</thead>

export default TableHeader
