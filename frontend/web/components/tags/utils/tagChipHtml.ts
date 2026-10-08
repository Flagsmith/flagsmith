import { Tag as TTag } from 'common/types/responses'
// The inner module, not the component: this must stay free of the stylesheet
// import so the tag utils can be unit tested.
import {
  chipColourUtilities,
  chipDotClass,
} from 'components/base/Chip/chipColour'
import { tagChipColour } from './tagChipColour'

const escapeHTML = (unsafe: string) =>
  unsafe.replace(
    /[^0-9A-Za-z\u0100-\uFFFF]/g,
    (c) => `&#${`000${c.charCodeAt(0)}`.slice(-4)};`,
  )

type TagChipOptions = {
  className?: string
  disabled?: boolean
}

/**
 * A tag chip as markup, for tooltips that go through innerHTML and cannot take
 * a component. Same classes, so the colour rules are not written twice.
 */
export const tagChipHtml = (
  tag: Partial<TTag>,
  { className = '', disabled = false }: TagChipOptions = {},
): string => {
  const choice = tagChipColour(tag)
  const utilities = chipColourUtilities(choice)
  const classes = [
    'ds-chip ds-chip--xs d-inline-flex align-items-center gap-1 rounded-md',
    utilities,
    disabled ? 'opacity-50' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')
  const dot = choice.dot
    ? `<span class="ds-chip__dot rounded-circle ${chipDotClass(
        choice.dot,
      )}"></span>`
    : ''
  return `<span class="${classes}">${dot}${escapeHTML(tag.label ?? '')}</span>`
}
