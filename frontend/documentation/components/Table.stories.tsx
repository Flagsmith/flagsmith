import type { Meta, StoryObj } from 'storybook'

import Table from 'components/base/Table'
import { DependenciesPanel } from 'components/modals/create-feature/tabs/FeatureDependenciesTab'

const meta: Meta<typeof Table> = {
  component: Table,
  parameters: {
    docs: {
      description: {
        component:
          'The semantic table elements, styled. Composed rather than configured: no columns or rows prop, because cells hold toggles, buttons and tooltips. Sorting and filtering sit above it, as they do in shadcn/ui and Radix Themes.',
      },
    },
  },
  title: 'Components/Table',
}
export default meta

type Story = StoryObj<typeof Table>

const ROWS = [
  { env: 'Production', flag: 'billing_engine_v2', state: 'On' },
  { env: 'Staging', flag: 'payment_provider', state: 'Off' },
  { env: 'Development', flag: 'dark_mode', state: 'On' },
]

const Rows = () => (
  <Table.Body>
    {ROWS.map((row) => (
      <Table.Row key={row.flag}>
        <Table.Cell>{row.flag}</Table.Cell>
        <Table.Cell>{row.env}</Table.Cell>
        <Table.Cell>{row.state}</Table.Cell>
      </Table.Row>
    ))}
  </Table.Body>
)

const Head = () => (
  <Table.Header>
    <Table.Row>
      <Table.ColumnHeader>Feature</Table.ColumnHeader>
      <Table.ColumnHeader>Environment</Table.ColumnHeader>
      <Table.ColumnHeader>State</Table.ColumnHeader>
    </Table.Row>
  </Table.Header>
)

// The house style: MetricsTable and ExperimentsTable both already draw this.
export const Hover: Story = {
  render: () => (
    <Table hover>
      <Head />
      <Rows />
    </Table>
  ),
}

export const Surface: Story = {
  render: () => (
    <Table>
      <Head />
      <Rows />
    </Table>
  ),
}

export const Ghost: Story = {
  render: () => (
    <DependenciesPanel>
      <Table variant='ghost'>
        <Head />
        <Rows />
      </Table>
    </DependenciesPanel>
  ),
}

// Columns share the width evenly, so a long name truncates in its cell rather
// than pushing the others out.
export const FixedLayout: Story = {
  render: () => (
    <Table layout='fixed'>
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader>Feature</Table.ColumnHeader>
          <Table.ColumnHeader>Environment</Table.ColumnHeader>
          <Table.ColumnHeader>State</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        <Table.Row>
          <Table.Cell className='text-truncate'>
            a_very_long_feature_name_that_would_otherwise_widen_the_table
          </Table.Cell>
          <Table.Cell>Production</Table.Cell>
          <Table.Cell>On</Table.Cell>
        </Table.Row>
      </Table.Body>
    </Table>
  ),
}

export const Empty: Story = {
  render: () => (
    <Table>
      <Head />
      <Table.Body />
    </Table>
  ),
}
