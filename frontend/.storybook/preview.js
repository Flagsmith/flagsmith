import '../web/styles/styles.scss'
import './docs-theme.scss'
import { allModes } from './modes'
import { DocsContainer } from './DocsContainer'

// TODO: Remove these globals once legacy .js components (Input.js, etc.) are
// migrated to TypeScript with proper imports. These replicate what
// web/project/libs.js and web/project/project-components.js set at boot.
// Utils is stubbed via webpack alias in main.js to avoid circular deps.
import React from 'react'
import PropTypes from 'prop-types'
import Utils from 'common/utils/utils'
import ReactSelect from 'react-select'
import Tooltip from '../web/components/Tooltip'

window.React = React
window.propTypes = PropTypes
window.OptionalString = PropTypes.string
window.OptionalFunc = PropTypes.func
window.OptionalBool = PropTypes.bool
window.OptionalNumber = PropTypes.number
window.OptionalObject = PropTypes.object
window.OptionalArray = PropTypes.array
window.OptionalNode = PropTypes.node
window.OptionalElement = PropTypes.element
window.RequiredString = PropTypes.string.isRequired
window.RequiredFunc = PropTypes.func.isRequired
window.RequiredBool = PropTypes.bool.isRequired
window.RequiredNumber = PropTypes.number.isRequired
window.RequiredObject = PropTypes.object.isRequired
window.RequiredNode = PropTypes.node.isRequired
window.Any = PropTypes.any
window.oneOf = PropTypes.oneOf
window.oneOfType = PropTypes.oneOfType
window.Utils = Utils
global.Select = ReactSelect
global.Tooltip = Tooltip

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
    docs: {
      container: DocsContainer,
    },
    chromatic: {
      modes: {
        light: allModes.light,
        dark: allModes.dark,
      },
    },
  },
}

export default preview
