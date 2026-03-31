// =============================================================================
// Design Tokens — AUTO-GENERATED from common/theme/tokens.json
// Do not edit manually. Run: npm run generate:tokens
// =============================================================================

export const tokens = {
  border: {
    action: 'var(--color-border-action, #6837fc)',
    danger: 'var(--color-border-danger, #ef4d56)',
    default: 'var(--color-border-default)',
    disabled: 'var(--color-border-disabled)',
    info: 'var(--color-border-info, #0aaddf)',
    strong: 'var(--color-border-strong)',
    success: 'var(--color-border-success, #27ab95)',
    warning: 'var(--color-border-warning, #ff9f43)',
  },
  icon: {
    action: 'var(--color-icon-action, #6837fc)',
    danger: 'var(--color-icon-danger, #ef4d56)',
    default: 'var(--color-icon-default, #1a2634)',
    disabled: 'var(--color-icon-disabled, #9da4ae)',
    info: 'var(--color-icon-info, #0aaddf)',
    secondary: 'var(--color-icon-secondary, #656d7b)',
    success: 'var(--color-icon-success, #27ab95)',
    warning: 'var(--color-icon-warning, #ff9f43)',
  },
  surface: {
    action: 'var(--color-surface-action, #6837fc)',
    actionActive: 'var(--color-surface-action-active, #3919b7)',
    actionHover: 'var(--color-surface-action-hover, #4e25db)',
    actionMuted: 'var(--color-surface-action-muted)',
    actionSubtle: 'var(--color-surface-action-subtle)',
    active: 'var(--color-surface-active)',
    danger: 'var(--color-surface-danger)',
    default: 'var(--color-surface-default, #ffffff)',
    emphasis: 'var(--color-surface-emphasis, #e0e3e9)',
    hover: 'var(--color-surface-hover)',
    info: 'var(--color-surface-info)',
    muted: 'var(--color-surface-muted, #eff1f4)',
    subtle: 'var(--color-surface-subtle, #fafafb)',
    success: 'var(--color-surface-success)',
    warning: 'var(--color-surface-warning)',
  },
  text: {
    action: 'var(--color-text-action, #6837fc)',
    danger: 'var(--color-text-danger, #ef4d56)',
    default: 'var(--color-text-default, #1a2634)',
    disabled: 'var(--color-text-disabled, #9da4ae)',
    info: 'var(--color-text-info, #0aaddf)',
    secondary: 'var(--color-text-secondary, #656d7b)',
    success: 'var(--color-text-success, #27ab95)',
    tertiary: 'var(--color-text-tertiary, #9da4ae)',
    warning: 'var(--color-text-warning, #ff9f43)',
  },
} as const

export type TokenEntry = {
  value: string
  description: string
}

// Radius
export const radius: Record<string, TokenEntry> = {
  '2xl': {
    description: 'Modals.',
    value: 'var(--radius-2xl, 18px)',
  },
  'full': {
    description: 'Pill shapes, avatars, circular elements.',
    value: 'var(--radius-full, 9999px)',
  },
  'lg': {
    description: 'Large cards, panels.',
    value: 'var(--radius-lg, 8px)',
  },
  'md': {
    description: 'Default component radius. Cards, dropdowns, tooltips.',
    value: 'var(--radius-md, 6px)',
  },
  'none': {
    description: 'Sharp corners. Tables, dividers.',
    value: 'var(--radius-none, 0px)',
  },
  'sm': {
    description: 'Buttons, inputs, small interactive elements.',
    value: 'var(--radius-sm, 4px)',
  },
  'xl': {
    description: 'Extra-large containers.',
    value: 'var(--radius-xl, 10px)',
  },
  'xs': {
    description: 'Barely rounded. Badges, tags.',
    value: 'var(--radius-xs, 2px)',
  },
}
// Shadow
export const shadow: Record<string, TokenEntry> = {
  'lg': {
    description:
      'Modals, drawers, slide-over panels. High elevation for overlay content.',
    value: 'var(--shadow-lg, 0px 8px 16px rgba(0, 0, 0, 0.15))',
  },
  'md': {
    description:
      'Cards, dropdowns, popovers. Default elevation for floating elements.',
    value: 'var(--shadow-md, 0px 4px 8px rgba(0, 0, 0, 0.12))',
  },
  'sm': {
    description: 'Subtle lift. Buttons on hover, input focus ring companion.',
    value: 'var(--shadow-sm, 0px 1px 2px rgba(0, 0, 0, 0.05))',
  },
  'xl': {
    description:
      'Toast notifications, command palettes. Maximum elevation for urgent content.',
    value: 'var(--shadow-xl, 0px 12px 24px rgba(0, 0, 0, 0.20))',
  },
}
// Duration
export const duration: Record<string, TokenEntry> = {
  'fast': {
    description:
      'Quick feedback. Hover states, toggle switches, checkbox ticks.',
    value: 'var(--duration-fast, 100ms)',
  },
  'normal': {
    description:
      'Standard transitions. Dropdown open, tooltip appear, tab switch.',
    value: 'var(--duration-normal, 200ms)',
  },
  'slow': {
    description:
      'Deliberate emphasis. Modal enter, drawer slide, accordion expand.',
    value: 'var(--duration-slow, 300ms)',
  },
}
// Easing
export const easing: Record<string, TokenEntry> = {
  'entrance': {
    description:
      'Elements entering the viewport. Decelerates into resting position. Modals, toasts, slide-ins.',
    value: 'var(--easing-entrance)',
  },
  'exit': {
    description:
      'Elements leaving the viewport. Accelerates out of view. Closing modals, dismissing toasts.',
    value: 'var(--easing-exit)',
  },
  'standard': {
    description:
      'Default for most transitions. Smooth deceleration. Use for elements moving within the page.',
    value: 'var(--easing-standard)',
  },
}

export type TokenCategory = keyof typeof tokens
export type TokenName<C extends TokenCategory> = keyof (typeof tokens)[C]
export type RadiusScale = keyof typeof radius
export type ShadowScale = keyof typeof shadow
