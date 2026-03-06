import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'

// ---------------------------------------------------------------------------
// Meta
// ---------------------------------------------------------------------------

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Dark Mode Issues',
}
export default meta

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const hardcodedColourRows = [
  {
    code: "fill='#1A2634'",
    colour: '#1A2634',
    component: 'StatItem',
    file: 'web/components/StatItem.tsx',
    issue: 'Invisible in dark mode',
    line: 43,
  },
  {
    code: "fill={checked ? '#656D7B' : '#1A2634'}",
    colour: '#1A2634',
    component: 'Switch',
    file: 'web/components/Switch.tsx',
    issue: '#1A2634 invisible in dark mode',
    line: 57,
  },
  {
    code: "fill={isOpen ? '#1A2634' : '#9DA4AE'}",
    colour: '#1A2634',
    component: 'DateSelect',
    file: 'web/components/DateSelect.tsx',
    issue: '#1A2634 invisible in dark mode',
    line: 136,
  },
  {
    code: "fill={'#1A2634'}",
    colour: '#1A2634',
    component: 'ScheduledChangesPage',
    file: 'web/components/pages/ScheduledChangesPage.tsx',
    issue: 'Invisible in dark mode',
    line: 126,
  },
  {
    code: "tick={{ fill: '#1A2634' }}",
    colour: '#1A2634',
    component: 'OrganisationUsage',
    file: 'web/components/organisation-settings/usage/OrganisationUsage.container.tsx',
    issue: 'Chart labels invisible in dark mode',
    line: 63,
  },
  {
    code: "tick={{ fill: '#1A2634' }}",
    colour: '#1A2634',
    component: 'SingleSDKLabelsChart',
    file: 'web/components/organisation-settings/usage/components/SingleSDKLabelsChart.tsx',
    issue: 'Chart labels invisible in dark mode',
    line: 62,
  },
]

// ---------------------------------------------------------------------------
// Shared styles
// ---------------------------------------------------------------------------

const tableHeaderStyle: React.CSSProperties = {
  borderBottom: '2px solid var(--colorStrokeStandard)',
  color: 'var(--colorTextSecondary)',
  fontSize: 13,
  fontWeight: 600,
  padding: '8px 12px',
  textAlign: 'left',
  whiteSpace: 'nowrap',
}

const tableCellStyle: React.CSSProperties = {
  borderBottom: '1px solid var(--colorStrokeStandard)',
  color: 'var(--colorTextStandard)',
  fontSize: 13,
  padding: '10px 12px',
  verticalAlign: 'middle',
}

const codeStyle: React.CSSProperties = {
  background: 'var(--colorSurfacePanel)',
  borderRadius: 4,
  color: 'var(--colorTextSecondary)',
  fontFamily: "'Fira Code', 'Consolas', 'Courier New', monospace",
  fontSize: 12,
  padding: '2px 6px',
  wordBreak: 'break-all',
}

const badgeStyle: React.CSSProperties = {
  background: 'rgba(239,77,86,0.12)',
  borderRadius: 4,
  color: '#EF4D56',
  display: 'inline-block',
  fontSize: 11,
  fontWeight: 700,
  padding: '2px 8px',
  whiteSpace: 'nowrap',
}

// ---------------------------------------------------------------------------
// Story 1: HardcodedColoursInComponents
// ---------------------------------------------------------------------------

