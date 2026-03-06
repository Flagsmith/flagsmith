import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ButtonVariant = {
  className: string
  label: string
  description: string
  /** True when the .dark block in _buttons.scss has no override for this variant */
  noDarkOverride?: boolean
  noDarkReason?: string
  /** True for icon-only buttons that need a fixed size container */
  iconOnly?: boolean
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

/**
 * All button variants drawn from web/styles/project/_buttons.scss.
 *
 * Dark mode coverage analysis (from the `.dark .btn` block, lines 432-563):
 *   btn-primary        — covered via base .btn :hover/:active rules
 *   btn-secondary      — covered (.btn.btn-secondary block, line 453)
 *   btn-icon           — covered (.btn.btn-icon block, line 441)
 *   btn--outline       — covered (.btn--outline block, line 473)
 *   btn--outline-danger — covered (.btn--outline-danger block, line 489)
 *   btn--with-icon     — covered (.btn--with-icon block, line 494)
 *   btn-with-icon      — covered (.btn.btn-with-icon block, line 553)
 *   btn-project        — covered (.btn-project block, line 526)
 *
 *   btn-tertiary       — NO .dark override (uses $secondary500 yellow in both modes)
 *   btn-danger         — NO .dark override (relies on Bootstrap's base danger colour)
 *   btn--transparent   — NO .dark override (hover stays rgba(0,0,0,0.1) — invisible on dark bg)
 */
const variants: ButtonVariant[] = [
  {
    className: 'btn btn-primary',
    description:
      'Primary action. Purple ($primary: #6837fc). Dark override: hover → $primary400.',
    label: 'btn-primary',
  },
  {
    className: 'btn btn-secondary',
    description:
      'Secondary action. Background: $basic-alpha-8 (light) / $white-alpha-8 (dark). Text adapts.',
    label: 'btn-secondary',
  },
  {
    className: 'btn btn-tertiary',
    description:
      'Tertiary / accent. Background: $secondary500 (#F7D56E yellow). Text: $primary900 (#1E0D26).',
    label: 'btn-tertiary',
    noDarkOverride: true,
    noDarkReason:
      'No .dark override — background stays yellow (#F7D56E) and text stays $primary900 (#1E0D26) in dark mode. Yellow on dark works visually but the hover colour ($secondary600) is not re-specified under .dark.',
  },
  {
    className: 'btn btn-danger',
    description:
      'Destructive action. Background: Bootstrap $danger / $ef4d56. Hover: $btn-danger-hover (#cd384d).',
    label: 'btn-danger',
    noDarkOverride: true,
    noDarkReason:
      'No .dark override — hover/active colours (#cd384d, #ac2646) are hardcoded and not adjusted for the dark surface.',
  },
  {
    className: 'btn btn--outline',
    description:
      'Outline variant of primary. Border + text: $primary (#6837fc). Dark: border/text shift to $primary400.',
    label: 'btn--outline',
  },
  {
    className: 'btn btn--outline btn--outline-danger',
    description:
      'Outline variant for destructive actions. Border + text: $danger (#ef4d56). Dark: $danger400 (#f57c78).',
    label: 'btn--outline-danger',
  },
  {
    className: 'btn btn--transparent',
    description:
      'Icon-only transparent button. 38×38 px. Hover: rgba(0,0,0,0.1). Used for toolbar/nav actions.',
    iconOnly: true,
    label: 'btn--transparent',
    noDarkOverride: true,
    noDarkReason:
      'No .dark override — hover is rgba(0,0,0,0.1), which is nearly invisible on the dark background ($bg-dark500: #101628). Should be rgba(255,255,255,0.1) or a $white-alpha-* token in dark mode.',
  },
  {
    className: 'btn btn-with-icon',
    description:
      'Button with an icon + text. Background: $basic-alpha-8. Dark: same token. SVG path fill swaps to $primary on hover.',
    label: 'btn-with-icon',
  },
  {
    className: 'btn btn-icon',
    description:
      'Square icon-only button. 32×32 px. Hover: $bg-light300 (light) / $bg-dark300 (dark).',
    iconOnly: true,
    label: 'btn-icon',
  },
]

/** Variants that have no .dark block override in _buttons.scss */
const noDarkOverrideVariants = variants.filter((v) => v.noDarkOverride)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Inline SVG used to give icon-only buttons visible content */
const PlaceholderSvg = () => (
  <svg
    xmlns='http://www.w3.org/2000/svg'
    width={18}
    height={18}
    viewBox='0 0 24 24'
    fill='none'
    stroke='currentColor'
    strokeWidth={2}
    strokeLinecap='round'
    strokeLinejoin='round'
  >
    <circle cx={12} cy={12} r={9} />
    <line x1={12} y1={8} x2={12} y2={12} />
    <line x1={12} y1={16} x2={12} y2={16} />
  </svg>
)

type ButtonRowProps = {
  variant: ButtonVariant
  /** Wrap in a red-bordered gap indicator */
  highlightGap?: boolean
}

const ButtonRow: React.FC<ButtonRowProps> = ({ highlightGap, variant }) => {
  const { className, description, iconOnly, label, noDarkReason } = variant

  const buttonContent = iconOnly ? <PlaceholderSvg /> : label

  const row = (
    <div
      style={{
        alignItems: 'center',
        borderBottom: '1px solid var(--colorStrokeStandard)',
        display: 'grid',
        gap: 16,
        gridTemplateColumns: '200px 120px 120px 120px 1fr',
        padding: '12px 0',
      }}
    >
      {/* Variant name */}
      <code
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 12,
          wordBreak: 'break-all',
        }}
      >
        {label}
      </code>

      {/* Default state */}
      <div>
        <button className={className} type='button'>
          {buttonContent}
        </button>
      </div>

      {/* Hover note — we describe it rather than simulate, as CSS :hover cannot be forced */}
      <div
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 11,
          fontStyle: 'italic',
        }}
      >
        Hover via CSS
        <br />
        (see description)
      </div>

      {/* Disabled state */}
      <div>
        <button className={className} type='button' disabled>
          {buttonContent}
        </button>
      </div>

      {/* Description */}
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 12,
          lineHeight: 1.5,
          margin: 0,
        }}
      >
        {description}
      </p>
    </div>
  )

  if (highlightGap) {
    return (
      <div
        style={{
          background: 'rgba(239,77,86,0.04)',
          border: '2px solid #ef4d56',
          borderRadius: 6,
          marginBottom: 8,
          padding: '0 12px',
        }}
      >
        <div
          style={{
            alignItems: 'center',
            display: 'flex',
            gap: 8,
            padding: '6px 0 2px',
          }}
        >
          <span
            style={{
              color: '#ef4d56',
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            No .dark override
          </span>
        </div>
        {row}
        {noDarkReason && (
          <p
            style={{
              color: '#ef4d56',
              fontSize: 11,
              lineHeight: 1.5,
              margin: '4px 0 8px',
            }}
          >
            {noDarkReason}
          </p>
        )}
      </div>
    )
  }

  return row
}

// ---------------------------------------------------------------------------
// Meta
// ---------------------------------------------------------------------------

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Buttons',
}
export default meta

