import { FC, HTMLAttributes } from 'react'

const TableBody: FC<HTMLAttributes<HTMLTableSectionElement>> = ({
  children,
  ...rest
}) => <tbody {...rest}>{children}</tbody>

export default TableBody
