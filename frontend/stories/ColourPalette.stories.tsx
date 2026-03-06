import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Colours/Palette Audit',
}
export default meta

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

const fontStack = "'OpenSans', sans-serif"

function getBadgeForLabel(
  label: string,
): { colour: string; text: string } | undefined {
  if (label === '$primary400') {
    return { colour: '#ef4d56', text: 'LIGHTER than base' }
  }
  if (label === '$primary (base)') {
    return { colour: '#27ab95', text: 'Base' }
  }
  return undefined
}

function getBadgeForSlot(
  label: string,
): { colour: string; text: string } | undefined {
  if (label === 'primary-500') {
    return { colour: '#27ab95', text: 'Existing $primary' }
  }
  if (label === 'primary-400') {
    return { colour: '#6837fc', text: 'Correct 400 slot' }
  }
  return undefined
}

const Swatch: React.FC<{
  hex: string
  label: string
  sublabel?: string
  width?: number
  height?: number
  badge?: { text: string; colour: string }
}> = ({ badge, height = 56, hex, label, sublabel, width = 56 }) => (
  <div
    style={{
      alignItems: 'center',
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
    }}
  >
    <div style={{ position: 'relative' }}>
      <div
        style={{
          background: hex,
          border: '1px solid rgba(128,128,128,0.2)',
          borderRadius: 8,
          flexShrink: 0,
          height,
          width,
        }}
      />
      {badge && (
        <div
          style={{
            background: badge.colour,
            borderRadius: 4,
            color: '#fff',
            fontSize: 9,
            fontWeight: 700,
            letterSpacing: '0.03em',
            padding: '2px 5px',
            position: 'absolute',
            right: -8,
            top: -8,
            whiteSpace: 'nowrap',
          }}
        >
          {badge.text}
        </div>
      )}
    </div>
    <div style={{ textAlign: 'center' }}>
      <div
        style={{
          color: 'var(--colorTextStandard)',
          fontSize: 11,
          fontWeight: 600,
          maxWidth: width + 16,
          wordBreak: 'break-all',
        }}
      >
        {label}
      </div>
      {sublabel && (
        <div
          style={{
            color: 'var(--colorTextSecondary)',
            fontSize: 10,
            maxWidth: width + 16,
            wordBreak: 'break-all',
          }}
        >
          {sublabel}
        </div>
      )}
    </div>
  </div>
)

const SwatchRow: React.FC<{ swatches: React.ReactNode; label?: string }> = ({
  label,
  swatches,
}) => (
  <div style={{ marginBottom: 24 }}>
    {label && (
      <div
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.07em',
          marginBottom: 10,
          textTransform: 'uppercase',
        }}
      >
        {label}
      </div>
    )}
    <div
      style={{
        alignItems: 'flex-start',
        display: 'flex',
        flexWrap: 'wrap',
        gap: 16,
      }}
    >
      {swatches}
    </div>
  </div>
)

const IssueCallout: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <div
    style={{
      background: 'rgba(239,77,86,0.08)',
      border: '1px solid rgba(239,77,86,0.32)',
      borderRadius: 8,
      color: 'var(--colorTextStandard)',
      fontSize: 13,
      lineHeight: 1.55,
      marginBottom: 20,
      padding: '10px 14px',
    }}
  >
    {children}
  </div>
)

const SectionHeading: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <h3
    style={{
      borderBottom: '1px solid rgba(128,128,128,0.18)',
      color: 'var(--colorTextStandard)',
      fontSize: 15,
      fontWeight: 700,
      marginBottom: 12,
      marginTop: 28,
      paddingBottom: 8,
    }}
  >
    {children}
  </h3>
)

// ---------------------------------------------------------------------------
// Story 1: TonalScaleInconsistency
// ---------------------------------------------------------------------------

