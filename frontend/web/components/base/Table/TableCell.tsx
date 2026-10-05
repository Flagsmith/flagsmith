import { FC, TdHTMLAttributes } from 'react'

const TableCell: FC<TdHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  ...rest
}) => <td {...rest}>{children}</td>

export default TableCell
