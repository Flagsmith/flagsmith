import React, { FC, ReactNode } from 'react'
import classNames from 'classnames'
import './DiffRow.scss'

export type DiffRowState = 'added' | 'removed' | 'unchanged'

type DiffRowProps = {
  state: DiffRowState
  children: ReactNode
  // Scroll long content rather than widening the container.
  scrollable?: boolean
  className?: string
}

const MARKERS: Record<DiffRowState, string> = {
  added: '+',
  removed: '-',
  unchanged: '',
}

const DiffRow: FC<DiffRowProps> = ({
  children,
  className,
  scrollable,
  state,
}) => (
  <div
    className={classNames(
      'diff-row d-flex align-items-center',
      `diff-row--${state}`,
      className,
      { 'overflow-auto': scrollable },
    )}
  >
    <div className='diff-row__marker d-flex align-items-center justify-content-center flex-shrink-0'>
      <pre>{MARKERS[state]}</pre>
    </div>
    <div className='diff-row__content'>{children}</div>
  </div>
)

export default DiffRow