export const TonalScaleInconsistency: StoryObj = {
  render: () => {
    const actualScale = [
      { hex: '#906af6', label: '$primary400', note: 'Lighter' },
      { hex: '#6837fc', label: '$primary (base)', note: 'Base' },
      { hex: '#4e25db', label: '$primary600', note: 'Darker' },
      { hex: '#3919b7', label: '$primary700', note: 'Darker' },
      { hex: '#2a2054', label: '$primary800', note: 'Darker' },
      { hex: '#1e0d26', label: '$primary900', note: 'Darkest' },
    ]

    // What a correct 50–900 scale would look like (illustrative, HSL-derived from #6837fc)
    const correctScale = [
      { hex: '#f0ebff', label: 'primary-50', note: 'Lightest' },
      { hex: '#ddd0ff', label: 'primary-100', note: '' },
      { hex: '#c4aaff', label: 'primary-200', note: '' },
      { hex: '#a882ff', label: 'primary-300', note: '' },
      {
        hex: '#8b5cff',
        label: 'primary-400',
        note: 'Should be darker than 300',
      },
      { hex: '#6837fc', label: 'primary-500', note: 'Base (current $primary)' },
      { hex: '#4e25db', label: 'primary-600', note: 'Matches $primary600' },
      { hex: '#3919b7', label: 'primary-700', note: 'Matches $primary700' },
      { hex: '#2a2054', label: 'primary-800', note: 'Matches $primary800' },
      { hex: '#1e0d26', label: 'primary-900', note: 'Matches $primary900' },
    ]

    return (
      <div style={{ fontFamily: fontStack, maxWidth: 900 }}>
        <h2 style={{ color: 'var(--colorTextStandard)', marginBottom: 6 }}>
          Tonal Scale Inconsistency
        </h2>
        <p
          style={{
            color: 'var(--colorTextSecondary)',
            fontSize: 13,
            lineHeight: 1.6,
            marginBottom: 20,
          }}
        >
          The convention for numbered colour scales is: higher numbers = darker
          shades. The current primary scale violates this at{' '}
          <code>$primary400</code>, which is <strong>lighter</strong> than the
          unnumbered <code>$primary</code> base. There is also no{' '}
          <code>$primary100</code>, <code>$primary200</code>, or{' '}
          <code>$primary300</code> — the scale jumps straight from 400 to the
          base, with no low-numbered light stops defined at all.
        </p>

        <IssueCallout>
          <strong>Issue:</strong> <code>$primary400</code> (#906AF6) is{' '}
          <em>lighter</em> than <code>$primary</code> (#6837FC). In a
          conventional 50–900 scale, 400 should sit below the 500-equivalent
          base, not above it. This makes the scale non-intuitive and
          error-prone: a developer reaching for a lighter variant correctly
          picks 400 and gets the wrong result.
        </IssueCallout>

        <SectionHeading>
          Current scale — as defined in _variables.scss
        </SectionHeading>
        <SwatchRow
          swatches={actualScale.map((s) => (
            <Swatch
              key={s.label}
              hex={s.hex}
              label={s.label}
              sublabel={s.hex}
              badge={getBadgeForLabel(s.label)}
            />
          ))}
        />

        <div
          style={{
            background: 'rgba(255,159,67,0.08)',
            border: '1px solid rgba(255,159,67,0.32)',
            borderRadius: 8,
            color: 'var(--colorTextSecondary)',
            fontSize: 12,
            margin: '16px 0',
            padding: '10px 14px',
          }}
        >
          Note: <code>$primary-faded</code> (#e2d4fe) is referenced in component
          code but is <strong>not defined in _variables.scss</strong>. It
          appears as an orphan hex. It would naturally belong at the primary-100
          or primary-50 level.
        </div>

        <SectionHeading>
          What a correct 50–900 scale would look like
        </SectionHeading>
        <p
          style={{
            color: 'var(--colorTextSecondary)',
            fontSize: 12,
            lineHeight: 1.5,
            marginBottom: 12,
          }}
        >
          Illustrative target — HSL-interpolated from the existing base
          (#6837FC). The 600–900 range already matches existing variables; the
          gap is the 50–400 range.
        </p>
        <SwatchRow
          swatches={correctScale.map((s) => (
            <Swatch
              key={s.label}
              hex={s.hex}
              label={s.label}
              sublabel={s.hex}
              badge={getBadgeForSlot(s.label)}
            />
          ))}
        />
      </div>
    )
  },
}

// ---------------------------------------------------------------------------
// Story 2: AlphaColourMismatches
// ---------------------------------------------------------------------------

export const AlphaColourMismatches: StoryObj = {
  render: () => {
    type AlphaEntry = {
      name: string
      solidHex: string
      solidRgb: string
      alphaBaseRgb: string
      alphaBaseHex: string
      alphaVars: Array<{ label: string; actual: string; correct: string }>
    }

    const entries: AlphaEntry[] = [
      {
        alphaBaseHex: '#956cff',
        alphaBaseRgb: '149, 108, 255',
        alphaVars: [
          {
            actual: 'rgba(149,108,255,0.08)',
            correct: 'rgba(104,55,252,0.08)',
            label: 'alfa-8',
          },
          {
            actual: 'rgba(149,108,255,0.16)',
            correct: 'rgba(104,55,252,0.16)',
            label: 'alfa-16',
          },
          {
            actual: 'rgba(149,108,255,0.24)',
            correct: 'rgba(104,55,252,0.24)',
            label: 'alfa-24',
          },
          {
            actual: 'rgba(149,108,255,0.32)',
            correct: 'rgba(104,55,252,0.32)',
            label: 'alfa-32',
          },
        ],
        name: 'Primary',
        solidHex: '#6837fc',
        solidRgb: '104, 55, 252',
      },
      {
        alphaBaseHex: '#ff424b',
        alphaBaseRgb: '255, 66, 75',
        alphaVars: [
          {
            actual: 'rgba(255,66,75,0.08)',
            correct: 'rgba(239,77,86,0.08)',
            label: 'alfa-8',
          },
          {
            actual: 'rgba(255,66,75,0.16)',
            correct: 'rgba(239,77,86,0.16)',
            label: 'alfa-16',
          },
        ],
        name: 'Danger',
        solidHex: '#ef4d56',
        solidRgb: '239, 77, 86',
      },
      {
        alphaBaseHex: '#ff9f00',
        alphaBaseRgb: '255, 159, 0',
        alphaVars: [
          {
            actual: 'rgba(255,159,0,0.08)',
            correct: 'rgba(255,159,67,0.08)',
            label: 'alfa-8',
          },
        ],
        name: 'Warning',
        solidHex: '#ff9f43',
        solidRgb: '255, 159, 67',
      },
    ]

    return (
      <div style={{ fontFamily: fontStack, maxWidth: 900 }}>
        <h2 style={{ color: 'var(--colorTextStandard)', marginBottom: 6 }}>
          Alpha Colour Mismatches
        </h2>
        <p
          style={{
            color: 'var(--colorTextSecondary)',
            fontSize: 13,
            lineHeight: 1.6,
            marginBottom: 20,
          }}
        >
          Alpha variants (e.g. <code>$primary-alfa-8</code>) should be derived
          from the same RGB values as their solid counterpart. In this codebase,
          all three checked colours use a<em>different</em> RGB base for their
          alpha variants. This causes the alpha overlays to tint differently
          from the solid colour they are meant to complement.
        </p>

        <IssueCallout>
          <strong>Issue:</strong> <code>$primary-alfa-*</code> uses RGB (149,
          108, 255) — which corresponds to <code>$primary400</code> (#956CFF),
          not <code>$primary</code> (#6837FC / 104, 55, 252). The danger and
          warning alphas similarly derive from undocumented RGB values that do
          not match their solid variables.
        </IssueCallout>

        {entries.map((entry) => (
          <div key={entry.name} style={{ marginBottom: 36 }}>
            <SectionHeading>{entry.name}</SectionHeading>

            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 32,
                marginBottom: 16,
              }}
            >
              <div>
                <div
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 11,
                    fontWeight: 600,
                    letterSpacing: '0.07em',
                    marginBottom: 8,
                    textTransform: 'uppercase',
                  }}
                >
                  Solid token
                </div>
                <Swatch
                  hex={entry.solidHex}
                  label={`$${entry.name.toLowerCase()}`}
                  sublabel={`${entry.solidHex} — rgb(${entry.solidRgb})`}
                  badge={{ colour: '#27ab95', text: 'SOLID' }}
                />
              </div>

              <div>
                <div
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 11,
                    fontWeight: 600,
                    letterSpacing: '0.07em',
                    marginBottom: 8,
                    textTransform: 'uppercase',
                  }}
                >
                  Alpha base actually used
                </div>
                <Swatch
                  hex={entry.alphaBaseHex}
                  label='Alpha RGB base'
                  sublabel={`${entry.alphaBaseHex} — rgb(${entry.alphaBaseRgb})`}
                  badge={{ colour: '#ef4d56', text: 'MISMATCH' }}
                />
              </div>
            </div>

            <div
              style={{
                color: 'var(--colorTextSecondary)',
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: '0.07em',
                marginBottom: 10,
                textTransform: 'uppercase',
              }}
            >
              Alpha variants: actual (left) vs correct (right)
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 28 }}>
              {entry.alphaVars.map((v) => (
                <div
                  key={v.label}
                  style={{
                    alignItems: 'center',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 8,
                  }}
                >
                  <div
                    style={{
                      color: 'var(--colorTextStandard)',
                      fontSize: 11,
                      fontWeight: 600,
                    }}
                  >
                    -{v.label}
                  </div>
                  <div
                    style={{ alignItems: 'center', display: 'flex', gap: 6 }}
                  >
                    <div
                      style={{
                        alignItems: 'center',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 4,
                      }}
                    >
                      <div
                        style={{
                          background: v.actual,
                          border: '1px solid rgba(239,77,86,0.35)',
                          borderRadius: 6,
                          height: 44,
                          width: 44,
                        }}
                      />
                      <div
                        style={{
                          color: '#ef4d56',
                          fontSize: 9,
                          fontWeight: 700,
                        }}
                      >
                        ACTUAL
                      </div>
                    </div>
                    <div
                      style={{
                        color: 'var(--colorTextSecondary)',
                        fontSize: 14,
                        padding: '0 2px',
                      }}
                    >
                      vs
                    </div>
                    <div
                      style={{
                        alignItems: 'center',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 4,
                      }}
                    >
                      <div
                        style={{
                          background: v.correct,
                          border: '1px solid rgba(39,171,149,0.35)',
                          borderRadius: 6,
                          height: 44,
                          width: 44,
                        }}
                      />
                      <div
                        style={{
                          color: '#27ab95',
                          fontSize: 9,
                          fontWeight: 700,
                        }}
                      >
                        CORRECT
                      </div>
                    </div>
                  </div>
                  <code
                    style={{
                      color: 'var(--colorTextSecondary)',
                      fontSize: 9,
                      maxWidth: 100,
                      textAlign: 'center',
                      wordBreak: 'break-all',
                    }}
                  >
                    {v.actual}
                  </code>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  },
}

// ---------------------------------------------------------------------------
// Story 3: OrphanHexValues
// ---------------------------------------------------------------------------

export const OrphanHexValues: StoryObj = {
  render: () => {
    type OrphanEntry = {
      hex: string
      uses: number
      description: string
      shouldMapTo: string | null
    }

    const orphans: OrphanEntry[] = [
      {
        description: 'Mid grey — most used orphan',
        hex: '#9DA4AE',
        shouldMapTo:
          '$text-icon-light-grey (rgba(157,164,174,1) ≈ same colour)',
        uses: 52,
      },
      {
        description: 'Red — not using $danger',
        hex: '#e74c3c',
        shouldMapTo: '$danger (#ef4d56)',
        uses: 8,
      },
      {
        description: 'Green — not using $success',
        hex: '#53af41',
        shouldMapTo: '$success (#27ab95)',
        uses: 5,
      },
      {
        description: 'Grey',
        hex: '#767d85',
        shouldMapTo: 'No exact match — nearest $text-icon-grey (#656d7b)',
        uses: 7,
      },
      {
        description: 'Grey-blue',
        hex: '#5D6D7E',
        shouldMapTo: 'No exact match — nearest $text-icon-grey (#656d7b)',
        uses: 4,
      },
      {
        description: 'Dark grey',
        hex: '#343a40',
        shouldMapTo: 'No exact match — nearest $body-color (#1a2634)',
        uses: 6,
      },
      {
        description: 'GitHub purple',
        hex: '#8957e5',
        shouldMapTo: 'No variable — third-party brand colour',
        uses: 3,
      },
      {
        description: 'GitHub green',
        hex: '#238636',
        shouldMapTo: 'No variable — third-party brand colour',
        uses: 3,
      },
      {
        description: 'GitHub red',
        hex: '#da3633',
        shouldMapTo: 'No variable — third-party brand colour',
        uses: 3,
      },
      {
        description: 'Navy',
        hex: '#1c2840',
        shouldMapTo: 'No exact match — nearest $bg-dark500 (#101628)',
        uses: 2,
      },
    ]

    const isThirdParty = (entry: OrphanEntry) =>
      entry.shouldMapTo?.startsWith('No variable — third-party') ?? false
    const hasNearMatch = (entry: OrphanEntry) =>
      !isThirdParty(entry) &&
      (entry.shouldMapTo?.startsWith('No exact') ?? false)
    const hasExactMap = (entry: OrphanEntry) =>
      !isThirdParty(entry) && !hasNearMatch(entry)

    const tagColour = (entry: OrphanEntry) => {
      if (isThirdParty(entry)) return '#0aaddf'
      if (hasNearMatch(entry)) return '#ff9f43'
      return '#ef4d56'
    }

    const tagLabel = (entry: OrphanEntry) => {
      if (isThirdParty(entry)) return '3rd party'
      if (hasNearMatch(entry)) return 'near match'
      return 'has variable'
    }

    return (
      <div style={{ fontFamily: fontStack, maxWidth: 900 }}>
        <h2 style={{ color: 'var(--colorTextStandard)', marginBottom: 6 }}>
          Orphan Hex Values
        </h2>
        <p
          style={{
            color: 'var(--colorTextSecondary)',
            fontSize: 13,
            lineHeight: 1.6,
            marginBottom: 20,
          }}
        >
          These hex values appear directly in component files — not referencing
          any SCSS variable or design token. They bypass the design system and
          will not respond to theme changes or future token migrations. The
          usage counts are approximate from a codebase grep.
        </p>

        <IssueCallout>
          <strong>Issue:</strong> <code>#9DA4AE</code> appears in 52 places
          across the codebase. It is visually equivalent to{' '}
          <code>$text-icon-light-grey</code> (rgba(157,164,174,1)) but is
          written as a raw hex. Any change to the grey text colour will miss
          these 52 instances. Similarly, <code>#e74c3c</code> and{' '}
          <code>#53af41</code> duplicate existing semantic variables (
          <code>$danger</code> and <code>$success</code>) without referencing
          them.
        </IssueCallout>

        <div
          style={{
            color: 'var(--colorTextSecondary)',
            display: 'flex',
            flexWrap: 'wrap',
            fontSize: 12,
            gap: 8,
            marginBottom: 20,
          }}
        >
          <span>Legend:</span>
          {[
            { colour: '#ef4d56', label: 'Has a variable — should be replaced' },
            { colour: '#ff9f43', label: 'Near match — needs review' },
            { colour: '#0aaddf', label: 'Third-party brand colour' },
          ].map(({ colour, label }) => (
            <span
              key={label}
              style={{
                alignItems: 'center',
                background: `${colour}18`,
                border: `1px solid ${colour}55`,
                borderRadius: 4,
                display: 'inline-flex',
                gap: 4,
                padding: '2px 8px',
              }}
            >
              <span
                style={{
                  background: colour,
                  borderRadius: '50%',
                  display: 'inline-block',
                  height: 8,
                  width: 8,
                }}
              />
              {label}
            </span>
          ))}
        </div>

        <div
          style={{
            display: 'grid',
            gap: 12,
            gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          }}
        >
          {orphans.map((entry) => (
            <div
              key={entry.hex}
              style={{
                alignItems: 'flex-start',
                border: '1px solid rgba(128,128,128,0.18)',
                borderRadius: 8,
                display: 'flex',
                gap: 12,
                padding: '12px 14px',
              }}
            >
              <div
                style={{
                  background: entry.hex,
                  border: '1px solid rgba(128,128,128,0.2)',
                  borderRadius: 6,
                  flexShrink: 0,
                  height: 40,
                  width: 40,
                }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    alignItems: 'center',
                    display: 'flex',
                    gap: 6,
                    marginBottom: 3,
                  }}
                >
                  <code
                    style={{
                      color: 'var(--colorTextStandard)',
                      fontSize: 12,
                      fontWeight: 700,
                    }}
                  >
                    {entry.hex}
                  </code>
                  <span
                    style={{
                      background: tagColour(entry),
                      borderRadius: 3,
                      color: '#fff',
                      fontSize: 9,
                      fontWeight: 700,
                      letterSpacing: '0.05em',
                      padding: '1px 5px',
                      textTransform: 'uppercase',
                    }}
                  >
                    {tagLabel(entry)}
                  </span>
                </div>
                <div
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 11,
                    marginBottom: 2,
                  }}
                >
                  {entry.description}
                </div>
                <div
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 10,
                    fontStyle: 'italic',
                    lineHeight: 1.4,
                  }}
                >
                  {entry.shouldMapTo ?? 'No match'}
                </div>
                <div
                  style={{
                    color: hasExactMap(entry) ? '#ef4d56' : '#ff9f43',
                    fontSize: 10,
                    fontWeight: 700,
                    marginTop: 6,
                  }}
                >
                  {entry.uses} uses in codebase
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  },
}

// ---------------------------------------------------------------------------
// Story 4: GreyScaleGaps
// ---------------------------------------------------------------------------

export const GreyScaleGaps: StoryObj = {
  render: () => {
    type GreyEntry = {
      variable: string
      hex: string
      role: string
    }

    const currentGreys: GreyEntry[] = [
      { hex: '#656d7b', role: 'Body / icon text', variable: '$text-icon-grey' },
      {
        hex: 'rgba(157,164,174,1)',
        role: 'Muted / placeholder text',
        variable: '$text-icon-light-grey',
      },
      {
        hex: '#ffffff',
        role: 'Page background (light)',
        variable: '$bg-light100',
      },
      { hex: '#fafafb', role: 'Panel background', variable: '$bg-light200' },
      {
        hex: '#eff1f4',
        role: 'Subtle surface / pills',
        variable: '$bg-light300',
      },
      {
        hex: '#e0e3e9',
        role: 'Border / divider surface',
        variable: '$bg-light500',
      },
      {
        hex: '#e7e7e7',
        role: 'Footer — no exact variable',
        variable: '$footer-grey (approx)',
      },
      {
        hex: '#2d3443',
        role: 'Dark surface (dark mode only)',
        variable: '$bg-dark100',
      },
      {
        hex: '#202839',
        role: 'Dark surface — code bg',
        variable: '$bg-dark200',
      },
      { hex: '#161d30', role: 'Dark panel secondary', variable: '$bg-dark300' },
      { hex: '#15192b', role: 'Dark panel / modal', variable: '$bg-dark400' },
      { hex: '#101628', role: 'Dark page background', variable: '$bg-dark500' },
    ]

    // A well-structured neutral 50–900 scale (illustrative target)
    const idealGreys = [
      { hex: '#f9fafb', note: '≈ $bg-light200 (#fafafb)', step: 'neutral-50' },
      { hex: '#f3f4f6', note: '≈ $bg-light300 (#eff1f4)', step: 'neutral-100' },
      { hex: '#e5e7eb', note: '≈ $bg-light500 (#e0e3e9)', step: 'neutral-200' },
      { hex: '#d1d5db', note: 'Missing — no variable', step: 'neutral-300' },
      {
        hex: '#9ca3af',
        note: '≈ $text-icon-light-grey / #9DA4AE orphan',
        step: 'neutral-400',
      },
      {
        hex: '#6b7280',
        note: '≈ $text-icon-grey (#656d7b)',
        step: 'neutral-500',
      },
      { hex: '#4b5563', note: 'Missing — no variable', step: 'neutral-600' },
      { hex: '#374151', note: 'Missing — no variable', step: 'neutral-700' },
      { hex: '#1f2937', note: '≈ $bg-dark200 (#202839)', step: 'neutral-800' },
      { hex: '#111827', note: '≈ $bg-dark500 (#101628)', step: 'neutral-900' },
    ]

    return (
      <div style={{ fontFamily: fontStack, maxWidth: 960 }}>
        <h2 style={{ color: 'var(--colorTextStandard)', marginBottom: 6 }}>
          Grey Scale Gaps
        </h2>
        <p
          style={{
            color: 'var(--colorTextSecondary)',
            fontSize: 13,
            lineHeight: 1.6,
            marginBottom: 20,
          }}
        >
          The current grey system has no systematic numbering. Greys are split
          across two naming conventions (<code>$bg-light*</code> /{' '}
          <code>$bg-dark*</code> for surfaces, and <code>$text-icon-*</code> for
          foreground) with no unified neutral scale. Light and dark backgrounds
          are defined in entirely separate variable sets with no tonal
          relationship between them. Several mid-grey values (neutral-300 to
          neutral-700) are completely absent, which is why orphan hex values
          like <code>#767d85</code> and <code>#5D6D7E</code> appear in
          components.
        </p>

        <IssueCallout>
          <strong>Issue:</strong> There is no <code>$bg-light400</code> (it
          skips from 300 to 500), the dark scale goes in the opposite direction
          (100 is the lightest dark shade, 500 the darkest), and there is no
          cross-referencing between the light and dark ends of the scale. A
          developer cannot predictably choose a surface colour by number.
        </IssueCallout>

        <SectionHeading>
          Current greys — as defined in _variables.scss
        </SectionHeading>
        <p
          style={{
            color: 'var(--colorTextSecondary)',
            fontSize: 12,
            lineHeight: 1.5,
            marginBottom: 14,
          }}
        >
          Shown lightest to darkest. Note: there is no <code>$bg-light400</code>{' '}
          step, and the dark-mode backgrounds form a completely separate set
          rather than extending the same scale.
        </p>
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 12,
            marginBottom: 32,
          }}
        >
          {currentGreys.map((g) => (
            <div
              key={g.variable}
              style={{
                alignItems: 'center',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
                width: 80,
              }}
            >
              <div
                style={{
                  background: g.hex,
                  border: '1px solid rgba(128,128,128,0.25)',
                  borderRadius: 8,
                  height: 64,
                  width: 64,
                }}
              />
              <div
                style={{
                  color: 'var(--colorTextStandard)',
                  fontSize: 9,
                  fontWeight: 600,
                  textAlign: 'center',
                  wordBreak: 'break-all',
                }}
              >
                {g.variable}
              </div>
              <div
                style={{
                  color: 'var(--colorTextSecondary)',
                  fontSize: 9,
                  textAlign: 'center',
                  wordBreak: 'break-all',
                }}
              >
                {g.hex}
              </div>
              <div
                style={{
                  color: 'var(--colorTextSecondary)',
                  fontSize: 8,
                  fontStyle: 'italic',
                  lineHeight: 1.4,
                  textAlign: 'center',
                }}
              >
                {g.role}
              </div>
            </div>
          ))}
        </div>

        <SectionHeading>
          What a proper neutral-50 through neutral-900 scale would look like
        </SectionHeading>
        <p
          style={{
            color: 'var(--colorTextSecondary)',
            fontSize: 12,
            lineHeight: 1.5,
            marginBottom: 14,
          }}
        >
          A unified scale unifies foreground and background colours into one
          progressive sequence. Existing SCSS variables map closely to several
          steps — shown in the annotations below. The gaps (300, 600, 700) are
          where orphan hex values currently fill in ad hoc.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
          {idealGreys.map((g) => {
            const isGap = g.note.startsWith('Missing')
            return (
              <div
                key={g.step}
                style={{
                  alignItems: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                  width: 80,
                }}
              >
                <div style={{ position: 'relative' }}>
                  <div
                    style={{
                      background: g.hex,
                      border: isGap
                        ? '2px dashed #ef4d56'
                        : '1px solid rgba(128,128,128,0.25)',
                      borderRadius: 8,
                      height: 64,
                      width: 64,
                    }}
                  />
                  {isGap && (
                    <div
                      style={{
                        background: '#ef4d56',
                        borderRadius: 3,
                        color: '#fff',
                        fontSize: 8,
                        fontWeight: 700,
                        letterSpacing: '0.04em',
                        padding: '2px 4px',
                        position: 'absolute',
                        right: -7,
                        top: -7,
                      }}
                    >
                      GAP
                    </div>
                  )}
                </div>
                <div
                  style={{
                    color: 'var(--colorTextStandard)',
                    fontSize: 10,
                    fontWeight: 600,
                    textAlign: 'center',
                  }}
                >
                  {g.step}
                </div>
                <div
                  style={{
                    color: 'var(--colorTextSecondary)',
                    fontSize: 9,
                    textAlign: 'center',
                    wordBreak: 'break-all',
                  }}
                >
                  {g.hex}
                </div>
                <div
                  style={{
                    color: isGap ? '#ef4d56' : 'var(--colorTextSecondary)',
                    fontSize: 8,
                    fontStyle: 'italic',
                    fontWeight: isGap ? 600 : 400,
                    lineHeight: 1.4,
                    textAlign: 'center',
                  }}
                >
                  {g.note}
                </div>
              </div>
            )
          })}
        </div>

        <div
          style={{
            background: 'rgba(10,173,223,0.08)',
            border: '1px solid rgba(10,173,223,0.32)',
            borderRadius: 8,
            color: 'var(--colorTextSecondary)',
            fontSize: 12,
            lineHeight: 1.6,
            marginTop: 24,
            padding: '10px 14px',
          }}
        >
          <strong style={{ color: 'var(--colorTextStandard)' }}>
            Recommendation:
          </strong>{' '}
          Define a single <code>$neutral-50</code> through{' '}
          <code>$neutral-900</code> scale, then alias the existing semantic
          names (<code>$text-icon-grey</code>, <code>$bg-light*</code>,{' '}
          <code>$bg-dark*</code>) as references to the appropriate steps. This
          eliminates the need for orphan hex values and makes dark-mode surface
          colours predictable by number.
        </div>
      </div>
    )
  },
}
