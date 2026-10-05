import type { Meta, StoryObj } from 'storybook'

import Table, {
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from 'components/base/Table'
import { DependenciesPanel } from 'components/modals/create-feature/tabs/FeatureDependenciesTab'

const meta: Meta<typeof Table> = {
  component: Table,
  parameters: {
    chromatic: { disableSnapshot: false },
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
  <TableBody>
    {ROWS.map((row) => (
      <TableRow key={row.flag}>
        <TableCell>{row.flag}</TableCell>
        <TableCell>{row.env}</TableCell>
        <TableCell>{row.state}</TableCell>
      </TableRow>
    ))}
  </TableBody>
)

const Head = () => (
  <TableHeader>
    <TableRow>
      <TableColumnHeader>Feature</TableColumnHeader>
      <TableColumnHeader>Environment</TableColumnHeader>
      <TableColumnHeader>State</TableColumnHeader>
    </TableRow>
  </TableHeader>
)

// The house style: MetricsTable and ExperimentsTable both already draw this.
export const Hover: Story = {
  render: () => (
    <Table highlightRowOnHover>
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
      <TableHeader>
        <TableRow>
          <TableColumnHeader>Feature</TableColumnHeader>
          <TableColumnHeader>Environment</TableColumnHeader>
          <TableColumnHeader>State</TableColumnHeader>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className='text-truncate'>
            a_very_long_feature_name_that_would_otherwise_widen_the_table
          </TableCell>
          <TableCell>Production</TableCell>
          <TableCell>On</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
}

export const Empty: Story = {
  render: () => (
    <Table>
      <Head />
      <TableBody />
    </Table>
  ),
}

export const RowPending: Story = {
  name: 'Row, write in flight',
  render: () => (
    <Table>
      <Head />
      <TableBody>
        <TableRow>
          <TableCell>billing_engine_v2</TableCell>
          <TableCell>Production</TableCell>
          <TableCell>On</TableCell>
        </TableRow>
        <TableRow pending>
          <TableCell>payment_provider</TableCell>
          <TableCell>Staging</TableCell>
          <TableCell>Off</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
}

// The actions column is the table's, so two tables do not each pick a width.
export const ActionsColumn: Story = {
  render: () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableColumnHeader>Feature</TableColumnHeader>
          <TableColumnHeader
            className='ds-table__actions text-end'
            aria-label='Actions'
          />
        </TableRow>
      </TableHeader>
      <TableBody>
        {ROWS.map((row) => (
          <TableRow key={row.flag}>
            <TableCell>{row.flag}</TableCell>
            <TableCell className='ds-table__actions text-end'>···</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  ),
}
