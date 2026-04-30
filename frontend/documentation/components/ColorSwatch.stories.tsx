import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import ColorSwatch from 'components/ColorSwatch'
import {
  CHART_COLOURS,
  colorChart1,
  colorChart3,
  colorChart4,
  colorSurfaceAction,
  colorSurfaceMuted,
} from 'common/theme/tokens'

const meta: Meta<typeof ColorSwatch> = {
  argTypes: {
    color: { control: 'color' },
    shape: { control: 'inline-radio', options: ['square', 'circle'] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
  },
  args: {
    color: colorChart1,
    shape: 'square',
    size: 'md',
  },
  component: ColorSwatch,
  parameters: {
    docs: {
      description: {
        component:
          'A small coloured shape used as a visual key. Pair it with a label anywhere a colour identifies something (a series, environment, tag, category, segment, on/off state). Defaults to a square; pass `shape="circle"` for a dot. Decorative — always accompany it with text or context.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Data Display/ColorSwatch',
}
export default meta

type Story = StoryObj<typeof ColorSwatch>

export const Default: Story = {}

export const Sizes: Story = {
  parameters: {
    docs: {
      description: {
        story:
          '`sm` (8px) suits dense rows, `md` (12px) is the default for inline labels, `lg` (16px) is for headers or emphasised labels.',
      },
    },
  },
  render: () => (
    <div className='d-flex align-items-center gap-3'>
      <ColorSwatch color={colorChart1} size='sm' />
      <ColorSwatch color={colorChart1} size='md' />
      <ColorSwatch color={colorChart1} size='lg' />
    </div>
  ),
}

export const WithLabel: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Canonical pairing: swatch + label. Use this anywhere a colour identifies a value — a tag, environment, series, or category.',
      },
    },
  },
  render: () => (
    <div className='d-flex align-items-center gap-2 fs-small'>
      <ColorSwatch color={colorChart1} />
      <span className='text-default'>Production</span>
    </div>
  ),
}

export const List: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'A vertical list stacking several swatch + label rows. Works for legends, colour pickers, category filters, or any colour-coded list.',
      },
    },
  },
  render: () => (
    <div className='d-flex flex-column gap-1 fs-small'>
      {[
        { color: colorChart1, name: 'Production' },
        { color: colorChart3, name: 'Staging' },
        { color: colorChart4, name: 'Development' },
      ].map(({ color, name }) => (
        <div key={name} className='d-flex align-items-center gap-2'>
          <ColorSwatch color={color} />
          <span className='text-default'>{name}</span>
        </div>
      ))}
    </div>
  ),
}

export const Shapes: Story = {
  parameters: {
    docs: {
      description: {
        story:
          '`square` (default) is the standard swatch. `circle` is used as a dot indicator — typical for boolean or status keys.',
      },
    },
  },
  render: () => (
    <div className='d-flex align-items-center gap-3'>
      <ColorSwatch color={colorChart1} shape='square' size='lg' />
      <ColorSwatch color={colorChart1} shape='circle' size='lg' />
    </div>
  ),
}

export const BooleanDot: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'On/off state shown as a dot — `circle` shape with action and muted surface tokens.',
      },
    },
  },
  render: () => (
    <div className='d-flex align-items-center gap-3'>
      <ColorSwatch color={colorSurfaceAction} shape='circle' size='lg' />
      <ColorSwatch color={colorSurfaceMuted} shape='circle' size='lg' />
    </div>
  ),
}

export const Palette: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'A row of swatches representing a palette. Useful for previewing the available colours when assigning colour-coded values.',
      },
    },
  },
  render: () => (
    <div className='d-flex gap-2'>
      {CHART_COLOURS.map((c, i) => (
        <ColorSwatch key={i} color={c} />
      ))}
    </div>
  ),
}
