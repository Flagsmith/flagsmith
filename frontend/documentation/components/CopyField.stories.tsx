import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import CopyField from 'components/CopyField'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Read-only input paired with an icon-only Copy button. Pass `value` to copy; render any width by wrapping in a sized container — the input flexes to fill the row.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Forms/CopyField',
}
export default meta

type Story = StoryObj

const Container: React.FC<React.PropsWithChildren> = ({ children }) => (
  <div style={{ width: 480 }}>{children}</div>
)

export const Default: Story = {
  render: () => (
    <Container>
      <CopyField value='https://app.flagsmith.com/api/v1/scim/organisations/42/scim/v2' />
    </Container>
  ),
}

export const Monospace: Story = {
  render: () => (
    <Container>
      <CopyField
        value='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzY2ltLXRva2VuIn0'
        className='font-monospace'
      />
    </Container>
  ),
}

export const ShortValue: Story = {
  render: () => (
    <Container>
      <CopyField value='org_42' />
    </Container>
  ),
}

export const LongValue: Story = {
  render: () => (
    <Container>
      <CopyField value='https://very-long-subdomain.example.flagsmith-eu.com/api/v1/auth/saml/configurations/marketing-okta/response/redirect?next=/dashboard' />
    </Container>
  ),
}
