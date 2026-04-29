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
import ReactSelect, { components as selectComponents } from 'react-select'
// Register safe globals that project-components.js would normally set.
// Only import components that use the automatic JSX transform (TSX files).
// Legacy .js files (Flex, Column, Input) use old JSX transform and crash here.
import Tooltip from '../web/components/Tooltip'
import Row from '../web/components/base/grid/Row'
import FormGroup from '../web/components/base/grid/FormGroup'

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
// Wrap ReactSelect to match the real app's global.Select (project-components.js)
// which adds className="react-select" and classNamePrefix="react-select"
// so _react-select.scss dark mode selectors work.
global.Select = (props) =>
  React.createElement(
    'div',
    { className: props.className, onClick: (e) => e.stopPropagation() },
    React.createElement(ReactSelect, {
      ...props,
      className: `react-select ${props.size || ''}`,
      classNamePrefix: 'react-select',
      components: { ...props.components },
    }),
  )
window.Tooltip = Tooltip
window.Row = Row
window.FormGroup = FormGroup

/** @type { import('storybook').Preview } */
const preview = {
  tags: ['autodocs'],
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
