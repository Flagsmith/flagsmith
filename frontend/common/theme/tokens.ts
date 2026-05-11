// =============================================================================
// Design Tokens — AUTO-GENERATED from common/theme/tokens.json
// Do not edit manually. Run: npm run generate:tokens
// =============================================================================

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
    value:
      'var(--shadow-lg, 0px 8px 16px oklch(from var(--slate-1000) l c h / 0.15))',
  },
  'md': {
    description:
      'Cards, dropdowns, popovers. Default elevation for floating elements.',
    value:
      'var(--shadow-md, 0px 4px 8px oklch(from var(--slate-1000) l c h / 0.12))',
  },
  'sm': {
    description: 'Subtle lift. Buttons on hover, input focus ring companion.',
    value:
      'var(--shadow-sm, 0px 1px 2px oklch(from var(--slate-1000) l c h / 0.05))',
  },
  'xl': {
    description:
      'Toast notifications, command palettes. Maximum elevation for urgent content.',
    value:
      'var(--shadow-xl, 0px 12px 24px oklch(from var(--slate-1000) l c h / 0.20))',
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

// =============================================================================
// Flat token constants — semantic tokens as CSS value strings.
// Use directly in any context that accepts a CSS value:
//   <Bar fill={colorChart1} />              (recharts prop)
//   style={{ color: colorTextSecondary }}   (inline style)
//   border: `1px solid ${colorBorderDefault}` (template strings)
// var() resolves at render; theme toggle updates colours via CSS cascade.
// =============================================================================

// Border
export const colorBorderAction = 'var(--color-border-action, #6837fc)'
export const colorBorderDanger = 'var(--color-border-danger, #ef4d56)'
export const colorBorderDefault =
  'var(--color-border-default, rgba(101, 109, 123, 0.16))'
export const colorBorderDisabled =
  'var(--color-border-disabled, rgba(101, 109, 123, 0.08))'
export const colorBorderInfo = 'var(--color-border-info, #0aaddf)'
export const colorBorderStrong =
  'var(--color-border-strong, rgba(101, 109, 123, 0.24))'
export const colorBorderSuccess = 'var(--color-border-success, #27ab95)'
export const colorBorderWarning = 'var(--color-border-warning, #ff9f43)'

// Icon
export const colorIconAction = 'var(--color-icon-action, #6837fc)'
export const colorIconDanger = 'var(--color-icon-danger, #ef4d56)'
export const colorIconDefault = 'var(--color-icon-default, #1a2634)'
export const colorIconDisabled = 'var(--color-icon-disabled, #9da4ae)'
export const colorIconInfo = 'var(--color-icon-info, #0aaddf)'
export const colorIconSecondary = 'var(--color-icon-secondary, #656d7b)'
export const colorIconSuccess = 'var(--color-icon-success, #27ab95)'
export const colorIconWarning = 'var(--color-icon-warning, #ff9f43)'

// Surface
export const colorSurfaceAction = 'var(--color-surface-action, #6837fc)'
export const colorSurfaceActionActive =
  'var(--color-surface-action-active, #3919b7)'
export const colorSurfaceActionHover =
  'var(--color-surface-action-hover, #4e25db)'
export const colorSurfaceActionMuted =
  'var(--color-surface-action-muted, rgba(104, 55, 252, 0.16))'
export const colorSurfaceActionSubtle =
  'var(--color-surface-action-subtle, rgba(104, 55, 252, 0.08))'
export const colorSurfaceActive =
  'var(--color-surface-active, rgba(0, 0, 0, 0.16))'
export const colorSurfaceDanger =
  'var(--color-surface-danger, rgba(239, 77, 86, 0.08))'
export const colorSurfaceDefault = 'var(--color-surface-default, #ffffff)'
export const colorSurfaceEmphasis = 'var(--color-surface-emphasis, #e0e3e9)'
export const colorSurfaceHover =
  'var(--color-surface-hover, rgba(0, 0, 0, 0.08))'
export const colorSurfaceInfo =
  'var(--color-surface-info, rgba(10, 173, 223, 0.08))'
export const colorSurfaceMuted = 'var(--color-surface-muted, #eff1f4)'
export const colorSurfaceSubtle = 'var(--color-surface-subtle, #fafafb)'
export const colorSurfaceSuccess =
  'var(--color-surface-success, rgba(39, 171, 149, 0.08))'
export const colorSurfaceWarning =
  'var(--color-surface-warning, rgba(255, 159, 67, 0.08))'

// Text
export const colorTextAction = 'var(--color-text-action, #6837fc)'
export const colorTextDanger = 'var(--color-text-danger, #ef4d56)'
export const colorTextDefault = 'var(--color-text-default, #1a2634)'
export const colorTextDisabled = 'var(--color-text-disabled, #9da4ae)'
export const colorTextInfo = 'var(--color-text-info, #0aaddf)'
export const colorTextSecondary = 'var(--color-text-secondary, #656d7b)'
export const colorTextSuccess = 'var(--color-text-success, #27ab95)'
export const colorTextTertiary = 'var(--color-text-tertiary, #9da4ae)'
export const colorTextWarning = 'var(--color-text-warning, #ff9f43)'

// Chart
export const colorChart1 = 'var(--color-chart-1, #0aaddf)'
export const colorChart2 = 'var(--color-chart-2, #ef4d56)'
export const colorChart3 = 'var(--color-chart-3, #27ab95)'
export const colorChart4 = 'var(--color-chart-4, #ff9f43)'
export const colorChart5 = 'var(--color-chart-5, #7a4dfc)'
export const colorChart6 = 'var(--color-chart-6, #0b8bb2)'
export const colorChart7 = 'var(--color-chart-7, #e61b26)'
export const colorChart8 = 'var(--color-chart-8, #13787b)'
export const colorChart9 = 'var(--color-chart-9, #fa810c)'
export const colorChart10 = 'var(--color-chart-10, #6837fc)'

// Chart palette — indexed access for building colour maps.
export const CHART_COLOURS = [
  colorChart1,
  colorChart2,
  colorChart3,
  colorChart4,
  colorChart5,
  colorChart6,
  colorChart7,
  colorChart8,
  colorChart9,
  colorChart10,
] as const

// Radius
export const radius2xl = 'var(--radius-2xl, 18px)'
export const radiusFull = 'var(--radius-full, 9999px)'
export const radiusLg = 'var(--radius-lg, 8px)'
export const radiusMd = 'var(--radius-md, 6px)'
export const radiusNone = 'var(--radius-none, 0px)'
export const radiusSm = 'var(--radius-sm, 4px)'
export const radiusXl = 'var(--radius-xl, 10px)'
export const radiusXs = 'var(--radius-xs, 2px)'

// Shadow
export const shadowLg =
  'var(--shadow-lg, 0px 8px 16px oklch(from var(--slate-1000) l c h / 0.15))'
export const shadowMd =
  'var(--shadow-md, 0px 4px 8px oklch(from var(--slate-1000) l c h / 0.12))'
export const shadowSm =
  'var(--shadow-sm, 0px 1px 2px oklch(from var(--slate-1000) l c h / 0.05))'
export const shadowXl =
  'var(--shadow-xl, 0px 12px 24px oklch(from var(--slate-1000) l c h / 0.20))'

// Duration
export const durationFast = 'var(--duration-fast, 100ms)'
export const durationNormal = 'var(--duration-normal, 200ms)'
export const durationSlow = 'var(--duration-slow, 300ms)'

// Easing
export const easingEntrance =
  'var(--easing-entrance, cubic-bezier(0.0, 0, 0.38, 0.9))'
export const easingExit = 'var(--easing-exit, cubic-bezier(0.2, 0, 1, 0.9))'
export const easingStandard =
  'var(--easing-standard, cubic-bezier(0.2, 0, 0.38, 0.9))'
