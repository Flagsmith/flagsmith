import { FC, ReactNode } from 'react'
import classNames from 'classnames'
import './ScopeCard.scss'

const ScopeSection: FC<{ open: boolean; children: ReactNode }> = ({
  children,
  open,
}) => (
  <div className={classNames('scope-card__section', { open })} inert={!open}>
    <div className='scope-card__section-inner'>{children}</div>
  </div>
)

export default ScopeSection
