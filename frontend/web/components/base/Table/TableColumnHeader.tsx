import { FC, ThHTMLAttributes } from 'react'
import cn from 'classnames'

// scope is what lets a screen reader read a cell with its column name.
const TableColumnHeader: FC<ThHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  className,
  scope = 'col',
  ...rest
}) => (
  <th
    {...rest}
    scope={scope}
    className={cn('text-start text-secondary font-weight-medium', className)}
  >
    {children}
  </th>
)

export default TableColumnHeader
