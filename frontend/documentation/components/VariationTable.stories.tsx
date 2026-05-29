import type { Meta, StoryObj } from 'storybook'

import VariationTable from 'components/experiments/VariationTable'
import { MultivariateOption } from 'common/types/responses'

const TWO_VARIATIONS: MultivariateOption[] = [
  {
    boolean_value: false,
    default_percentage_allocation: 50,
    id: 1,
    string_value: 'variant-a',
    type: 'unicode',
    uuid: 'a1',
  },
  {
    boolean_value: false,
    default_percentage_allocation: 50,
    id: 2,
    string_value: 'variant-b',
    type: 'unicode',
    uuid: 'b2',
  },
]

const MANY_VARIATIONS: MultivariateOption[] = [
  {
    boolean_value: false,
    default_percentage_allocation: 25,
    id: 1,
    string_value: 'small-hero',
    type: 'unicode',
    uuid: 'v1',
  },
  {
    boolean_value: false,
    default_percentage_allocation: 25,
    id: 2,
    integer_value: 42,
    string_value: '',
    type: 'int',
    uuid: 'v2',
  },
  {
    boolean_value: true,
    default_percentage_allocation: 25,
    id: 3,
    string_value: '',
    type: 'bool',
    uuid: 'v3',
  },
  {
    boolean_value: false,
    default_percentage_allocation: 15,
    id: 4,
    string_value: 'large-hero',
    type: 'unicode',
    uuid: 'v4',
  },
  {
    boolean_value: false,
    default_percentage_allocation: 10,
    id: 5,
    string_value: 'extra-large-hero',
    type: 'unicode',
    uuid: 'v5',
  },
]

const meta: Meta<typeof VariationTable> = {
  component: VariationTable,
  parameters: {
    docs: {
      description: {
        component:
          "Displays a feature flag's control value and multivariate options in a read-only table. Used in the experiment wizard to preview variations.",
      },
    },
    layout: 'padded',
  },
  title: 'Components/Experiments/VariationTable',
}
export default meta

type Story = StoryObj<typeof VariationTable>

export const Default: Story = {
  args: {
    controlValue: 'default-button',
    variations: TWO_VARIATIONS,
  },
}

export const ManyVariations: Story = {
  args: {
    controlValue: 'control-value',
    variations: MANY_VARIATIONS,
  },
  parameters: {
    docs: {
      description: {
        story:
          'A table with multiple variation types (unicode, int, bool) showing how different value types render.',
      },
    },
  },
}
