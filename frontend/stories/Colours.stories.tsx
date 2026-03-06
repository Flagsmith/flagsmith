import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import * as tokens from 'common/theme/tokens'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const Swatch: React.FC<{ name: string; value: string }> = ({ name, value }) => (
  <div
    style={{ alignItems: 'center', display: 'flex', gap: 12, marginBottom: 8 }}
  >
    <div
      style={{
        background: value,
        border: '1px solid rgba(128,128,128,0.25)',
        borderRadius: 6,
        flexShrink: 0,
        height: 48,
        width: 48,
      }}
    />
    <div>
      <div
        style={{
          color: 'var(--colorTextStandard)',
          fontSize: 13,
          fontWeight: 600,
        }}
      >
        {name}
      </div>
      <code style={{ color: 'var(--colorTextSecondary)', fontSize: 11 }}>
        {value}
      </code>
    </div>
  </div>
)

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({
  children,
  title,
}) => (
  <div style={{ marginBottom: 32 }}>
    <h3
      style={{
        borderBottom: '1px solid var(--colorStrokeStandard)',
        color: 'var(--colorTextHeading)',
        fontSize: 16,
        fontWeight: 700,
        marginBottom: 12,
        paddingBottom: 8,
      }}
    >
      {title}
    </h3>
    <div
      style={{
        display: 'grid',
        gap: 8,
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
      }}
    >
      {children}
    </div>
  </div>
)

// ---------------------------------------------------------------------------
// Token groups — extracted from the token file
// ---------------------------------------------------------------------------

const tokenGroups: Record<string, Record<string, string>> = {
  Brand: {
    colorBrandPrimary: tokens.colorBrandPrimary,
    colorBrandPrimaryActive: tokens.colorBrandPrimaryActive,
    colorBrandPrimaryAlpha16: tokens.colorBrandPrimaryAlpha16,
    colorBrandPrimaryAlpha24: tokens.colorBrandPrimaryAlpha24,
    colorBrandPrimaryAlpha8: tokens.colorBrandPrimaryAlpha8,
    colorBrandPrimaryHover: tokens.colorBrandPrimaryHover,
    colorBrandSecondary: tokens.colorBrandSecondary,
    colorBrandSecondaryHover: tokens.colorBrandSecondaryHover,
  },
  Feedback: {
    colorFeedbackDanger: tokens.colorFeedbackDanger,
    colorFeedbackDangerLight: tokens.colorFeedbackDangerLight,
    colorFeedbackDangerSurface: tokens.colorFeedbackDangerSurface,
    colorFeedbackInfo: tokens.colorFeedbackInfo,
    colorFeedbackInfoSurface: tokens.colorFeedbackInfoSurface,
    colorFeedbackSuccess: tokens.colorFeedbackSuccess,
    colorFeedbackSuccessLight: tokens.colorFeedbackSuccessLight,
    colorFeedbackSuccessSurface: tokens.colorFeedbackSuccessSurface,
    colorFeedbackWarning: tokens.colorFeedbackWarning,
    colorFeedbackWarningSurface: tokens.colorFeedbackWarningSurface,
  },
  Icon: {
    colorIconInverse: tokens.colorIconInverse,
    colorIconSecondary: tokens.colorIconSecondary,
    colorIconStandard: tokens.colorIconStandard,
    colorIconTertiary: tokens.colorIconTertiary,
  },
  Interactive: {
    colorInteractiveSecondary: tokens.colorInteractiveSecondary,
    colorInteractiveSecondaryActive: tokens.colorInteractiveSecondaryActive,
    colorInteractiveSecondaryHover: tokens.colorInteractiveSecondaryHover,
    colorInteractiveSwitchOff: tokens.colorInteractiveSwitchOff,
    colorInteractiveSwitchOffHover: tokens.colorInteractiveSwitchOffHover,
  },
  Stroke: {
    colorStrokeFocus: tokens.colorStrokeFocus,
    colorStrokeInput: tokens.colorStrokeInput,
    colorStrokeInputFocus: tokens.colorStrokeInputFocus,
    colorStrokeInputHover: tokens.colorStrokeInputHover,
    colorStrokeInverse: tokens.colorStrokeInverse,
    colorStrokeSecondary: tokens.colorStrokeSecondary,
    colorStrokeStandard: tokens.colorStrokeStandard,
  },
  Surface: {
    colorSurfaceInput: tokens.colorSurfaceInput,
    colorSurfaceInverse: tokens.colorSurfaceInverse,
    colorSurfaceModal: tokens.colorSurfaceModal,
    colorSurfaceMuted: tokens.colorSurfaceMuted,
    colorSurfacePanel: tokens.colorSurfacePanel,
    colorSurfacePanelSecondary: tokens.colorSurfacePanelSecondary,
    colorSurfaceSecondary: tokens.colorSurfaceSecondary,
    colorSurfaceStandard: tokens.colorSurfaceStandard,
    colorSurfaceTertiary: tokens.colorSurfaceTertiary,
  },
  Text: {
    colorTextHeading: tokens.colorTextHeading,
    colorTextInverse: tokens.colorTextInverse,
    colorTextOnBrand: tokens.colorTextOnBrand,
    colorTextSecondary: tokens.colorTextSecondary,
    colorTextStandard: tokens.colorTextStandard,
    colorTextTertiary: tokens.colorTextTertiary,
  },
}

// ---------------------------------------------------------------------------
// Current SCSS variables — documents what exists today (before token migration)
// ---------------------------------------------------------------------------

const currentScssVars: Record<
  string,
  Record<string, { light: string; dark: string }>
