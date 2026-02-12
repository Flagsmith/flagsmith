import React, { useLayoutEffect, useRef, useState } from 'react'
import Icon from 'components/Icon'
import classNames from 'classnames'
import useOutsideClick from 'common/useOutsideClick'
import { createPortal } from 'react-dom'
import { calculateListPosition } from 'common/utils/calculateListPosition'
import { useHistory } from 'react-router-dom'
import { getViewMode, setViewMode, ViewMode } from 'common/useViewMode'
import AccountStore from 'common/stores/account-store'

const AccountDropdown: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [currentViewMode, setCurrentViewMode] = useState<ViewMode>(
    getViewMode(),
  )
  const btnRef = useRef<HTMLButtonElement>(null)
  const dropDownRef = useRef<HTMLDivElement>(null)
  const history = useHistory()
  
  useOutsideClick(dropDownRef, () => setIsOpen(false))

  useLayoutEffect(() => {
    if (!isOpen || !dropDownRef.current || !btnRef.current) return
    const listPosition = calculateListPosition(
      btnRef.current,
      dropDownRef.current,
    )
    dropDownRef.current.style.top = `${listPosition.top}px`
    dropDownRef.current.style.left = `${listPosition.left}px`
  }, [btnRef, isOpen, dropDownRef])

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode)
    setCurrentViewMode(mode)

    // Navigate to the appropriate page based on view mode
    const organisationId = AccountStore.getOrganisation()?.id
    if (organisationId) {
      if (mode === 'release-manager') {
        history.push(`/organisation/${organisationId}/release-manager`)
      } else if (mode === 'executive') {
        history.push(`/organisation/${organisationId}/executive-view`)
      } else if (mode === 'dev') {
        history.push(`/organisation/${organisationId}/dev-view`)
      }
    }

    setIsOpen(false)
  }

  const handleAccountSettings = () => {
    history.push('/account')
    setIsOpen(false)
  }

  return (
    <div className='feature-action' tabIndex={-1}>
      <button
        className='btn btn-link p-0 d-flex ps-3 lh-1 align-items-center'
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen(!isOpen)
        }}
        ref={btnRef}
        id='account-settings-link'
        data-test='account-settings-link'
      >
        <span className='mr-1'>
          <Icon name='person' width={20} fill='#9DA4AE' />
        </span>
        <span className='d-none d-md-block'>Account</span>
      </button>

      {isOpen &&
        createPortal(
          <div ref={dropDownRef} className='feature-action__list'>
            <div
              className='feature-action__item feature-action__header'
              style={{
                color: '#656D7B',
                cursor: 'default',
                fontSize: '12px',
                fontWeight: 600,
                padding: '8px 16px',
              }}
              id={'account-settings-view-mode'}
            >
              View Mode
            </div>
            <div
              className={classNames('feature-action__item', {
                'feature-action__item--selected':
                  currentViewMode === 'release-manager',
              })}
              onClick={() => handleViewModeChange('release-manager')}
            >
              <Icon name='rocket' width={18} fill='#9DA4AE' />
              Release Manager
            </div>
            <div
              className={classNames('feature-action__item', {
                'feature-action__item--selected':
                  currentViewMode === 'executive',
              })}
              onClick={() => handleViewModeChange('executive')}
            >
              <Icon name='bar-chart' width={18} fill='#9DA4AE' />
              Executive View
            </div>
            <div
              className={classNames('feature-action__item', {
                'feature-action__item--selected': currentViewMode === 'dev',
              })}
              onClick={() => handleViewModeChange('dev')}
            >
              <Icon name='code' width={18} fill='#9DA4AE' />
              Dev View
            </div>
            <div
              className='feature-action__divider'
              style={{
                borderTop: '1px solid #E8EAED',
                margin: '4px 0',
              }}
            />
            <div
              className='feature-action__item'
              onClick={handleAccountSettings}
              id='account-settings'
            >
              <Icon name='setting' width={18} fill='#9DA4AE' />
              Account Settings
            </div>
          </div>,
          document.body,
        )}
    </div>
  )
}

export default AccountDropdown
