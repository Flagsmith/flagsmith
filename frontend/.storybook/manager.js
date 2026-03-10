import { addons } from 'storybook/manager-api'
import { create } from 'storybook/theming'

// Primitive palette — mirrors _primitives.scss
// Storybook manager runs outside the app, so CSS vars aren't available.
const slate = {
  200: '#e0e3e9',
  300: '#9da4ae',
  850: '#161d30',
  900: '#15192b',
}
const purple = { 600: '#6837fc' }

addons.setConfig({
  theme: create({
    base: 'dark',
    brandTitle: 'Flagsmith',
    brandUrl: 'https://flagsmith.com',
    brandImage: '/static/images/nav-logo.png',
    brandTarget: '_blank',

    // Sidebar
    appBg: slate[900],
    appContentBg: slate[850],
    appBorderColor: 'rgba(255, 255, 255, 0.1)',

    // Typography
    fontBase: '"Inter", sans-serif',

    // Toolbar
    barBg: slate[900],
    barTextColor: slate[300],
    barSelectedColor: purple[600],

    // Colours
    colorPrimary: purple[600],
    colorSecondary: purple[600],

    // Text
    textColor: slate[200],
    textMutedColor: slate[300],
    textInverseColor: slate[900],
  }),
})
