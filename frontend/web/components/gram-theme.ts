/**
 * Flagsmith theme overrides for Gram Elements.
 *
 * These map Gram's CSS custom properties to Flagsmith's design tokens.
 * Injected into the shadow DOM since Gram renders in an isolated root.
 *
 * Colour values sourced from web/styles/_variables.scss.
 */

// From _variables.scss
const colors = {
  bgDark100: '#2d3443',

  bgDark200: '#202839',

  bgDark400: '#15192b',
  // Backgrounds
  bgDark500: '#101628',
  bgLight100: '#ffffff',
  bgLight200: '#fafafb',
  bgLight300: '#eff1f4',
  bgLight500: '#e0e3e9',

  // Text
  bodyColor: '#1a2634',
  bodyColorDark: '#ffffff',
  danger: '#ef4d56',

  headerColorDark: '#e1e1e1',

  // Brand
  primary: '#6837fc',

  primary900: '#1E0D26',
  primaryForeground: '#ffffff',
  textMuted: '#656d7b',
  textMutedDark: '#9da4ae',

  whiteAlpha16: 'rgba(255, 255, 255, 0.16)',
  // Borders
  whiteAlpha8: 'rgba(255, 255, 255, 0.08)',
} as const

function gramThemeVars(vars: Record<string, string>): string {
  const entries = Object.entries(vars)
    .map(([key, value]) => `    ${key}: ${value} !important;`)
    .join('\n')
  return `:host, .gram-elements, :root {\n${entries}\n  }`
}

export const GRAM_DARK_THEME_CSS = gramThemeVars({
  '--accent': colors.bgDark100,
  '--accent-foreground': colors.bodyColorDark,
  '--background': colors.bgDark500,
  '--border': colors.whiteAlpha8,
  '--card': colors.bgDark400,
  '--card-foreground': colors.bodyColorDark,
  '--destructive': colors.danger,
  '--foreground': colors.bodyColorDark,
  '--input': colors.whiteAlpha16,
  '--muted': colors.bgDark200,
  '--muted-foreground': colors.textMutedDark,
  '--popover': colors.bgDark400,
  '--popover-foreground': colors.bodyColorDark,
  '--primary': colors.primary,
  '--primary-foreground': colors.primaryForeground,
  '--ring': colors.primary,
  '--secondary': colors.bgDark200,
  '--secondary-foreground': colors.headerColorDark,
})

export const GRAM_LIGHT_THEME_CSS = gramThemeVars({
  '--accent': colors.bgLight300,
  '--accent-foreground': colors.primary900,
  '--background': colors.bgLight100,
  '--border': colors.bgLight500,
  '--card': colors.bgLight100,
  '--card-foreground': colors.bodyColor,
  '--destructive': colors.danger,
  '--foreground': colors.bodyColor,
  '--input': colors.bgLight500,
  '--muted': colors.bgLight300,
  '--muted-foreground': colors.textMuted,
  '--popover': colors.bgLight100,
  '--popover-foreground': colors.bodyColor,
  '--primary': colors.primary,
  '--primary-foreground': colors.primaryForeground,
  '--ring': colors.primary,
  '--secondary': colors.bgLight200,
  '--secondary-foreground': colors.primary900,
})
