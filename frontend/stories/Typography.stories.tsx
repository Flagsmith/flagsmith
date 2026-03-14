import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'

// ---------------------------------------------------------------------------
// Meta
// ---------------------------------------------------------------------------

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Typography',
}
export default meta

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

function getA11yBackground(a11y: string): string {
  if (a11y.startsWith('Accessible')) return 'rgba(39, 171, 149, 0.1)'
  if (a11y.startsWith('Fails')) return 'rgba(239, 77, 86, 0.1)'
  return 'rgba(255, 159, 67, 0.1)'
}

function getA11yColour(a11y: string): string {
  if (a11y.startsWith('Accessible')) return '#27ab95'
  if (a11y.startsWith('Fails')) return '#ef4d56'
  return '#ff9f43'
}

const SectionHeading: React.FC<{ title: string; subtitle?: string }> = ({
  subtitle,
  title,
}) => (
  <div style={{ marginBottom: 24 }}>
    <h2
      style={{
        color: 'var(--colorTextHeading)',
        fontSize: 22,
        fontWeight: 700,
        margin: '0 0 4px',
      }}
    >
      {title}
    </h2>
    {subtitle && (
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 13,
          lineHeight: 1.5,
          margin: 0,
        }}
      >
        {subtitle}
      </p>
    )}
  </div>
)

const Divider: React.FC = () => (
  <hr
    style={{
      border: 'none',
      borderTop: '1px solid var(--colorStrokeStandard)',
      margin: '32px 0',
    }}
  />
)

const SpecBadge: React.FC<{ label: string }> = ({ label }) => (
  <code
    style={{
      background: 'rgba(101,109,123,0.08)',
      borderRadius: 4,
      color: 'var(--colorTextSecondary)',
      fontSize: 11,
      marginRight: 4,
      padding: '2px 6px',
    }}
  >
    {label}
  </code>
)

// ---------------------------------------------------------------------------
// TypeScale story
// ---------------------------------------------------------------------------

const headingLevels = [
  { lineHeight: 46, size: 42, tag: 'h1', weight: 700 },
  { lineHeight: 40, size: 34, tag: 'h2', weight: 700 },
  { lineHeight: 40, size: 30, tag: 'h3', weight: 700 },
  { lineHeight: 32, size: 24, tag: 'h4', weight: 700 },
  { lineHeight: 28, size: 18, tag: 'h5', weight: 700 },
  { lineHeight: 24, size: 16, tag: 'h6', weight: 700 },
] as const

const bodyLevels = [
  { label: 'Body', lineHeight: 20, scssVar: '$font-size-base', size: 14 },
  { label: 'Caption', lineHeight: 20, scssVar: '$font-caption', size: 13 },
  {
    label: 'Caption SM',
    lineHeight: 18,
    scssVar: '$font-caption-sm',
    size: 12,
  },
  {
    label: 'Caption XS',
    lineHeight: 16,
    scssVar: '$font-caption-xs',
    size: 11,
  },
] as const