export const HardcodedColoursInComponents: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 1100 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Hardcoded Colours in Components
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 20,
        }}
      >
        These components pass <code style={codeStyle}>#1A2634</code> as a
        hardcoded fill to icons or chart tick props. In dark mode the background
        is <code style={codeStyle}>#101628</code>, making the element
        effectively invisible. Each value should be replaced with a CSS custom
        property or <code style={codeStyle}>currentColor</code>.
      </p>

      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th style={tableHeaderStyle}>Component</th>
            <th style={tableHeaderStyle}>File</th>
            <th style={tableHeaderStyle}>Line</th>
            <th style={tableHeaderStyle}>Colour</th>
            <th style={tableHeaderStyle}>Code</th>
            <th style={tableHeaderStyle}>Issue</th>
            <th style={tableHeaderStyle}>Replace with</th>
          </tr>
        </thead>
        <tbody>
          {hardcodedColourRows.map((row) => (
            <tr key={`${row.component}-${row.line}`}>
              <td style={{ ...tableCellStyle, fontWeight: 700 }}>
                {row.component}
              </td>
              <td style={tableCellStyle}>
                <code style={{ ...codeStyle, fontSize: 11 }}>{row.file}</code>
              </td>
              <td style={{ ...tableCellStyle, textAlign: 'center' }}>
                <code style={codeStyle}>{row.line}</code>
              </td>
              <td style={{ ...tableCellStyle }}>
                <div style={{ alignItems: 'center', display: 'flex', gap: 8 }}>
                  <div
                    style={{
                      background: row.colour,
                      border: '1px solid rgba(128,128,128,0.3)',
                      borderRadius: 4,
                      flexShrink: 0,
                      height: 20,
                      width: 20,
                    }}
                    title={row.colour}
                  />
                  <code style={codeStyle}>{row.colour}</code>
                </div>
              </td>
              <td style={tableCellStyle}>
                <code style={codeStyle}>{row.code}</code>
              </td>
              <td style={tableCellStyle}>
                <span style={badgeStyle}>{row.issue}</span>
              </td>
              <td style={tableCellStyle}>
                <code style={{ ...codeStyle, color: '#2DA44E' }}>
                  {row.code.includes('tick')
                    ? "tick={{ fill: 'var(--colorTextStandard)' }}"
                    : "fill='currentColor'"}
                </code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ),
}

// ---------------------------------------------------------------------------
// Story 2: DarkModeImplementationPatterns
// ---------------------------------------------------------------------------

const patternBlockStyle: React.CSSProperties = {
  background: 'var(--colorSurfacePanel)',
  border: '1px solid var(--colorStrokeStandard)',
  borderRadius: 8,
  marginBottom: 24,
  padding: 20,
}

const patternTitleStyle: React.CSSProperties = {
  color: 'var(--colorTextHeading)',
  fontSize: 15,
  fontWeight: 700,
  marginBottom: 4,
  marginTop: 0,
}

const patternSubtitleStyle: React.CSSProperties = {
  color: 'var(--colorTextSecondary)',
  fontSize: 13,
  marginBottom: 12,
}

const preStyle = (borderColour: string): React.CSSProperties => ({
  background: '#0d1117',
  borderLeft: `4px solid ${borderColour}`,
  borderRadius: 6,
  color: '#e6edf3',
  fontFamily: "'Fira Code', 'Consolas', 'Courier New', monospace",
  fontSize: 13,
  lineHeight: 1.6,
  margin: '0 0 12px 0',
  overflow: 'auto',
  padding: '14px 18px',
})

const problemPillStyle: React.CSSProperties = {
  alignItems: 'center',
  background: 'rgba(239,77,86,0.12)',
  borderRadius: 20,
  color: '#EF4D56',
  display: 'inline-flex',
  fontSize: 12,
  fontWeight: 600,
  gap: 6,
  marginTop: 4,
  padding: '4px 10px',
}

const warningPillStyle: React.CSSProperties = {
  alignItems: 'center',
  background: 'rgba(255,159,67,0.12)',
  borderRadius: 20,
  color: '#FF9F43',
  display: 'inline-flex',
  fontSize: 12,
  fontWeight: 600,
  gap: 6,
  marginTop: 4,
  padding: '4px 10px',
}

const infoPillStyle: React.CSSProperties = {
  alignItems: 'center',
  background: 'rgba(10,173,223,0.12)',
  borderRadius: 20,
  color: '#0AADDF',
  display: 'inline-flex',
  fontSize: 12,
  fontWeight: 600,
  gap: 6,
  marginTop: 4,
  padding: '4px 10px',
}

export const DarkModeImplementationPatterns: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 900 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Dark Mode Implementation Patterns
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 24,
        }}
      >
        Three parallel mechanisms handle dark mode today. Each solves a
        different layer of the problem, but none covers everything — so
        components fall through the cracks.
      </p>

      {/* Pattern 1 */}
      <div style={patternBlockStyle}>
        <p style={patternTitleStyle}>
          Pattern 1 — SCSS <code>.dark</code> selectors
        </p>
        <p style={patternSubtitleStyle}>
          48 rules across 29 files. Applied by toggling the <code>.dark</code>{' '}
          class on <code>document.body</code>.
        </p>
        <pre style={preStyle('#EF4D56')}>
          <code>{`.dark .panel {
  background-color: $panel-bg-dark;
}

.dark .aside-nav {
  background: $aside-nav-bg-dark;
  border-right: 1px solid $nav-line-dark;
}`}</code>
        </pre>
        <span style={problemPillStyle}>
          Problem: compile-time only — cannot be used in inline styles or JS
          expressions
        </span>
      </div>

      {/* Pattern 2 */}
      <div style={patternBlockStyle}>
        <p style={patternTitleStyle}>
          Pattern 2 — <code>getDarkMode()</code> runtime ternaries
        </p>
        <p style={patternSubtitleStyle}>
          13 components call <code>getDarkMode()</code> to branch on colour
          values at render time.
        </p>
        <pre style={preStyle('#FF9F43')}>
          <code>{`// From Switch.tsx (line 57)
const color = getDarkMode() ? '#ffffff' : '#1A2634'

// Or inline
<Icon fill={getDarkMode() ? '#ffffff' : '#1A2634'} />

// From OrganisationUsage.container.tsx (line 63)
tick={{ fill: getDarkMode() ? '#ffffff' : '#1A2634' }}`}</code>
        </pre>
        <span style={warningPillStyle}>
          Problem: manual ternaries, easy to forget, requires re-render on theme
          change
        </span>
      </div>

      {/* Pattern 3 */}
      <div style={patternBlockStyle}>
        <p style={patternTitleStyle}>
          Pattern 3 — Bootstrap <code>data-bs-theme</code> attribute
        </p>
        <p style={patternSubtitleStyle}>
          Set on <code>document.documentElement</code> alongside the{' '}
          <code>.dark</code> class. Intended to unlock Bootstrap&apos;s built-in
          dark mode variables, but adoption is inconsistent.
        </p>
        <pre style={preStyle('#0AADDF')}>
          <code>{`// Set in theme toggle handler
document.documentElement.setAttribute('data-bs-theme', 'dark')
document.body.classList.add('dark')

// Bootstrap provides these automatically when data-bs-theme="dark":
// --bs-body-bg, --bs-body-color, --bs-border-color, etc.
// But our custom components don't use Bootstrap tokens consistently.`}</code>
        </pre>
        <span style={infoPillStyle}>
          Problem: conflicts with <code>.dark</code> class approach;
          inconsistent adoption across custom components
        </span>
      </div>

      {/* Proposed solution */}
      <div
        style={{
          ...patternBlockStyle,
          background: 'rgba(45,164,78,0.06)',
          borderColor: '#2DA44E',
        }}
      >
        <p style={{ ...patternTitleStyle, color: '#2DA44E' }}>
          Proposed solution — CSS custom properties (design tokens)
        </p>
        <p style={patternSubtitleStyle}>
          A single source of truth. The token value changes per theme;
          components never branch on theme state.
        </p>
        <pre style={preStyle('#2DA44E')}>
          <code>{`:root {
  --colorTextStandard: #1A2634;
  --colorIconStandard: #1A2634;
}

[data-bs-theme="dark"],
.dark {
  --colorTextStandard: #ffffff;
  --colorIconStandard: #ffffff;
}

/* Component just uses the token — no ternary, no getDarkMode() */
<Icon fill="var(--colorIconStandard)" />`}</code>
        </pre>
        <span
          style={{
            alignItems: 'center',
            background: 'rgba(45,164,78,0.12)',
            borderRadius: 20,
            color: '#2DA44E',
            display: 'inline-flex',
            fontSize: 12,
            fontWeight: 600,
            gap: 6,
            marginTop: 4,
            padding: '4px 10px',
          }}
        >
          Single mechanism, no runtime branching, works in SCSS and inline
          styles
        </span>
      </div>
    </div>
  ),
}

