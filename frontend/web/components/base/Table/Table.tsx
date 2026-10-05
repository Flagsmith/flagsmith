import { FC, TableHTMLAttributes } from 'react'
import cn from 'classnames'
import './Table.scss'

export type TableVariant = 'surface' | 'ghost'

export type TableLayout = 'auto' | 'fixed'

export type TableProps = TableHTMLAttributes<HTMLTableElement> & {
  variant?: TableVariant
  layout?: TableLayout
  // Rows take a hover fill, for tracking one across its columns. A clickable
  // row needs .cursor-pointer as well.
  hover?: boolean
}

// Composed from its parts rather than configured: no columns or rows prop,
// because cells hold toggles, buttons and tooltips.
const Table: FC<TableProps> = ({
  children,
  className,
  hover,
  layout = 'auto',
  variant = 'surface',
  ...rest
}) => (
  <table
    {...rest}
    className={cn(
      'ds-table',
      `ds-table--${variant}`,
      `ds-table--${layout}`,
      { 'ds-table--hover': hover },
      className,
    )}
  >
    {children}
  </table>
)

export default Table
