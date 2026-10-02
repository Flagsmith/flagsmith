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
// Font-weight
export const fontWeight: Record<string, TokenEntry> = {
  'bold': {
    description: 'Maximum emphasis. Page titles, key figures.',
    value: 'var(--font-weight-bold, 700)',
  },
  'medium': {
    description: 'Subtle emphasis. Labels, secondary headings, table headers.',
    value: 'var(--font-weight-medium, 500)',
  },
  'regular': {
    description: 'Body copy, default text.',
    value: 'var(--font-weight-regular, 400)',
  },
  'semibold': {
    description:
      'Strong emphasis. Card titles, selected states, section headings.',
    value: 'var(--font-weight-semibold, 600)',
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
export const colorBorderDanger = 'var(--color-border-danger, #e61b26)'
export const colorBorderDefault =
  'var(--color-border-default, rgba(101, 109, 123, 0.16))'
export const colorBorderDisabled =
  'var(--color-border-disabled, rgba(101, 109, 123, 0.08))'
export const colorBorderInfo = 'var(--color-border-info, #0fa5fc)'
export const colorBorderStrong =
  'var(--color-border-strong, rgba(101, 109, 123, 0.24))'
export const colorBorderSuccess = 'var(--color-border-success, #47aa7f)'
export const colorBorderWarning = 'var(--color-border-warning, #ffbc05)'

// Code
export const colorCodeBuiltin = 'var(--color-code-builtin, #e8a705)'
export const colorCodeComment = 'var(--color-code-comment, #9da4ae)'
export const colorCodeKeyword = 'var(--color-code-keyword, #6837fc)'
export const colorCodeLiteral = 'var(--color-code-literal, #0b82d7)'
export const colorCodeName = 'var(--color-code-name, #ef4d56)'
export const colorCodeString = 'var(--color-code-string, #47aa7f)'
export const colorCodeText = 'var(--color-code-text, #2d3443)'
export const colorCodeTitle = 'var(--color-code-title, #0fa5fc)'
export const colorCodeVariable = 'var(--color-code-variable, #d06907)'

// Icon
export const colorIconAction = 'var(--color-icon-action, #6837fc)'
export const colorIconDanger = 'var(--color-icon-danger, #e61b26)'
export const colorIconDefault = 'var(--color-icon-default, #1a2634)'
export const colorIconDisabled = 'var(--color-icon-disabled, #9da4ae)'
export const colorIconInfo = 'var(--color-icon-info, #0fa5fc)'
export const colorIconSecondary = 'var(--color-icon-secondary, #656d7b)'
export const colorIconSuccess = 'var(--color-icon-success, #47aa7f)'
export const colorIconWarning = 'var(--color-icon-warning, #ffbc05)'

// Surface
export const colorSurfaceAction = 'var(--color-surface-action, #6837fc)'
export const colorSurfaceActionActive =
  'var(--color-surface-action-active, #3919b7)'
export const colorSurfaceActionHover =
  'var(--color-surface-action-hover, #4f28d8)'
export const colorSurfaceActionMuted =
  'var(--color-surface-action-muted, rgba(104, 55, 252, 0.16))'
export const colorSurfaceActionSubtle =
  'var(--color-surface-action-subtle, rgba(104, 55, 252, 0.08))'
export const colorSurfaceActionTint =
  'var(--color-surface-action-tint, rgba(104, 55, 252, 0.12))'
export const colorSurfaceActive =
  'var(--color-surface-active, rgba(8, 12, 23, 0.16))'
export const colorSurfaceDanger = 'var(--color-surface-danger, #ffeddb)'
export const colorSurfaceDefault = 'var(--color-surface-default, #ffffff)'
export const colorSurfaceEmphasis = 'var(--color-surface-emphasis, #e1e2eb)'
export const colorSurfaceHover =
  'var(--color-surface-hover, rgba(8, 12, 23, 0.08))'
export const colorSurfaceInfo = 'var(--color-surface-info, #dff3ff)'
export const colorSurfaceMuted = 'var(--color-surface-muted, #f3f4f5)'
export const colorSurfaceSubtle = 'var(--color-surface-subtle, #fafafb)'
export const colorSurfaceSuccess = 'var(--color-surface-success, #f0fff2)'
export const colorSurfaceWarning = 'var(--color-surface-warning, #fff7cd)'

// Text
export const colorTextAction = 'var(--color-text-action, #6837fc)'
export const colorTextDanger = 'var(--color-text-danger, #7a0e18)'
export const colorTextDefault = 'var(--color-text-default, #1a2634)'
export const colorTextDisabled = 'var(--color-text-disabled, #9da4ae)'
export const colorTextInfo = 'var(--color-text-info, #023078)'
export const colorTextSecondary = 'var(--color-text-secondary, #656d7b)'
export const colorTextSuccess = 'var(--color-text-success, #1b392b)'
export const colorTextTertiary = 'var(--color-text-tertiary, #656d7b)'
export const colorTextWarning = 'var(--color-text-warning, #744800)'

// Chart
export const colorChart1 = 'var(--color-chart-1, #0fa5fc)'
export const colorChart2 = 'var(--color-chart-2, #ef4d56)'
export const colorChart3 = 'var(--color-chart-3, #47aa7f)'
export const colorChart4 = 'var(--color-chart-4, #ff9f43)'
export const colorChart5 = 'var(--color-chart-5, #7a4dfc)'
export const colorChart6 = 'var(--color-chart-6, #0b82d7)'
export const colorChart7 = 'var(--color-chart-7, #e61b26)'
export const colorChart8 = 'var(--color-chart-8, #35795a)'
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

// Primary
export const primary50 = 'var(--primary-50, #f5f0ff)'
export const primary100 = 'var(--primary-100, #e7e1f4)'
export const primary300 = 'var(--primary-300, #d4beff)'
export const primary400 = 'var(--primary-400, #9168fd)'
export const primary500 = 'var(--primary-500, #6837fc)'
export const primary600 = 'var(--primary-600, #4f28d8)'
export const primary900 = 'var(--primary-900, #1a0a78)'

// Neutral
export const neutral0 = 'var(--neutral-0, #ffffff)'
export const neutral50 = 'var(--neutral-50, #fafafb)'
export const neutral100 = 'var(--neutral-100, #f3f4f5)'
export const neutral300 = 'var(--neutral-300, #e1e2eb)'
export const neutral400 = 'var(--neutral-400, #bfc0c5)'
export const neutral500 = 'var(--neutral-500, #656d7b)'
export const neutral600 = 'var(--neutral-600, #1a2634)'
export const neutral900 = 'var(--neutral-900, #0e1629)'

// State
export const danger100 = 'var(--danger-100, #ffeddb)'
export const danger500 = 'var(--danger-500, #e61b26)'
export const danger900 = 'var(--danger-900, #7a0e18)'
export const info100 = 'var(--info-100, #dff3ff)'
export const info500 = 'var(--info-500, #0fa5fc)'
export const info900 = 'var(--info-900, #023078)'
export const success100 = 'var(--success-100, #f0fff2)'
export const success500 = 'var(--success-500, #6ad0a1)'
export const success900 = 'var(--success-900, #1b392b)'
export const warning100 = 'var(--warning-100, #fff7cd)'
export const warning500 = 'var(--warning-500, #ffbc05)'
export const warning900 = 'var(--warning-900, #744800)'

// Always
export const alwaysPrimary = 'var(--always-primary, #6837fc)'
export const alwaysWhite = 'var(--always-white, #ffffff)'

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

// Font-weight
export const fontWeightBold = 'var(--font-weight-bold, 700)'
export const fontWeightMedium = 'var(--font-weight-medium, 500)'
export const fontWeightRegular = 'var(--font-weight-regular, 400)'
export const fontWeightSemibold = 'var(--font-weight-semibold, 600)'
