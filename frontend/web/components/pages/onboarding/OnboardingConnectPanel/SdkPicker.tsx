import React, { FC, KeyboardEvent, useRef, useState } from 'react'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import Chip from 'components/base/Chip'
import { colorIconSecondary } from 'common/theme/tokens'
import { SDK_LANGS, SdkLang } from './sdkLangs'
import './SdkPicker.scss'

export type SdkPickerProps = {
  selected: SdkLang
  onSelect: (lang: SdkLang) => void
}

// The language / framework picker: popular SDKs as quick-pick chips with a
// "More" toggle pinned at the end of the first row, and the long tail opening as
// a second row beneath - so "More" never moves and open/close happens in place.
// A single-select radiogroup with Arrow/Home/End roving across the *visible*
// chips (selection follows focus). The overflow row stays mounted for the
// open/close transition but is `inert` while collapsed, so keyboard and screen
// readers skip it.
const SdkPicker: FC<SdkPickerProps> = ({ onSelect, selected }) => {
  const [moreOpen, setMoreOpen] = useState(false)
  const refs = useRef<Record<string, HTMLSpanElement | null>>({})

  const popularLangs = SDK_LANGS.filter((l) => l.popular)
  const moreLangs = SDK_LANGS.filter((l) => !l.popular)
  const visibleLangs = moreOpen ? SDK_LANGS : popularLangs

  // Exactly one chip is the tab stop: the selected one, or the first visible if
  // the selection is hidden in the collapsed tail.
  const tabStopLabel = visibleLangs.some((l) => l.label === selected.label)
    ? selected.label
    : visibleLangs[0]?.label

  const onKeyDown = (e: KeyboardEvent, lang: SdkLang) => {
    const index = visibleLangs.findIndex((l) => l.label === lang.label)
    const last = visibleLangs.length - 1
    let next: number
    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        next = index === last ? 0 : index + 1
        break
      case 'ArrowLeft':
      case 'ArrowUp':
        next = index === 0 ? last : index - 1
        break
      case 'Home':
        next = 0
        break
      case 'End':
        next = last
        break
      default:
        return
    }
    e.preventDefault()
    const target = visibleLangs[next]
    onSelect(target)
    refs.current[target.label]?.focus()
  }

  const renderOption = (lang: SdkLang) => {
    const Logo = lang.logo
    const isSelected = selected.label === lang.label
    return (
      <Chip
        key={lang.label}
        ref={(el) => {
          refs.current[lang.label] = el
        }}
        className='font-weight-medium'
        role='radio'
        aria-checked={isSelected}
        tabIndex={lang.label === tabStopLabel ? 0 : -1}
        variant={isSelected ? 'accent' : 'neutral'}
        onClick={() => onSelect(lang)}
        onKeyDown={(e) => onKeyDown(e, lang)}
      >
        <Logo />
        {lang.label}
      </Chip>
    )
  }

  return (
    <div
      role='radiogroup'
      aria-label='SDK'
      className='sdk-picker d-flex flex-column align-items-start'
    >
      <div className='d-flex flex-wrap align-items-center gap-2'>
        {popularLangs.map(renderOption)}
        <Chip
          className='font-weight-medium'
          onClick={() => setMoreOpen((open) => !open)}
          aria-expanded={moreOpen}
        >
          {moreOpen ? 'Less' : 'More'}
          <Icon
            name={moreOpen ? 'chevron-up' : 'chevron-down'}
            width={14}
            fill={colorIconSecondary}
            aria-hidden
          />
        </Chip>
      </div>
      <div
        className={classNames('sdk-picker__overflow', {
          'sdk-picker__overflow--open': moreOpen,
        })}
        inert={!moreOpen}
      >
        <div className='d-flex flex-wrap gap-2 pt-2'>
          {moreLangs.map(renderOption)}
        </div>
      </div>
    </div>
  )
}

export default SdkPicker
