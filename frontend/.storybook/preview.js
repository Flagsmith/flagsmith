import '../web/styles/styles.scss'
import './docs-theme.scss'
import { allModes } from './modes'

/** @type { import('storybook').Preview } */
const preview = {
  globalTypes: {
    theme: {
      description: 'Dark mode toggle',
      toolbar: {
        title: 'Theme',
        icon: 'moon',
        items: [
          { value: 'light', title: 'Light', icon: 'sun' },
          { value: 'dark', title: 'Dark', icon: 'moon' },
        ],
        dynamicTitle: true,
      },
    },
  },
  initialGlobals: {
    theme: window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light',
  },
  decorators: [
    (Story, context) => {
      const theme = context.globals.theme || 'light'
      const isDark = theme === 'dark'

      document.documentElement.setAttribute(
        'data-bs-theme',
        isDark ? 'dark' : 'light',
      )
      document.body.classList.toggle('dark', isDark)

      return Story()
    },
  ],
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: { disable: true },
    chromatic: {
      modes: {
        light: allModes.light,
        dark: allModes.dark,
      },
    },
  },
}

export default preview
