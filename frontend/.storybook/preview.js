/** @type { import('@storybook/react-webpack5').Preview } */

// Import global styles
import '../web/styles/styles.scss'

const preview = {
  parameters: {
    controls: {
      matchers: {
       color: /(background|color)$/i,
       date: /Date$/i,
      },
    },
  },
};

export default preview;