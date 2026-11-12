import { FC, HTMLAttributes } from 'react'
import cn from 'classnames'

export type TableRowProps = HTMLAttributes<HTMLTableRowElement> & {
  // A write for this row is in flight. Anything a table does for its own
  // reasons, such as marking a row that just arrived, is the caller's class.
  pending?: boolean
}

const TableRow: FC<TableRowProps> = ({
  children,
  className,
  pending,
  ...rest
}) => (
  <tr
    {...rest}
    className={cn(className, { 'ds-table__row--pending': pending })}
  >
    {children}
  </tr>
)

export default TableRow