export const TypeScale: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 900 }}>
      <SectionHeading
        title='Type Scale'
        subtitle='Heading levels h1–h6 defined in web/styles/project/_variables.scss. Body sizes come from $font-size-base, $font-caption, $font-caption-sm, and $font-caption-xs.'
      />

      {/* Headings */}
      <h3
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.08em',
          margin: '0 0 16px',
          textTransform: 'uppercase',
        }}
      >
        Headings
      </h3>

      {headingLevels.map(({ lineHeight, size, tag, weight }) => {
        const Tag = tag as keyof JSX.IntrinsicElements
        return (
          <div
            key={tag}
            style={{
              alignItems: 'baseline',
              borderBottom: '1px solid var(--colorStrokeStandard)',
              display: 'flex',
              gap: 20,
              padding: '12px 0',
            }}
          >
            {/* Tag label */}
            <code
              style={{
                color: 'var(--colorTextSecondary)',
                flexShrink: 0,
                fontSize: 11,
                minWidth: 28,
              }}
            >
              {tag}
            </code>

            {/* Spec badges */}
            <div
              style={{
                alignItems: 'center',
                display: 'flex',
                flexShrink: 0,
                gap: 4,
                minWidth: 200,
              }}
            >
              <SpecBadge label={`${size}px`} />
              <SpecBadge label={`lh ${lineHeight}px`} />
              <SpecBadge label={`w${weight}`} />
            </div>

            {/* Live element — picks up project CSS */}
            <Tag style={{ color: 'var(--colorTextStandard)', margin: 0 }}>
              The quick brown fox
            </Tag>
          </div>
        )
      })}

      <Divider />

      {/* Body */}
      <h3
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.08em',
          margin: '0 0 16px',
          textTransform: 'uppercase',
        }}
      >
        Body sizes
      </h3>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 12,
          lineHeight: 1.5,
          marginBottom: 16,
        }}
      >
        There are no CSS classes for body sizes — they are set via SCSS
        variables only. Rendered here with matching inline styles so you can see
        the scale.
      </p>

      {bodyLevels.map(({ label, lineHeight, scssVar, size }) => (
        <div
          key={label}
          style={{
            alignItems: 'baseline',
            borderBottom: '1px solid var(--colorStrokeStandard)',
            display: 'flex',
            gap: 20,
            padding: '10px 0',
          }}
        >
          {/* Label */}
          <div style={{ flexShrink: 0, minWidth: 90 }}>
            <div
              style={{
                color: 'var(--colorTextSecondary)',
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              {label}
            </div>
            <code style={{ color: 'var(--colorTextSecondary)', fontSize: 10 }}>
              {scssVar}
            </code>
          </div>

          {/* Spec badges */}
          <div
            style={{
              alignItems: 'center',
              display: 'flex',
              flexShrink: 0,
              gap: 4,
              minWidth: 160,
            }}
          >
            <SpecBadge label={`${size}px`} />
            <SpecBadge label={`lh ${lineHeight}px`} />
          </div>

          {/* Live sample */}
          <span
            style={{
              color: 'var(--colorTextStandard)',
              fontSize: size,
              lineHeight: `${lineHeight}px`,
            }}
          >
            The quick brown fox jumps over the lazy dog
          </span>
        </div>
      ))}
    </div>
  ),
}

// ---------------------------------------------------------------------------
// HardcodedFontSizes story
// ---------------------------------------------------------------------------

type HardcodedGroup = {
  value: string | number
  count: number
  files: string[]
}

const hardcodedGroups: HardcodedGroup[] = [
  {
    count: 17,
    files: [
      'IntegrationAdoptionTable',
      'ReleasePipelineStatsTable',
      'various admin components',
    ],
    value: 13,
  },
  {
    count: 12,
    files: ['Labels', 'captions', 'badges across many components'],
    value: 12,
  },
  {
    count: 7,
    files: ['TableFilter', 'TableFilterOptions', 'small labels'],
    value: 11,
  },
  {
    count: 1,
    files: ['Icon labels in stories'],
    value: 10,
  },
  {
    count: 1,
    files: ['IonIcon in CreateRole'],
    value: 16,
  },
  {
    count: 1,
    files: ['Scattered'],
    value: '18px',
  },
  {
    count: 1,
    files: ['Scattered'],
    value: '14px',
  },
  {
    count: 3,
    files: ['Scattered'],
    value: '13px',
  },
  {
    count: 2,
    files: ['Scattered'],
    value: '12px',
  },
  {
    count: 1,
    files: ['Scattered'],
    value: '0.875rem',
  },
]

const totalHardcoded = hardcodedGroups.reduce((acc, g) => acc + g.count, 0)

const CountBadge: React.FC<{ count: number }> = ({ count }) => (
  <span
    style={{
      alignItems: 'center',
      background: '#ef4d56',
      borderRadius: 10,
      color: '#fff',
      display: 'inline-flex',
      flexShrink: 0,
      fontSize: 11,
      fontWeight: 700,
      height: 20,
      justifyContent: 'center',
      minWidth: 24,
      padding: '0 6px',
    }}
  >
    {count}
  </span>
)

