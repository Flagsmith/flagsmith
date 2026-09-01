import React, { FC, ReactNode } from 'react'
import classNames from 'classnames'
import './DiffRow.scss'

export type DiffRowState = 'added' | 'removed' | 'unchanged'

type DiffRowProps = {
  state: DiffRowState
  children: ReactNode
  // Let long content scroll inside the row instead of widening its container.
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
    className={classNames('diff-row', `diff-row--${state}`, className, {
      'diff-row--scrollable': scrollable,
    })}
  >
    <div className='diff-row__marker'>
      <pre>{MARKERS[state]}</pre>
    </div>
    <div className='diff-row__content'>{children}</div>
  </div>
)

export default DiffRow