> = {
  'Backgrounds': {
    '$bg-dark100': { dark: '#2d3443', light: '(unused in light)' },
    '$bg-light100 / $bg-dark500': { dark: '#101628', light: '#ffffff' },
    '$bg-light200 / $bg-dark400': { dark: '#15192b', light: '#fafafb' },
    '$bg-light300 / $bg-dark300': { dark: '#161d30', light: '#eff1f4' },
    '$bg-light500 / $bg-dark200': { dark: '#202839', light: '#e0e3e9' },
  },
  'Body / Text': {
    '$body-color': { dark: 'white', light: '#1a2634' },
    '$header-color': { dark: '#ffffff', light: '#1e0d26' },
    '$text-icon-grey': { dark: '(no override)', light: '#656d7b' },
    '$text-icon-light-grey': {
      dark: '(no override)',
      light: 'rgba(157,164,174,1)',
    },
  },
  'Borders / Strokes': {
    '$basic-alpha-16 / $white-alpha-16': {
      dark: 'rgba(255,255,255,0.16)',
      light: 'rgba(101,109,123,0.16)',
    },
    '$input-border-color': { dark: '#15192b', light: 'rgba(101,109,123,0.16)' },
    '$panel-border-color': {
      dark: 'rgba(255,255,255,0.16)',
      light: 'rgba(101,109,123,0.16)',
    },
  },
  'Brand Palette': {
    '$danger': { dark: '#ef4d56', light: '#ef4d56' },
    '$info': { dark: '#0aaddf', light: '#0aaddf' },
    '$primary': { dark: '#6837fc', light: '#6837fc' },
    '$primary400': { dark: '#906af6', light: '#906af6' },
    '$primary600': { dark: '#4e25db', light: '#4e25db' },
    '$success': { dark: '#27ab95', light: '#27ab95' },
    '$warning': { dark: '#ff9f43', light: '#ff9f43' },
  },
}

const ScssVarRow: React.FC<{ name: string; light: string; dark: string }> = ({
  dark,
  light,
  name,
}) => (
  <tr>
    <td style={{ fontFamily: 'monospace', fontSize: 12, padding: '6px 12px' }}>
      {name}
    </td>
    <td style={{ padding: '6px 12px' }}>
      <div style={{ alignItems: 'center', display: 'flex', gap: 8 }}>
        <div
          style={{
            background: light,
            border: '1px solid rgba(128,128,128,0.25)',
            borderRadius: 4,
            height: 20,
            width: 20,
          }}
        />
        <code style={{ fontSize: 11 }}>{light}</code>
      </div>
    </td>
    <td style={{ padding: '6px 12px' }}>
      <div style={{ alignItems: 'center', display: 'flex', gap: 8 }}>
        <div
          style={{
            background:
              dark === '(no override)' || dark === '(unused in light)'
                ? 'transparent'
                : dark,
            border: '1px solid rgba(128,128,128,0.25)',
            borderRadius: 4,
            height: 20,
            width: 20,
          }}
        />
        <code style={{ fontSize: 11 }}>{dark}</code>
      </div>
    </td>
  </tr>
)

// ---------------------------------------------------------------------------
// Stories
// ---------------------------------------------------------------------------

const meta: Meta = {
  parameters: {
    layout: 'padded',
  },
  title: 'Design System/Colours',
}
export default meta

export const SemanticTokens: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 8 }}>
        Semantic Colour Tokens
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 24,
        }}
      >
        These tokens automatically adapt to light/dark mode via CSS custom
        properties. Toggle the theme in the toolbar above to preview both modes.
        <br />
        Source: <code>common/theme/tokens.ts</code> +{' '}
        <code>web/styles/_tokens.scss</code>
      </p>
      {Object.entries(tokenGroups).map(([group, values]) => (
        <Section key={group} title={group}>
          {Object.entries(values).map(([name, value]) => (
            <Swatch key={name} name={name} value={value} />
          ))}
        </Section>
      ))}
    </div>
  ),
}

export const CurrentScssVariables: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 8 }}>
        Current SCSS Variables
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 24,
        }}
      >
        The existing colour system in <code>_variables.scss</code>. Each
        variable has a separate <code>$*-dark</code> counterpart used in{' '}
        <code>.dark</code> selectors. This is what the token migration will
        consolidate.
      </p>
      {Object.entries(currentScssVars).map(([section, vars]) => (
        <div key={section} style={{ marginBottom: 24 }}>
          <h3
            style={{
              color: 'var(--colorTextHeading)',
              fontSize: 16,
              fontWeight: 700,
              marginBottom: 8,
            }}
          >
            {section}
          </h3>
          <table
            style={{ borderCollapse: 'collapse', fontSize: 13, width: '100%' }}
          >
            <thead>
              <tr
                style={{ borderBottom: '2px solid var(--colorStrokeStandard)' }}
              >
                <th
                  style={{
                    color: 'var(--colorTextSecondary)',
                    padding: '6px 12px',
                    textAlign: 'left',
                  }}
                >
                  Variable
                </th>
                <th
                  style={{
                    color: 'var(--colorTextSecondary)',
                    padding: '6px 12px',
                    textAlign: 'left',
                  }}
                >
                  Light
                </th>
                <th
                  style={{
                    color: 'var(--colorTextSecondary)',
                    padding: '6px 12px',
                    textAlign: 'left',
                  }}
                >
                  Dark
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(vars).map(([name, { dark, light }]) => (
                <ScssVarRow key={name} name={name} light={light} dark={dark} />
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  ),
}
