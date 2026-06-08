import React, { FC, useEffect } from 'react'
import Icon from 'components/icons/Icon'
import {
  CONCEPT_ITEMS,
  ConceptItemId,
} from 'web/components/pages/onboarding-quickstart/data/presets'
import './ConceptDrawer.scss'

type ConceptDrawerProps = {
  activeId: ConceptItemId | null
  completedIds: ConceptItemId[]
  isOpen: boolean
  onClose: () => void
  onItemClick: (id: ConceptItemId) => void
}

const ConceptDrawer: FC<ConceptDrawerProps> = ({
  activeId,
  completedIds,
  isOpen,
  onClose,
  onItemClick,
}) => {
  useEffect(() => {
    if (!isOpen) return
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isOpen, onClose])

  const completedCount = completedIds.length
  const totalCount = CONCEPT_ITEMS.length

  return (
    <>
      <div
        className={`concept-drawer__backdrop ${
          isOpen ? 'concept-drawer__backdrop--open' : ''
        }`}
        onClick={onClose}
        aria-hidden='true'
      />
      <aside
        className={`concept-drawer bg-surface-default border-default shadow-lg ${
          isOpen ? 'concept-drawer--open' : ''
        }`}
        role='dialog'
        aria-label='Get started'
        aria-hidden={!isOpen}
      >
        <header className='concept-drawer__header d-flex align-items-center justify-content-between p-3 border-bottom border-default'>
          <h3 className='mb-0'>Get started</h3>
          <button
            type='button'
            className='btn btn-link p-0 text-muted'
            onClick={onClose}
            aria-label='Close'
          >
            <Icon name='close' width={20} />
          </button>
        </header>

        <div className='concept-drawer__progress px-3 pt-3'>
          <div className='d-flex align-items-center justify-content-between mb-2'>
            <span className='text-muted'>Progress</span>
            <span className='text-muted'>
              {completedCount}/{totalCount}
            </span>
          </div>
          <div className='concept-drawer__bar bg-surface-muted rounded-full'>
            <div
              className='concept-drawer__bar-fill bg-surface-action rounded-full'
              style={
                {
                  // CSS custom property used for width so we keep styling
                  // out of inline style declarations elsewhere.
                  '--concept-drawer-progress': `${
                    (completedCount / totalCount) * 100
                  }%`,
                } as React.CSSProperties
              }
            />
          </div>
        </div>

        <ul className='concept-drawer__items list-unstyled m-0 p-3 d-flex flex-column gap-2'>
          {CONCEPT_ITEMS.map((item) => {
            const isCompleted = completedIds.includes(item.id)
            const isActive = activeId === item.id && !isCompleted
            return (
              <li key={item.id}>
                <button
                  type='button'
                  onClick={() => onItemClick(item.id)}
                  className={`concept-drawer__item w-100 text-start p-3 rounded-md border ${
                    isActive
                      ? 'concept-drawer__item--active border-action bg-surface-action-subtle'
                      : 'border-default bg-surface-default'
                  }`}
                  disabled={isCompleted}
                >
                  <div className='d-flex align-items-start gap-2'>
                    <span
                      className={`concept-drawer__marker ${
                        isCompleted
                          ? 'concept-drawer__marker--done icon-success'
                          : ''
                      }`}
                      aria-hidden='true'
                    >
                      {isCompleted ? (
                        <Icon name='checkmark' width={18} />
                      ) : (
                        <span className='concept-drawer__marker-empty' />
                      )}
                    </span>
                    <span className='flex-1'>
                      <span
                        className={`d-block fw-semibold ${
                          isCompleted ? 'text-muted' : 'text-default'
                        }`}
                      >
                        {item.title}
                      </span>
                      <span className='d-block text-muted'>
                        {item.description}
                      </span>
                    </span>
                  </div>
                </button>
              </li>
            )
          })}
        </ul>
      </aside>
    </>
  )
}

export default ConceptDrawer
