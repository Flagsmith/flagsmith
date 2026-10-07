import { Tag as TTag } from 'common/types/responses'
import { getTagSwatchUtilities } from './tagSwatch'
import { SYSTEM_TAG_UTILITIES, isSystemTag } from './systemTag'

// Numeric-entity everything that is not alphanumeric or beyond Latin-1.
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
 * A tag chip as markup, for the tooltips that go through innerHTML and so
 * cannot render a component. Same classes as the real chip, so there is one
 * set of colour rules.
 */
export const tagChipHtml = (
  tag: Partial<TTag>,
  { className = '', disabled = false }: TagChipOptions = {},
): string => {
  const utilities = isSystemTag(tag)
    ? SYSTEM_TAG_UTILITIES
    : getTagSwatchUtilities(tag.color)
  const classes = [
    'ds-chip ds-chip--xs d-inline-flex align-items-center rounded-md',
    utilities,
    disabled ? 'opacity-50' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')
  return `<span class="${classes}">${escapeHTML(tag.label ?? '')}</span>`
}
