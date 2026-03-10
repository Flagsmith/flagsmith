import React from 'react'
import type { Meta, StoryObj } from '@storybook/react-webpack5'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Colour Palette',
}
export default meta

// ---------------------------------------------------------------------------
// Primitive scales — mirrors web/styles/_primitives.scss
// ---------------------------------------------------------------------------

type Scale = { label: string; hex: string; mapping?: string }[]

const slate: Scale = [
  { hex: '#ffffff', label: '0', mapping: '$bg-light100' },
  { hex: '#fafafb', label: '50', mapping: '$bg-light200' },
  { hex: '#eff1f4', label: '100', mapping: '$bg-light300' },
  { hex: '#e0e3e9', label: '200', mapping: '$bg-light500' },
  { hex: '#9da4ae', label: '300', mapping: '$text-icon-light-grey' },
  { hex: '#767d85', label: '400' },
  { hex: '#656d7b', label: '500', mapping: '$text-icon-grey' },
  { hex: '#1a2634', label: '600', mapping: '$body-color' },
  { hex: '#2d3443', label: '700', mapping: '$bg-dark100' },
  { hex: '#202839', label: '800', mapping: '$bg-dark200' },
  { hex: '#161d30', label: '850', mapping: '$bg-dark300' },
  { hex: '#15192b', label: '900', mapping: '$bg-dark400' },
  { hex: '#101628', label: '950', mapping: '$bg-dark500' },
]

const purple: Scale = [
  { hex: '#f5f0ff', label: '50' },
  { hex: '#e8dbff', label: '100' },
  { hex: '#d4bcff', label: '200' },
  { hex: '#b794ff', label: '300' },
  { hex: '#906af6', label: '400', mapping: '$primary400' },
  { hex: '#7a4dfc', label: '500' },
  { hex: '#6837fc', label: '600', mapping: '$primary' },
  { hex: '#4e25db', label: '700', mapping: '$primary600' },
  { hex: '#3919b7', label: '800', mapping: '$primary700' },
  { hex: '#2a2054', label: '900', mapping: '$primary800' },
  { hex: '#1e163e', label: '950' },
]

const red: Scale = [
  { hex: '#fef2f1', label: '50' },
  { hex: '#fce5e4', label: '100' },
  { hex: '#f9cbc9', label: '200' },
  { hex: '#f5a5a2', label: '300' },
  { hex: '#f57c78', label: '400', mapping: '$danger400' },
  { hex: '#ef4d56', label: '500', mapping: '$danger' },
  { hex: '#e61b26', label: '600' },
  { hex: '#bb1720', label: '700' },
  { hex: '#90141b', label: '800' },
  { hex: '#701116', label: '900' },
  { hex: '#500d11', label: '950' },
]

const green: Scale = [
  { hex: '#eef9f6', label: '50' },
  { hex: '#d6f1eb', label: '100' },
  { hex: '#b5e5da', label: '200' },
  { hex: '#87d4c4', label: '300' },
  { hex: '#56ccad', label: '400', mapping: '$success400' },
  { hex: '#27ab95', label: '500', mapping: '$success' },
  { hex: '#13787b', label: '600', mapping: '$success600' },
  { hex: '#116163', label: '700' },
  { hex: '#0e4a4c', label: '800' },
  { hex: '#0c3a3b', label: '900' },
  { hex: '#09292a', label: '950' },
]

const gold: Scale = [
  { hex: '#fefbf0', label: '50' },
  { hex: '#fdf6e0', label: '100' },
  { hex: '#faeec5', label: '200' },
  { hex: '#fae392', label: '300', mapping: '$secondary' },
  { hex: '#f9dc80', label: '400' },
  { hex: '#f7d56e', label: '500', mapping: '$secondary500' },
  { hex: '#e5c55f', label: '600', mapping: '$secondary600' },
  { hex: '#d4b050', label: '700', mapping: '$secondary700' },
  { hex: '#b38f30', label: '800' },
  { hex: '#8b7027', label: '900' },
  { hex: '#64511e', label: '950' },
]

