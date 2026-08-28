import { FC } from 'react'
import classNames from 'classnames'
import './CsvPreview.scss'

const DEFAULT_ROW_COUNT = 5

export type CsvPreviewType = {
  columns: string[]
  rows: string[][]
  selectedColumn: number | null
  rowCount?: number
}

const CsvPreview: FC<CsvPreviewType> = ({
  columns,
  rowCount = DEFAULT_ROW_COUNT,
  rows,
  selectedColumn,
}) => (
  <div>
    <div className='csv-preview__section-label fw-semibold text-secondary text-uppercase mb-2'>
      Preview (first {rowCount} rows)
    </div>
    <div className='csv-preview__table rounded-lg overflow-auto'>
      <table className='mb-0 w-100 fs-small'>
        <thead>
          <tr>
            {columns.map((column, i) => (
              <th
                key={i}
                className={classNames(
                  'fw-semibold',
                  i === selectedColumn
                    ? 'bg-surface-action-tint'
                    : 'bg-surface-muted',
                )}
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, rowCount).map((row, i) => (
            <tr key={i}>
              {columns.map((_, j) => (
                <td
                  key={j}
                  className={classNames({
                    'bg-surface-action-tint': j === selectedColumn,
                  })}
                >
                  {row[j]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
)

export default CsvPreview
