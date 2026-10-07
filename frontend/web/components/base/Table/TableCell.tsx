import { FC, TdHTMLAttributes } from 'react'
import cn from 'classnames'

const TableCell: FC<TdHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  className,
  ...rest
}) => (
  <td {...rest} className={cn('py-2 px-3 align-middle', className)}>
    {children}
  </td>
)

export default TableCell
