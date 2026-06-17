import React, { FC, KeyboardEvent, useRef, useState } from 'react'
import Icon from 'components/icons/Icon'
import Chip from 'components/base/Chip'
import { colorIconSecondary } from 'common/theme/tokens'
import { SDK_LANGS, SdkLang } from './sdkLangs'

export type SdkPickerProps = {
  selected: SdkLang
  onSelect: (lang: SdkLang) => void
}

// The language / framework picker: popular SDKs as quick-pick chips, the long
// tail behind "More". A single-select radiogroup — one tab stop, with
// Arrow/Home/End moving focus and selection across the visible options
// (selection follows focus). "More" is a separate disclosure button, not an
// option, so it stays outside the group.
const SdkPicker: FC<SdkPickerProps> = ({ onSelect, selected }) => {
  const [moreOpen, setMoreOpen] = useState(false)
  const optionRefs = useRef<(HTMLSpanElement | null)[]>([])

  const popularLangs = SDK_LANGS.filter((l) => l.popular)
  const moreLangs = SDK_LANGS.filter((l) => !l.popular)
  const options = moreOpen ? [...popularLangs, ...moreLangs] : popularLangs

  // The selected option is the single tab stop; if it's hidden (selected a
  // "More" SDK then collapsed), fall back to the first so the group stays
  // reachable.
  const selectedIndex = options.findIndex((l) => l.label === selected.label)
  const tabStopIndex = selectedIndex === -1 ? 0 : selectedIndex

  const onKeyDown = (e: KeyboardEvent, index: number) => {
    const last = options.length - 1
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
    onSelect(options[next])
    optionRefs.current[next]?.focus()
  }

  const renderOption = (lang: SdkLang, index: number) => {
    const Logo = lang.logo
    const isSelected = selected.label === lang.label
    return (
      <Chip
        key={lang.label}
        ref={(el) => {
          optionRefs.current[index] = el
        }}
        role='radio'
        aria-checked={isSelected}
        tabIndex={index === tabStopIndex ? 0 : -1}
        variant={isSelected ? 'accent' : 'neutral'}
        onClick={() => onSelect(lang)}
        onKeyDown={(e) => onKeyDown(e, index)}
      >
        <Logo />
        {lang.label}
      </Chip>
    )
  }

  // Column layout: the radiogroup wraps on top, the More/Less toggle sits on
  // its own line beneath it — so the toggle keeps a stable position instead of
  // trailing the chips and jumping when the long tail expands.
  return (
    <div className='d-flex flex-column align-items-start gap-2'>
      <div
        role='radiogroup'
        aria-label='SDK'
        className='d-flex flex-wrap align-items-center gap-2'
      >
        {options.map(renderOption)}
      </div>
      <Chip onClick={() => setMoreOpen((open) => !open)}>
        {moreOpen ? 'Less' : 'More'}
        <Icon
          name={moreOpen ? 'chevron-up' : 'chevron-down'}
          width={14}
          fill={colorIconSecondary}
          aria-hidden
        />
      </Chip>
    </div>
  )
}

export default SdkPicker