export const HardcodedFontSizes: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 900 }}>
      <SectionHeading
        title='Hardcoded Font Sizes'
        subtitle='Visual audit of inline fontSize values in TSX files. Grouped by pixel value.'
      />

      {/* Summary callout */}
      <div
        style={{
          alignItems: 'flex-start',
          background: 'rgba(239,77,86,0.04)',
          border: '2px solid #ef4d56',
          borderRadius: 8,
          display: 'flex',
          gap: 12,
          marginBottom: 32,
          padding: 16,
        }}
      >
        <span
          style={{
            flexShrink: 0,
            fontSize: 20,
            lineHeight: 1,
            marginTop: 2,
          }}
          aria-hidden='true'
        >
          !
        </span>
        <div>
          <strong
            style={{
              color: '#ef4d56',
              display: 'block',
              fontSize: 14,
              marginBottom: 4,
            }}
          >
            {totalHardcoded} inline fontSize values bypass the type scale.
          </strong>
          <span
            style={{
              color: 'var(--colorTextSecondary)',
              fontSize: 13,
              lineHeight: 1.5,
            }}
          >
            These should use typography tokens instead. Each hardcoded value
            creates drift between components and makes future type-scale changes
            labour-intensive.
          </span>
        </div>
      </div>

      {/* Column headers */}
      <div
        style={{
          borderBottom: '2px solid var(--colorStrokeStandard)',
          display: 'grid',
          gap: 12,
          gridTemplateColumns: '110px 52px 1fr 200px',
          marginBottom: 8,
          paddingBottom: 8,
        }}
      >
        {['Value', 'Count', 'Sample', 'Files'].map((h) => (
          <span
            key={h}
            style={{
              color: 'var(--colorTextSecondary)',
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            {h}
          </span>
        ))}
      </div>

      {hardcodedGroups.map((group) => {
        const numericSize =
          typeof group.value === 'number'
            ? group.value
            : parseFloat(group.value as string) *
              (String(group.value).endsWith('rem') ? 16 : 1)

        return (
          <div
            key={String(group.value)}
            style={{
              alignItems: 'center',
              borderBottom: '1px solid var(--colorStrokeStandard)',
              display: 'grid',
              gap: 12,
              gridTemplateColumns: '110px 52px 1fr 200px',
              padding: '10px 0',
            }}
          >
            {/* Value */}
            <code
              style={{
                color: 'var(--colorTextStandard)',
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              {`fontSize: ${
                typeof group.value === 'string'
                  ? `'${group.value}'`
                  : group.value
              }`}
            </code>

            {/* Count badge */}
            <div>
              <CountBadge count={group.count} />
            </div>

            {/* Sample — rendered at the actual size with audit border */}
            <div
              style={{
                border: '1px solid #ef4d56',
                borderRadius: 4,
                display: 'inline-block',
                maxWidth: 360,
                padding: '4px 10px',
              }}
            >
              <span
                style={{
                  color: 'var(--colorTextStandard)',
                  fontSize: numericSize,
                  lineHeight: 1.4,
                }}
              >
                Sample text at {group.value}
              </span>
            </div>

            {/* Files */}
            <div>
              {group.files.map((f) => (
                <div
                  key={f}
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 11,
                    lineHeight: 1.6,
                  }}
                >
                  {f}
                </div>
              ))}
            </div>
          </div>
        )
      })}

      {/* Legend */}
      <div
        style={{
          alignItems: 'center',
          display: 'flex',
          gap: 8,
          marginTop: 16,
        }}
      >
        <div
          style={{
            border: '1px solid #ef4d56',
            borderRadius: 2,
            flexShrink: 0,
            height: 12,
            width: 12,
          }}
        />
        <span style={{ color: 'var(--colorTextSecondary)', fontSize: 12 }}>
          Red border = sample rendered at the hardcoded size
        </span>
      </div>
    </div>
  ),
}

// ---------------------------------------------------------------------------
// WeightAndStyleUsage story
// ---------------------------------------------------------------------------

const weightTiers = [
  {
    classes: 'fw-bold, .bold-link',
    label: 'Bold',
    occurrences: '~14 in SCSS',
    scssVar: '$btn-font-weight',
    usage: 'Headings (h1–h6), buttons, badges',
    value: 700,
  },
  {
    classes: 'fw-semibold',
    label: 'Semibold',
    occurrences: '~3 in SCSS, 3 inline in TSX',
    scssVar: '$tab-btn-active-font-weight',
    usage: 'Active tab states, admin dashboard tables',
    value: 600,
  },
  {
    classes: '.font-weight-medium, fw-normal (sometimes)',
    label: 'Medium',
    occurrences: '~33 in SCSS, 1 inline in TSX',
    scssVar: '$input-font-weight',
    usage: 'Body text, inputs, alerts, tabs, links — most common weight',
    value: 500,
  },
  {
    classes: 'fw-normal',
    label: 'Regular',
    occurrences: '~5 in SCSS, 1 inline in TSX',
    scssVar: '(none)',
    usage: 'Secondary/muted text, placeholders, dividers',
    value: 400,
  },
]

const mutedTextPatterns = [
  {
    a11y: 'Accessible',
    method: 'Colour-based',
    pattern: '$text-muted / .text-muted',
    value: '#656D7B',
  },
  {
    a11y: 'Accessible',
    method: 'Colour + size',
    pattern: '.faint',
    value: '$text-muted + 0.8em',
  },
  {
    a11y: 'Risky — depends on bg',
    method: 'Opacity',
    pattern: 'opacity: 0.6',
    value: '60% transparency',
  },
  {
    a11y: 'Risky — low contrast',
    method: 'Opacity',
    pattern: 'opacity: 0.5',
    value: '50% transparency',
  },
  {
    a11y: 'Fails WCAG AA',
    method: 'Opacity',
    pattern: 'opacity: 0.4',
    value: '40% transparency',
  },
  {
    a11y: 'Intentional (disabled)',
    method: 'Opacity',
    pattern: '$btn-disabled-opacity (0.32)',
    value: '32% transparency',
  },
]