// ---------------------------------------------------------------------------
// Stories
// ---------------------------------------------------------------------------

export const AllVariants: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 1100 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Button Variants ({variants.length})
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 16,
        }}
      >
        Source: <code>web/styles/project/_buttons.scss</code>. All variants use
        raw HTML <code>&lt;button&gt;</code> elements with Bootstrap/project CSS
        classes — there is no React Button component. Toggle dark mode in the
        Storybook toolbar to see how each variant responds.
      </p>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
        <div style={{ alignItems: 'center', display: 'flex', gap: 6 }}>
          <span
            style={{
              border: '2px solid #ef4d56',
              borderRadius: 2,
              display: 'inline-block',
              height: 12,
              width: 12,
            }}
          />
          <span style={{ color: 'var(--colorTextSecondary)', fontSize: 12 }}>
            No <code>.dark</code> override in <code>_buttons.scss</code>
          </span>
        </div>
      </div>

      {/* Column headers */}
      <div
        style={{
          borderBottom: '2px solid var(--colorStrokeStandard)',
          display: 'grid',
          gap: 16,
          gridTemplateColumns: '200px 120px 120px 120px 1fr',
          paddingBottom: 8,
        }}
      >
        {['Variant', 'Default', 'Hover', 'Disabled', 'Notes'].map((h) => (
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

      {/* Rows */}
      <div>
        {variants.map((variant) => (
          <ButtonRow
            key={variant.label}
            variant={variant}
            highlightGap={variant.noDarkOverride}
          />
        ))}
      </div>
    </div>
  ),
}

export const DarkModeGaps: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Dark Mode Gaps ({noDarkOverrideVariants.length} variants)
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 8,
        }}
      >
        These button variants have <strong>no override rules</strong> inside the{' '}
        <code>.dark .btn</code> block in{' '}
        <code>web/styles/project/_buttons.scss</code> (lines 432–563). Each one
        either looks wrong in dark mode or relies on accident rather than
        intention.
      </p>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 24,
        }}
      >
        Enable dark mode via the Storybook toolbar (moon icon) to see the issues
        live.
      </p>

      {noDarkOverrideVariants.map((variant) => {
        const buttonContent = variant.iconOnly ? (
          <PlaceholderSvg />
        ) : (
          variant.label
        )

        return (
          <div
            key={variant.label}
            style={{
              background: 'rgba(239,77,86,0.04)',
              border: '2px solid #ef4d56',
              borderRadius: 8,
              marginBottom: 24,
              padding: 16,
            }}
          >
            {/* Header */}
            <div
              style={{
                alignItems: 'center',
                display: 'flex',
                gap: 12,
                marginBottom: 12,
              }}
            >
              <span
                style={{
                  background: 'rgba(239,77,86,0.12)',
                  borderRadius: 4,
                  color: '#ef4d56',
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                  padding: '2px 8px',
                  textTransform: 'uppercase',
                }}
              >
                No .dark override
              </span>
              <code
                style={{
                  color: 'var(--colorTextStandard)',
                  fontSize: 14,
                  fontWeight: 600,
                }}
              >
                {variant.label}
              </code>
            </div>

            {/* Button states side by side */}
            <div
              style={{
                alignItems: 'center',
                display: 'flex',
                gap: 16,
                marginBottom: 12,
              }}
            >
              <div>
                <div
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 10,
                    letterSpacing: '0.06em',
                    marginBottom: 6,
                    textTransform: 'uppercase',
                  }}
                >
                  Default
                </div>
                <button className={variant.className} type='button'>
                  {buttonContent}
                </button>
              </div>
              <div>
                <div
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 10,
                    letterSpacing: '0.06em',
                    marginBottom: 6,
                    textTransform: 'uppercase',
                  }}
                >
                  Disabled
                </div>
                <button className={variant.className} type='button' disabled>
                  {buttonContent}
                </button>
              </div>
            </div>

            {/* Issue description */}
            <p
              style={{
                color: 'var(--colorTextSecondary)',
                fontSize: 13,
                lineHeight: 1.6,
                margin: '0 0 8px',
              }}
            >
              {variant.description}
            </p>

            {/* Dark mode specific callout */}
            {variant.noDarkReason && (
              <div
                style={{
                  borderLeft: '3px solid #ef4d56',
                  marginTop: 8,
                  paddingLeft: 12,
                }}
              >
                <p
                  style={{
                    color: '#ef4d56',
                    fontSize: 12,
                    lineHeight: 1.6,
                    margin: 0,
                  }}
                >
                  <strong>Dark mode issue:</strong> {variant.noDarkReason}
                </p>
              </div>
            )}
          </div>
        )
      })}

      {/* Summary table */}
      <h3
        style={{
          color: 'var(--colorTextHeading)',
          marginBottom: 12,
          marginTop: 32,
        }}
      >
        Recommended fixes
      </h3>
      <table
        style={{ borderCollapse: 'collapse', fontSize: 13, width: '100%' }}
      >
        <thead>
          <tr style={{ borderBottom: '2px solid var(--colorStrokeStandard)' }}>
            {['Variant', 'Issue', 'Fix'].map((h) => (
              <th
                key={h}
                style={{
                  color: 'var(--colorTextSecondary)',
                  fontWeight: 700,
                  padding: '8px 12px',
                  textAlign: 'left',
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {[
            [
              'btn-tertiary',
              'Yellow (#F7D56E) background unchanged in dark mode; hover colour not re-specified.',
              'Add .dark .btn.btn-tertiary { background-color: $btn-tertiary-bg-dark ($secondary600); } and re-specify hover.',
            ],
            [
              'btn-danger',
              'Hover (#cd384d) and active (#ac2646) colours are hardcoded light-mode values; no dark adjustment.',
              'Add .dark .btn.btn-danger { &:hover, &:focus { background-color: $danger400; } } to use the lighter danger shade.',
            ],
            [
              'btn--transparent',
              'Hover is rgba(0,0,0,0.1) — nearly invisible on the dark background (#101628).',
              'Add .dark .btn.btn--transparent { &:hover { background-color: $white-alpha-8; } }',
            ],
          ].map(([variant, issue, fix]) => (
            <tr
              key={variant as string}
              style={{ borderBottom: '1px solid var(--colorStrokeStandard)' }}
            >
              <td
                style={{
                  color: 'var(--colorTextStandard)',
                  fontWeight: 600,
                  padding: '8px 12px',
                }}
              >
                <code>{variant}</code>
              </td>
              <td
                style={{
                  color: 'var(--colorTextSecondary)',
                  padding: '8px 12px',
                }}
              >
                {issue}
              </td>
              <td
                style={{
                  color: 'var(--colorTextSecondary)',
                  padding: '8px 12px',
                }}
              >
                {fix}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ),
}

export const SizeVariants: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 800 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Size Variants
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 24,
        }}
      >
        Button sizes are controlled by modifier classes. Heights and
        line-heights come from <code>_variables.scss</code>. Shown here with{' '}
        <code>btn-primary</code> and <code>btn-secondary</code> for contrast.
      </p>

      {[
        { height: '56px', label: 'btn-lg', modifier: 'btn-lg' },
        { height: '44px', label: '(default)', modifier: '' },
        { height: '40px', label: 'btn-sm', modifier: 'btn-sm' },
        { height: '32px', label: 'btn-xsm', modifier: 'btn-xsm' },
        { height: '24px', label: 'btn-xxsm', modifier: 'btn-xxsm' },
      ].map(({ height, label, modifier }) => (
        <div
          key={label}
          style={{
            alignItems: 'center',
            borderBottom: '1px solid var(--colorStrokeStandard)',
            display: 'flex',
            gap: 16,
            padding: '12px 0',
          }}
        >
          <code
            style={{
              color: 'var(--colorTextSecondary)',
              fontSize: 12,
              minWidth: 100,
            }}
          >
            {label}
          </code>
          <span
            style={{
              color: 'var(--colorTextSecondary)',
              fontSize: 11,
              minWidth: 60,
            }}
          >
            h={height}
          </span>
          <button
            className={`btn btn-primary${modifier ? ` ${modifier}` : ''}`}
            type='button'
          >
            Primary
          </button>
          <button
            className={`btn btn-secondary${modifier ? ` ${modifier}` : ''}`}
            type='button'
          >
            Secondary
          </button>
        </div>
      ))}
    </div>
  ),
}
