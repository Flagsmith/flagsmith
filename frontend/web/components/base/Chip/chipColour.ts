import type { ContentColour } from 'common/theme/tokens'

export type ChipVariant = 'neutral' | 'accent' | 'muted'

const VARIANT_UTILITIES: Record<ChipVariant, string> = {
  accent: 'bg-surface-action-subtle text-action',
  muted: 'bg-surface-muted text-default',
  neutral: 'bg-surface-subtle text-default',
}

export const chipVariantClass = (variant: ChipVariant = 'neutral') =>
  VARIANT_UTILITIES[variant]

export const chipColourClass = (colour: ContentColour) => `tag-${colour}`

// The two channels as one value, so a caller that cannot pass props (markup
// built for innerHTML) resolves them the same way the component does.
export type ChipColourChoice =
  | { variant: ChipVariant }
  | { colour: ContentColour }

export const chipColourUtilities = (choice: ChipColourChoice) =>
  'colour' in choice
    ? chipColourClass(choice.colour)
    : chipVariantClass(choice.variant)