const bugs = [
  {
    code: "fontWeight: 'semi-bold'",
    file: 'web/components/messages/SuccessMessage.tsx',
    fix: 'fontWeight: 600',
    issue:
      'Invalid CSS — "semi-bold" is not a valid fontWeight value. Browser ignores it.',
  },
  {
    code: "fontWeight: 'semi-bold'",
    file: 'web/components/SuccessMessage.js',
    fix: 'fontWeight: 600',
    issue: 'Same bug, duplicate file (JS version of the above).',
  },
]

export const WeightAndStyleUsage: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
      <SectionHeading
        title='Font Weight & Style Usage'
        subtitle='Audit of how font weights, styles, and "subtle" text patterns are actually used across the codebase. 71 font-weight declarations in SCSS, 9 inline in TSX.'
      />

      {/* Weight tiers */}
      <h3
        style={{
          color: 'var(--colorTextHeading)',
          fontSize: 16,
          fontWeight: 700,
          marginBottom: 12,
        }}
      >
        Weight Tiers in Use
      </h3>
      <table
        style={{ borderCollapse: 'collapse', marginBottom: 32, width: '100%' }}
      >
        <thead>
          <tr style={{ borderBottom: '2px solid var(--colorStrokeStandard)' }}>
            {['Weight', 'Sample', 'SCSS variable', 'CSS classes', 'Usage'].map(
              (h) => (
                <th
                  key={h}
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: '0.06em',
                    padding: '8px 8px 10px 0',
                    textAlign: 'left',
                    textTransform: 'uppercase',
                  }}
                >
                  {h}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody>
          {weightTiers.map((tier) => (
            <tr
              key={tier.value}
              style={{ borderBottom: '1px solid var(--colorStrokeStandard)' }}
            >
              <td style={{ padding: '10px 8px 10px 0' }}>
                <SpecBadge label={`${tier.value}`} />
                <span
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 11,
                    marginLeft: 6,
                  }}
                >
                  {tier.label}
                </span>
              </td>
              <td style={{ padding: '10px 8px' }}>
                <span
                  style={{
                    color: 'var(--colorTextStandard)',
                    fontSize: 14,
                    fontWeight: tier.value,
                  }}
                >
                  The quick brown fox
                </span>
              </td>
              <td style={{ padding: '10px 8px' }}>
                <code
                  style={{ color: 'var(--colorTextSecondary)', fontSize: 11 }}
                >
                  {tier.scssVar}
                </code>
              </td>
              <td style={{ padding: '10px 8px' }}>
                <code
                  style={{ color: 'var(--colorTextSecondary)', fontSize: 11 }}
                >
                  {tier.classes}
                </code>
              </td>
              <td
                style={{
                  color: 'var(--colorTextSecondary)',
                  fontSize: 12,
                  padding: '10px 8px',
                }}
              >
                {tier.usage}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Inconsistency callout */}
      <div
        style={{
          background: 'rgba(255, 159, 67, 0.06)',
          border: '2px solid #ff9f43',
          borderRadius: 8,
          marginBottom: 32,
          padding: 16,
        }}
      >
        <strong style={{ color: 'var(--colorTextStandard)', fontSize: 13 }}>
          Inconsistency: Two class systems in use
        </strong>
        <p
          style={{
            color: 'var(--colorTextSecondary)',
            fontSize: 12,
            margin: '8px 0 0',
          }}
        >
          Custom class <code>.font-weight-medium</code> (500) competes with
          Bootstrap utilities <code>fw-bold</code> (18 uses),{' '}
          <code>fw-semibold</code> (16 uses), <code>fw-normal</code> (32 uses).
          Components pick whichever they find first. Should standardise on one
          system.
        </p>
      </div>

      <Divider />

      {/* Muted text patterns */}
      <h3
        style={{
          color: 'var(--colorTextHeading)',
          fontSize: 16,
          fontWeight: 700,
          marginBottom: 12,
        }}
      >
        &quot;Subtle&quot; / Muted Text Patterns
      </h3>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 13,
          marginBottom: 16,
        }}
      >
        Text hierarchy is achieved through both colour and opacity.
        Opacity-based patterns are an accessibility concern — the resulting
        contrast depends on the background, making it unpredictable across
        light/dark modes.
      </p>
      <table
        style={{ borderCollapse: 'collapse', marginBottom: 32, width: '100%' }}
      >
        <thead>
          <tr style={{ borderBottom: '2px solid var(--colorStrokeStandard)' }}>
            {['Pattern', 'Method', 'Value', 'Accessibility'].map((h) => (
              <th
                key={h}
                style={{
                  color: 'var(--colorTextSecondary)',
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: '0.06em',
                  padding: '8px 8px 10px 0',
                  textAlign: 'left',
                  textTransform: 'uppercase',
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {mutedTextPatterns.map((row) => (
            <tr
              key={row.pattern}
              style={{ borderBottom: '1px solid var(--colorStrokeStandard)' }}
            >
              <td style={{ padding: '10px 8px 10px 0' }}>
                <code
                  style={{ color: 'var(--colorTextStandard)', fontSize: 11 }}
                >
                  {row.pattern}
                </code>
              </td>
              <td
                style={{
                  color: 'var(--colorTextSecondary)',
                  fontSize: 12,
                  padding: '10px 8px',
                }}
              >
                {row.method}
              </td>
              <td
                style={{
                  color: 'var(--colorTextSecondary)',
                  fontSize: 12,
                  padding: '10px 8px',
                }}
              >
                {row.value}
              </td>
              <td style={{ padding: '10px 8px' }}>
                <span
                  style={{
                    background: getA11yBackground(row.a11y),
                    borderRadius: 4,
                    color: getA11yColour(row.a11y),
                    fontSize: 11,
                    fontWeight: 600,
                    padding: '2px 8px',
                  }}
                >
                  {row.a11y}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Divider />

      {/* Bugs */}
      <h3
        style={{
          color: '#ef4d56',
          fontSize: 16,
          fontWeight: 700,
          marginBottom: 12,
        }}
      >
        Bugs Found
      </h3>
      {bugs.map((bug) => (
        <div
          key={bug.file}
          style={{
            background: 'rgba(239, 77, 86, 0.04)',
            border: '2px solid #ef4d56',
            borderRadius: 8,
            marginBottom: 12,
            padding: 16,
          }}
        >
          <code
            style={{
              color: 'var(--colorTextStandard)',
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            {bug.file}
          </code>
          <div style={{ marginTop: 8 }}>
            <code style={{ color: '#ef4d56', fontSize: 12 }}>{bug.code}</code>
          </div>
          <p
            style={{
              color: 'var(--colorTextSecondary)',
              fontSize: 12,
              margin: '8px 0 0',
            }}
          >
            {bug.issue}
          </p>
          <p
            style={{
              color: 'var(--colorTextSecondary)',
              fontSize: 12,
              margin: '4px 0 0',
            }}
          >
            <strong>Fix:</strong> <code>{bug.fix}</code>
          </p>
        </div>
      ))}

      <Divider />

      {/* Other styles */}
      <h3
        style={{
          color: 'var(--colorTextHeading)',
          fontSize: 16,
          fontWeight: 700,
          marginBottom: 12,
        }}
      >
        Other Styles
      </h3>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <tbody>
          {[
            [
              'Italic',
              '2 occurrences (CodeReferenceItem, RuleConditionPropertySelect)',
              'Not a pattern — ad-hoc usage only',
            ],
            [
              'Underline',
              '4 declarations in SCSS (.link-style, a:hover, .btn-link:hover)',
              'Consistent — used for interactive text',
            ],
            [
              'text-transform: uppercase',
              '1 occurrence (.btn-project-letter)',
              'Rare — not systemic',
            ],
            [
              'text-transform: capitalize',
              '1 occurrence (.panel heading)',
              'Rare — not systemic',
            ],
            ['letter-spacing', '1 class (.letter-spacing: 1px)', 'Barely used'],
          ].map(([style, usage, note]) => (
            <tr
              key={style}
              style={{ borderBottom: '1px solid var(--colorStrokeStandard)' }}
            >
              <td
                style={{
                  color: 'var(--colorTextStandard)',
                  fontSize: 13,
                  fontWeight: 600,
                  padding: '8px 12px',
                }}
              >
                {style}
              </td>
              <td
                style={{
                  color: 'var(--colorTextSecondary)',
                  fontSize: 12,
                  padding: '8px 12px',
                }}
              >
                {usage}
              </td>
              <td
                style={{
                  color: 'var(--colorTextSecondary)',
                  fontSize: 12,
                  padding: '8px 12px',
                }}
              >
                {note}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ),
}