// ---------------------------------------------------------------------------
// Story 3: ThemeTokenComparison
// ---------------------------------------------------------------------------

const comparisonCardStyle = (accent: string): React.CSSProperties => ({
  background: 'var(--colorSurfacePanel)',
  border: `1px solid ${accent}`,
  borderRadius: 8,
  display: 'flex',
  flex: 1,
  flexDirection: 'column',
  gap: 12,
  minWidth: 0,
  padding: 20,
})

const comparisonHeadingStyle = (colour: string): React.CSSProperties => ({
  borderBottom: `1px solid var(--colorStrokeStandard)`,
  color: colour,
  fontSize: 14,
  fontWeight: 700,
  margin: 0,
  paddingBottom: 8,
})

export const ThemeTokenComparison: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Theme Token Comparison
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 24,
        }}
      >
        Side-by-side view of the current approach versus token-based theming.
        The goal is to remove all dark mode awareness from component code.
      </p>

      {/* Row 1: Icon fill */}
      <div style={{ marginBottom: 32 }}>
        <h3
          style={{
            color: 'var(--colorTextStandard)',
            fontSize: 14,
            fontWeight: 700,
            marginBottom: 12,
          }}
        >
          Example 1 — Icon fill colour
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20 }}>
          <div style={comparisonCardStyle('#EF4D56')}>
            <p style={comparisonHeadingStyle('#EF4D56')}>Before (current)</p>
            <pre style={{ ...preStyle('#EF4D56'), margin: 0 }}>
              <code>{`// Component has to know about dark mode
const color = getDarkMode()
  ? '#ffffff'
  : '#1A2634'

<Icon fill={color} />`}</code>
            </pre>
            <ul
              style={{
                color: 'var(--colorTextSecondary)',
                fontSize: 13,
                lineHeight: 1.7,
                margin: 0,
                paddingLeft: 18,
              }}
            >
              <li>Component coupled to theme state</li>
              <li>Re-renders needed on theme change</li>
              <li>Easy to forget one branch</li>
              <li>Raw hex values scattered across codebase</li>
            </ul>
          </div>

          <div style={comparisonCardStyle('#2DA44E')}>
            <p style={comparisonHeadingStyle('#2DA44E')}>After (with tokens)</p>
            <pre style={{ ...preStyle('#2DA44E'), margin: 0 }}>
              <code>{`// Component just uses semantic token
import { colorIconStandard }
  from 'common/theme'

<Icon fill={colorIconStandard} />

// Or directly via CSS variable
<Icon fill="var(--colorIconStandard)" />`}</code>
            </pre>
            <ul
              style={{
                color: 'var(--colorTextSecondary)',
                fontSize: 13,
                lineHeight: 1.7,
                margin: 0,
                paddingLeft: 18,
              }}
            >
              <li>Component has zero theme knowledge</li>
              <li>CSS updates the value — no re-render</li>
              <li>One token covers both light and dark</li>
              <li>Token name documents intent</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Row 2: Chart tick */}
      <div style={{ marginBottom: 32 }}>
        <h3
          style={{
            color: 'var(--colorTextStandard)',
            fontSize: 14,
            fontWeight: 700,
            marginBottom: 12,
          }}
        >
          Example 2 — Recharts tick colour
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20 }}>
          <div style={comparisonCardStyle('#EF4D56')}>
            <p style={comparisonHeadingStyle('#EF4D56')}>Before (current)</p>
            <pre style={{ ...preStyle('#EF4D56'), margin: 0 }}>
              <code>{`// OrganisationUsage.container.tsx, line 63
// Chart labels are invisible in dark mode
<YAxis
  tick={{ fill: '#1A2634' }}
/>

<XAxis
  tick={{ fill: '#1A2634' }}
/>`}</code>
            </pre>
          </div>

          <div style={comparisonCardStyle('#2DA44E')}>
            <p style={comparisonHeadingStyle('#2DA44E')}>After (with tokens)</p>
            <pre style={{ ...preStyle('#2DA44E'), margin: 0 }}>
              <code>{`// Reads computed token at render time
const textColour = getComputedStyle(
  document.documentElement
).getPropertyValue('--colorTextStandard').trim()

<YAxis
  tick={{ fill: textColour }}
/>

<XAxis
  tick={{ fill: textColour }}
/>`}</code>
            </pre>
          </div>
        </div>
      </div>

      {/* Token mapping table */}
      <div>
        <h3
          style={{
            color: 'var(--colorTextStandard)',
            fontSize: 14,
            fontWeight: 700,
            marginBottom: 12,
          }}
        >
          Proposed token mapping
        </h3>
        <table
          style={{ borderCollapse: 'collapse', fontSize: 13, width: '100%' }}
        >
          <thead>
            <tr>
              <th style={tableHeaderStyle}>Token name</th>
              <th style={tableHeaderStyle}>Light value</th>
              <th style={tableHeaderStyle}>Dark value</th>
              <th style={tableHeaderStyle}>Replaces</th>
            </tr>
          </thead>
          <tbody>
            {[
              {
                dark: '#ffffff',
                light: '#1A2634',
                replaces: "fill='#1A2634' (icons)",
                token: '--colorIconStandard',
              },
              {
                dark: '#ffffff',
                light: '#1A2634',
                replaces: "tick={{ fill: '#1A2634' }} (charts)",
                token: '--colorTextStandard',
              },
              {
                dark: '#9DA4AE',
                light: '#9DA4AE',
                replaces: "fill='#9DA4AE' (secondary icons)",
                token: '--colorIconSubtle',
              },
              {
                dark: '#656D7B',
                light: '#656D7B',
                replaces: "fill='#656D7B' (sun icon in Switch)",
                token: '--colorIconDisabled',
              },
            ].map(({ dark, light, replaces, token }) => (
              <tr key={token}>
                <td style={{ ...tableCellStyle, fontWeight: 600 }}>
                  <code style={codeStyle}>{token}</code>
                </td>
                <td style={tableCellStyle}>
                  <div
                    style={{ alignItems: 'center', display: 'flex', gap: 8 }}
                  >
                    <div
                      style={{
                        background: light,
                        border: '1px solid rgba(128,128,128,0.3)',
                        borderRadius: 3,
                        flexShrink: 0,
                        height: 16,
                        width: 16,
                      }}
                    />
                    <code style={codeStyle}>{light}</code>
                  </div>
                </td>
                <td style={tableCellStyle}>
                  <div
                    style={{ alignItems: 'center', display: 'flex', gap: 8 }}
                  >
                    <div
                      style={{
                        background: dark,
                        border: '1px solid rgba(128,128,128,0.3)',
                        borderRadius: 3,
                        flexShrink: 0,
                        height: 16,
                        width: 16,
                      }}
                    />
                    <code style={codeStyle}>{dark}</code>
                  </div>
                </td>
                <td style={tableCellStyle}>
                  <code style={{ ...codeStyle, color: '#FF9F43' }}>
                    {replaces}
                  </code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  ),
}
