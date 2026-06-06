import React, { FC, useEffect, useLayoutEffect, useRef, useState } from 'react'
import classNames from 'classnames'
import ConfigProvider from 'common/providers/ConfigProvider'
import { calculateListPosition } from 'common/utils/calculateListPosition'
import useOutsideClick from 'common/useOutsideClick'
import InlinePillToggle from './base/forms/InlinePillToggle'
import Icon, { type IconName } from './icons/Icon'
import {
  getResolvedDarkMode,
  getThemePreference,
  listenToThemePreference,
  setThemePreference,
  type ThemePreference,
} from 'project/darkMode'
import { createPortal } from 'react-dom'

const themeOptions: {
  icon: IconName
  label: string
  value: ThemePreference
}[] = [
  { icon: 'sun', label: 'Light', value: 'light' },
  { icon: 'moon', label: 'Dark', value: 'dark' },
  { icon: 'options-2', label: 'System', value: 'system' },
]

const getThemeOption = (preference: ThemePreference) =>
  themeOptions.find((option) => option.value === preference) ?? themeOptions[0]

const getActiveThemeIcon = (
  preference: ThemePreference,
  resolvedDarkMode: boolean,
) => {
  if (preference === 'system') {
    return resolvedDarkMode ? 'moon' : 'sun'
  }

  return getThemeOption(preference).icon
}

const getThemeState = () => ({
  preference: getThemePreference(),
  resolvedDarkMode: getResolvedDarkMode(),
})

const useThemePreference = () => {
  const [themeState, setThemeState] = useState(getThemeState)

  useEffect(
    () =>
      listenToThemePreference(() => {
        setThemeState(getThemeState())
      }),
    [],
  )

  return {
    ...themeState,
    setPreference: setThemePreference,
  }
}

const DarkModeSwitch: FC = () => {
  const { preference, setPreference } = useThemePreference()

  return (
    <>
      <Row className='mb-2 align-items-center justify-content-between'>
        <h5 className='mb-0'>Theme</h5>
        <InlinePillToggle
          data-test='theme-preference-setting'
          options={themeOptions.map(({ label, value }) => ({ label, value }))}
          size='small'
          value={preference}
          onChange={setPreference}
        />
      </Row>
      <p className='fs-small lh-sm'>
        Choose a light or dark theme, or follow your system setting.
      </p>
    </>
  )
}

export const ThemeModeDropdown: FC = () => {
  const { preference, resolvedDarkMode, setPreference } = useThemePreference()
  const [isOpen, setIsOpen] = useState(false)
  const btnRef = useRef<HTMLButtonElement>(null)
  const dropDownRef = useRef<HTMLDivElement>(null)
  const activeOption = getThemeOption(preference)
  const activeIcon = getActiveThemeIcon(preference, resolvedDarkMode)

  useOutsideClick(dropDownRef as React.RefObject<HTMLElement>, () =>
    setIsOpen(false),
  )

  useLayoutEffect(() => {
    if (!isOpen || !dropDownRef.current || !btnRef.current) return
    const listPosition = calculateListPosition(
      btnRef.current,
      dropDownRef.current,
    )
    dropDownRef.current.style.top = `${listPosition.top}px`
    dropDownRef.current.style.left = `${listPosition.left}px`
  }, [isOpen])

  return (
    <div className='feature-action' tabIndex={-1}>
      <button
        aria-expanded={isOpen}
        aria-label='Theme'
        className='account-dropdown-trigger d-flex ps-3 lh-1 align-items-center text-default'
        data-test='theme-preference-trigger'
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen(!isOpen)
        }}
        ref={btnRef}
        title='Theme'
        type='button'
      >
        <span className='mr-1 icon-secondary'>
          <Icon name={activeIcon} width={18} />
        </span>
        <span className='d-none d-lg-block'>{activeOption.label}</span>
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
            >
              Theme
            </div>
            {themeOptions.map((option) => {
              const isSelected = preference === option.value
              return (
                <button
                  aria-pressed={isSelected}
                  className={classNames('feature-action__item theme-option', {
                    'feature-action__item--selected': isSelected,
                  })}
                  data-test={`theme-preference-${option.value}`}
                  key={option.value}
                  onClick={(e) => {
                    e.stopPropagation()
                    setPreference(option.value)
                    setIsOpen(false)
                  }}
                  type='button'
                >
                  <Icon name={option.icon} width={18} fill='#9DA4AE' />
                  <span>{option.label}</span>
                  {isSelected && (
                    <Icon
                      className='ms-auto'
                      name='checkmark'
                      width={16}
                      fill='#6837FC'
                    />
                  )}
                </button>
              )
            })}
          </div>,
          document.body,
        )}
    </div>
  )
}

export default ConfigProvider(DarkModeSwitch)
