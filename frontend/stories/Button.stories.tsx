import React from 'react'
import type { Meta, StoryObj } from '@storybook/react-webpack5'
import Button, {
  themeClassNames,
  sizeClassNames,
} from 'components/base/forms/Button'

const themes = Object.keys(themeClassNames) as Array<
  keyof typeof themeClassNames
>
const sizes = Object.keys(sizeClassNames) as Array<keyof typeof sizeClassNames>

const meta: Meta<typeof Button> = {
  component: Button,
  parameters: {
    layout: 'padded',
  },
  title: 'Components/Button',
}
export default meta

type Story = StoryObj<typeof Button>

// ---------------------------------------------------------------------------
// All themes
// ---------------------------------------------------------------------------

export const AllThemes: Story = {
  name: 'All themes',
  render: () => (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
      {themes.map((theme) => (
        <Button key={theme} theme={theme}>
          {theme}
        </Button>
      ))}
    </div>
  ),
}

// ---------------------------------------------------------------------------
// All sizes
// ---------------------------------------------------------------------------

export const AllSizes: Story = {
  name: 'All sizes',
  render: () => (
    <div
      style={{
        alignItems: 'center',
        display: 'flex',
        flexWrap: 'wrap',
        gap: 12,
      }}
    >
      {sizes.map((size) => (
        <Button key={size} size={size}>
          {size}
        </Button>
      ))}
    </div>
  ),
}

// ---------------------------------------------------------------------------
// Theme × Size matrix
// ---------------------------------------------------------------------------

export const ThemeSizeMatrix: Story = {
  name: 'Theme × Size matrix',
  render: () => (
    <table style={{ borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          <th
            style={{
              color: 'var(--colorTextSecondary, #656d7b)',
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: '0.05em',
              padding: '8px 12px',
              textAlign: 'left',
              textTransform: 'uppercase',
            }}
          >
            Theme / Size
          </th>
          {sizes.map((size) => (
            <th
              key={size}
              style={{
                color: 'var(--colorTextSecondary, #656d7b)',
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: '0.05em',
                padding: '8px 12px',
                textAlign: 'center',
                textTransform: 'uppercase',
              }}
            >
              {size}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {themes.map((theme) => (
          <tr key={theme}>
            <td
              style={{
                fontFamily: 'monospace',
                fontSize: 12,
                padding: '8px 12px',
              }}
            >
              {theme}
            </td>
            {sizes.map((size) => (
              <td
                key={size}
                style={{ padding: '8px 12px', textAlign: 'center' }}
              >
                <Button theme={theme} size={size}>
                  Label
                </Button>
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  ),
}

// ---------------------------------------------------------------------------
// With icons
// ---------------------------------------------------------------------------

export const WithIcons: Story = {
  name: 'With icons',
  render: () => (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
      <Button iconLeft='plus'>Icon left</Button>
      <Button iconRight='chevron-right'>Icon right</Button>
      <Button iconLeft='setting' iconRight='chevron-down'>
        Both icons
      </Button>
      <Button theme='secondary' iconLeft='copy'>
        Copy
      </Button>
      <Button theme='danger' iconLeft='trash-2'>
        Delete
      </Button>
    </div>
  ),
}

// ---------------------------------------------------------------------------
// States
// ---------------------------------------------------------------------------

export const States: Story = {
  render: () => (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
      <Button>Default</Button>
      <Button disabled>Disabled</Button>
      <Button theme='secondary'>Secondary</Button>
      <Button theme='secondary' disabled>
        Secondary disabled
      </Button>
      <Button theme='danger'>Danger</Button>
      <Button theme='danger' disabled>
        Danger disabled
      </Button>
    </div>
  ),
}

// ---------------------------------------------------------------------------
// As link
// ---------------------------------------------------------------------------

export const AsLink: Story = {
  name: 'As link (href)',
  render: () => (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
      <Button href='#'>Primary link</Button>
      <Button href='#' theme='secondary'>
        Secondary link
      </Button>
      <Button href='#' theme='text'>
        Text link
      </Button>
    </div>
  ),
}
