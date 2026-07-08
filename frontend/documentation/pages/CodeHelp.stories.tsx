import type { Meta, StoryObj } from 'storybook'

import CodeHelp from 'components/CodeHelp'
import Constants from 'common/constants'

// A stand-in environment key for the snippets.
const ENV = 'YOUR_ENVIRONMENT_KEY'

const meta: Meta<typeof CodeHelp> = {
  component: CodeHelp,
  parameters: {
    docs: {
      description: {
        component:
          'The shared code-example component, used across SDK setup, identities, segments and environment docs. These stories mirror those real use cases with the actual `codeHelp` snippets. Use the theme toggle in the toolbar to QA the code block (surface + syntax colours) in light and dark, and the language dropdown to check each SDK.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/CodeHelp',
}
export default meta

type Story = StoryObj<typeof CodeHelp>

// Installing the SDK (SDK integration page).
export const Install: Story = {
  args: {
    showInitially: true,
    snippets: Constants.codeHelp.INSTALL,
    title: 'Installing the SDK',
  },
}

// Initialising the client, keyed by the environment (the most common use).
export const Initialise: Story = {
  args: {
    showInitially: true,
    snippets: Constants.codeHelp.INIT(ENV),
    title: 'Initialising your project',
  },
}

// Creating an identity (identities pages).
export const CreateIdentity: Story = {
  args: {
    showInitially: true,
    snippets: Constants.codeHelp.CREATE_USER(ENV),
    title: 'Creating an identity',
  },
}

// Setting traits (identities pages).
export const SetTraits: Story = {
  args: {
    showInitially: true,
    snippets: Constants.codeHelp.USER_TRAITS(ENV),
    title: 'Setting traits',
  },
}

// Default entry point: the collapsed CalloutBar header before it's opened.
export const CollapsedHeader: Story = {
  args: {
    snippets: Constants.codeHelp.INSTALL,
    title: 'Installing the SDK',
  },
}

// Embedded with no header and no docs links (e.g. inside another panel).
export const Embedded: Story = {
  args: {
    hideDocs: true,
    hideHeader: true,
    snippets: Constants.codeHelp.INIT(ENV),
  },
}
