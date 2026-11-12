import { FC, TableHTMLAttributes } from 'react'
import cn from 'classnames'
import './Table.scss'

export type TableVariant = 'surface' | 'ghost'

export type TableLayout = 'auto' | 'fixed'

export type TableProps = TableHTMLAttributes<HTMLTableElement> & {
  variant?: TableVariant
  layout?: TableLayout
  highlightRowOnHover?: boolean
}

// Composed from its parts rather than configured: no columns or rows prop,
// because cells hold toggles, buttons and tooltips.
const Table: FC<TableProps> = ({
  children,
  className,
  highlightRowOnHover,
  layout = 'auto',
  variant = 'surface',
  ...rest
}) => (
  <table
    {...rest}
    className={cn(
      'ds-table w-100',
      `ds-table--${variant}`,
      `ds-table--${layout}`,
      { 'ds-table--hover': highlightRowOnHover },
      // The surface variant clips its rows to its own corners.
      { 'overflow-hidden rounded-lg': variant === 'surface' },
      className,
    )}
  >
    {children}
  </table>
)

export default Table
