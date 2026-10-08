import type { ContentColour } from 'common/theme/tokens'

export type ChipVariant = 'neutral' | 'accent' | 'outline'

const VARIANT_UTILITIES: Record<ChipVariant, string> = {
  accent: 'bg-surface-action-subtle text-action',

  neutral: 'bg-surface-subtle text-default',
  // No fill: the border carries the edge, so the chip takes no surface.
  outline: 'text-default',
}

export const chipVariantClass = (variant: ChipVariant = 'neutral') =>
  VARIANT_UTILITIES[variant]

export const chipDotClass = (colour: ContentColour) => `tag-dot-${colour}`

// Surface and dot as one value, so a caller that cannot pass props (markup
// built for innerHTML) resolves them the same way the component does.
export type ChipColourChoice = {
  variant?: ChipVariant
  dot?: ContentColour
}

export const chipColourUtilities = ({ variant }: ChipColourChoice) =>
  chipVariantClass(variant)
