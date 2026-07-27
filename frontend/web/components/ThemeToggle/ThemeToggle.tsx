import React, { useState } from 'react'
import cn from 'classnames'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import InlineModal from 'components/InlineModal'
import { ThemeSetting, useTheme } from 'project/darkMode'

const THEME_OPTIONS: { label: string; value: ThemeSetting }[] = [
  { label: 'Light', value: 'light' },
  { label: 'Dark', value: 'dark' },
  { label: 'System', value: 'system' },
]

// Always-visible theme control: an icon button showing the resolved theme,
// opening a Light / Dark / System menu. The icon set has no "system" glyph,
// which is why this is a labelled menu rather than a three-state cycle.
const ThemeToggle = () => {
  const [isOpen, setIsOpen] = useState(false)
  const { isDark, setThemeSetting, setting } = useTheme()

  return (
    <div className='position-relative'>
      <Button
        theme='icon'
        onClick={() => setIsOpen(!isOpen)}
        aria-label='Change theme'
        aria-haspopup='menu'
        aria-expanded={isOpen}
      >
        <Icon name={isDark ? 'moon' : 'sun'} width={18} />
      </Button>
      <InlineModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        hideClose
        relativeToParent
        className='inline-modal--sm right mt-1'
      >
        <div role='menu' className='d-flex flex-column'>
          {THEME_OPTIONS.map((option) => (
            <Button
              key={option.value}
              role='menuitemradio'
              aria-checked={setting === option.value}
              theme='text'
              className={cn(
                'text-start px-2 py-1',
                setting === option.value && 'font-weight-medium',
              )}
              onClick={() => {
                setThemeSetting(option.value)
                setIsOpen(false)
              }}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </InlineModal>
    </div>
  )
}

export default ThemeToggle