const blue: Scale = [
  { hex: '#eef8fb', label: '50' },
  { hex: '#d6eef5', label: '100' },
  { hex: '#b3e0ed', label: '200' },
  { hex: '#7ecde2', label: '300' },
  { hex: '#45bce0', label: '400' },
  { hex: '#0aaddf', label: '500', mapping: '$info' },
  { hex: '#0b8bb2', label: '600' },
  { hex: '#0b7190', label: '700' },
  { hex: '#0b576e', label: '800' },
  { hex: '#094456', label: '900' },
  { hex: '#07313e', label: '950' },
]

const orange: Scale = [
  { hex: '#fff5ec', label: '50' },
  { hex: '#ffe9d4', label: '100' },
  { hex: '#ffd7b5', label: '200' },
  { hex: '#ffc08a', label: '300' },
  { hex: '#efb47c', label: '400' },
  { hex: '#ff9f43', label: '500', mapping: '$warning' },
  { hex: '#fa810c', label: '600' },
  { hex: '#d06907', label: '700' },
  { hex: '#9f5208', label: '800' },
  { hex: '#7b4008', label: '900' },
  { hex: '#592f07', label: '950' },
]

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

const Swatch: React.FC<{ hex: string; label: string; mapping?: string }> = ({
  hex,
  label,
  mapping,
}) => {
  const isDark =
    parseInt(hex.replace('#', '').slice(0, 2), 16) < 128 &&
    parseInt(hex.replace('#', '').slice(2, 4), 16) < 128

  return (
    <div
      style={{ display: 'flex', flexDirection: 'column', gap: 4, width: 72 }}
    >
      <div
        style={{
          alignItems: 'flex-end',
          background: hex,
          border: '1px solid rgba(128,128,128,0.2)',
          borderRadius: 8,
          color: isDark ? '#fff' : '#1a2634',
          display: 'flex',
          fontSize: 11,
          fontWeight: 600,
          height: 56,
          padding: 6,
        }}
      >
        {label}
      </div>
      <code
        style={{ color: 'var(--color-text-secondary, #656d7b)', fontSize: 10 }}
      >
        {hex}
      </code>
      {mapping && (
        <code
          style={{
            color: 'var(--color-text-tertiary, #9da4ae)',
            fontSize: 9,
            wordBreak: 'break-all',
          }}
        >
          {mapping}
        </code>
      )}
    </div>
  )
}

const ScaleRow: React.FC<{
  name: string
  scale: Scale
  description?: string
}> = ({ description, name, scale }) => (
  <div style={{ marginBottom: 32 }}>
    <h3
      style={{
        color: 'var(--color-text-default, #1a2634)',
        fontSize: 16,
        fontWeight: 700,
        marginBottom: 4,
      }}
    >
      {name}
    </h3>
    {description && (
      <p
        style={{
          color: 'var(--color-text-secondary, #656d7b)',
          fontSize: 13,
          marginBottom: 12,
          marginTop: 0,
        }}
      >
        {description}
      </p>
    )}
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {scale.map((s) => (
        <Swatch key={s.label} {...s} />
      ))}
    </div>
  </div>
)

// ---------------------------------------------------------------------------
// Stories
// ---------------------------------------------------------------------------

export const Primitives: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
      <h2
        style={{ color: 'var(--color-text-default, #1a2634)', marginBottom: 4 }}
      >
        Primitive Colour Palette
      </h2>
      <p
        style={{
          color: 'var(--color-text-secondary, #656d7b)',
          fontSize: 14,
          marginBottom: 24,
        }}
      >
        Full tonal scales from <code>web/styles/_primitives.scss</code>. Where a
        value maps to an existing SCSS variable, the mapping is shown below each
        swatch.
      </p>

      <ScaleRow
        name='Slate'
        description='Neutral greys — surfaces, text, borders. Light mode uses the lower end, dark mode uses the upper end.'
        scale={slate}
      />
      <ScaleRow
        name='Purple'
        description='Brand colour — primary actions, links, focus rings.'
        scale={purple}
      />
      <ScaleRow
        name='Red'
        description='Danger / destructive actions.'
        scale={red}
      />
      <ScaleRow
        name='Green'
        description='Success / positive feedback.'
        scale={green}
      />
      <ScaleRow
        name='Gold'
        description='Secondary accent — tertiary buttons, highlights.'
        scale={gold}
      />
      <ScaleRow name='Blue' description='Informational.' scale={blue} />
      <ScaleRow name='Orange' description='Warnings.' scale={orange} />
    </div>
  ),
}
