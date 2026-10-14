import { addons } from 'storybook/manager-api'
import { create } from 'storybook/theming'
import { primitives } from '../common/theme/tokens.json'

// The manager runs outside the app, so it reads hex values, not CSS vars.
const slate = (step) => primitives[`slate-${step}`]
const purple = (step) => primitives[`purple-${step}`]

const shared = {
  brandTitle: 'Flagsmith',
  brandUrl: 'https://flagsmith.com',
  brandImage: '/static/images/nav-logo.png',
  brandTarget: '_blank',
  fontBase: '"Inter", sans-serif',
  colorPrimary: purple(600),
  colorSecondary: purple(600),
}

const dark = create({
  base: 'dark',
  ...shared,
  appBg: slate(900),
  appContentBg: slate(850),
  appBorderColor: 'rgba(255, 255, 255, 0.1)',
  barBg: slate(900),
  barTextColor: slate(300),
  barSelectedColor: purple(600),
  textColor: slate(200),
  textMutedColor: slate(300),
  textInverseColor: slate(900),
})

const light = create({
  base: 'light',
  ...shared,
  appBg: slate(50),
  appContentBg: slate(0),
  appBorderColor: slate(100),
  barBg: slate(0),
  barTextColor: slate(500),
  barSelectedColor: purple(600),
  textColor: slate(600),
  textMutedColor: slate(300),
  textInverseColor: slate(0),
})

const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

addons.setConfig({
  theme: prefersDark ? dark : light,
})
