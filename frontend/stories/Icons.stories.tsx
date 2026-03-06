import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import Icon from 'components/Icon'
import type { IconName } from 'components/Icon'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getBorderStyle(broken?: boolean, hardcoded?: boolean): string {
  if (broken) return '2px solid #ef4d56'
  if (hardcoded) return '2px solid #ff9f43'
  return '1px solid var(--colorStrokeStandard)'
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

/** All icon names from the IconName union type in Icon.tsx */
const allIconNames: IconName[] = [
  'arrow-left',
  'arrow-right',
  'award',
  'bar-chart',
  'bell',
  'calendar',
  'checkmark',
  'checkmark-circle',
  'checkmark-square',
  'chevron-down',
  'chevron-left',
  'chevron-right',
  'chevron-up',
  'clock',
  'close-circle',
  'code',
  'copy',
  'copy-outlined',
  'dash',
  'diff',
  'edit',
  'edit-outlined',
  'email',
  'expand',
  'eye',
  'eye-off',
  'features',
  'file-text',
  'flash',
  'flask',
  'github',
  'google',
  'height',
  'info',
  'info-outlined',
  'issue-closed',
  'issue-linked',
  'layers',
  'layout',
  'link',
  'list',
  'lock',
  'minus-circle',
  'moon',
  'more-vertical',
  'nav-logo',
  'open-external-link',
  'options-2',
  'people',
  'person',
  'pie-chart',
  'plus',
  'pr-closed',
  'pr-draft',
  'pr-linked',
  'pr-merged',
  'radio',
  'refresh',
  'request',
  'required',
  'rocket',
  'search',
  'setting',
  'settings-2',
  'shield',
  'star',
  'sun',
  'timer',
  'trash-2',
  'warning',
]

/** Icons that default to #1A2634 — invisible in dark mode */
const darkModeBreakageIcons: IconName[] = [
  'checkmark',
  'chevron-down',
  'chevron-left',
  'chevron-right',
  'chevron-up',
  'arrow-left',
  'arrow-right',
  'clock',
  'code',
  'copy',
  'copy-outlined',
  'dash',
  'diff',
  'edit',
  'edit-outlined',
  'email',
  'file-text',
  'flash',
  'flask',
  'height',
  'bell',
  'calendar',
  'layout',
  'layers',
  'list',
  'lock',
  'minus-circle',
  'more-vertical',
  'people',
  'person',
  'pie-chart',
  'refresh',
  'request',
  'setting',
  'settings-2',
  'shield',
  'star',
  'timer',
  'trash-2',
  'bar-chart',
  'award',
  'options-2',
  'open-external-link',
  'features',
  'rocket',
  'expand',
  'radio',
]

/** Icons with hardcoded fills that can't be overridden */
const hardcodedFillIcons: IconName[] = [
  'github',
  'google',
  'link',
  'pr-merged',
  'pr-closed',
  'pr-linked',
  'pr-draft',
  'issue-closed',
  'issue-linked',
]

/** Icons using specific semantic defaults (not #1A2634) */
const semanticDefaultIcons: Record<
  string,
  { icons: IconName[]; colour: string }
> = {
  'Cyan (#0AADDF)': { colour: '#0AADDF', icons: ['info'] },
  'Grey (#9DA4AE)': {
    colour: '#9DA4AE',
    icons: ['eye', 'eye-off', 'search', 'info-outlined'],
  },
  'Orange (#FF9F43)': { colour: '#FF9F43', icons: ['warning'] },
  'Purple (#6837FC)': { colour: '#6837FC', icons: ['checkmark-square'] },
  'Red (#EF4D56)': { colour: '#EF4D56', icons: ['close-circle'] },
  'Sun/Moon grey (#656D7B)': { colour: '#656D7B', icons: ['sun', 'moon'] },
  'White (#ffffff)': { colour: '#ffffff', icons: ['plus', 'nav-logo'] },
}

/** Separate SVG components outside of Icon.tsx */
const separateSvgComponents = [
  { name: 'ArrowUpIcon', path: 'web/components/svg/ArrowUpIcon.tsx' },
  { name: 'AuditLogIcon', path: 'web/components/svg/AuditLogIcon.tsx' },
  { name: 'CaretDownIcon', path: 'web/components/svg/CaretDownIcon.tsx' },
  { name: 'CaretRightIcon', path: 'web/components/svg/CaretRightIcon.tsx' },
  {
    name: 'DocumentationIcon',
    path: 'web/components/svg/DocumentationIcon.tsx',
  },
  { name: 'DropIcon', path: 'web/components/svg/DropIcon.tsx' },
  {
    name: 'EnvironmentSettingsIcon',
    path: 'web/components/svg/EnvironmentSettingsIcon.tsx',
  },
  { name: 'FeaturesIcon', path: 'web/components/svg/FeaturesIcon.tsx' },
  { name: 'LogoutIcon', path: 'web/components/svg/LogoutIcon.tsx' },
  { name: 'NavIconSmall', path: 'web/components/svg/NavIconSmall.tsx' },
  { name: 'OrgSettingsIcon', path: 'web/components/svg/OrgSettingsIcon.tsx' },
  { name: 'PlayIcon', path: 'web/components/svg/PlayIcon.tsx' },
  { name: 'PlusIcon', path: 'web/components/svg/PlusIcon.tsx' },
  {
    name: 'ProjectSettingsIcon',
    path: 'web/components/svg/ProjectSettingsIcon.tsx',
  },
  { name: 'SegmentsIcon', path: 'web/components/svg/SegmentsIcon.tsx' },
  { name: 'SparklesIcon', path: 'web/components/svg/SparklesIcon.tsx' },
  { name: 'UpgradeIcon', path: 'web/components/svg/UpgradeIcon.tsx' },
  { name: 'UserSettingsIcon', path: 'web/components/svg/UserSettingsIcon.tsx' },
  { name: 'UsersIcon', path: 'web/components/svg/UsersIcon.tsx' },
  { name: 'GithubIcon', path: 'web/components/base/icons/GithubIcon.tsx' },
  { name: 'GitlabIcon', path: 'web/components/base/icons/GitlabIcon.tsx' },
  {
    name: 'IdentityOverridesIcon',
    path: 'web/components/IdentityOverridesIcon.tsx',
  },
  {
    name: 'SegmentOverridesIcon',
    path: 'web/components/SegmentOverridesIcon.tsx',
  },
]

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const IconCell: React.FC<{
  name: IconName
  broken?: boolean
  hardcoded?: boolean
}> = ({ broken, hardcoded, name }) => (
  <div
    style={{
      alignItems: 'center',
      background: 'var(--colorSurfacePanel)',
      border: getBorderStyle(broken, hardcoded),
      borderRadius: 6,
      display: 'flex',
      flexDirection: 'column',
      minWidth: 100,
      padding: 12,
    }}
  >
    <div style={{ alignItems: 'center', display: 'flex', height: 32 }}>
      <Icon name={name} width={24} />
    </div>
    <code
      style={{
        color: 'var(--colorTextSecondary)',
        fontSize: 10,
        marginTop: 6,
        textAlign: 'center',
        wordBreak: 'break-all',
      }}
    >
      {name}
    </code>
    {broken && (
      <span
        style={{ color: '#ef4d56', fontSize: 9, fontWeight: 700, marginTop: 4 }}
      >
        DARK MODE BROKEN
      </span>
    )}
    {hardcoded && (
      <span
        style={{ color: '#ff9f43', fontSize: 9, fontWeight: 700, marginTop: 4 }}
      >
        HARDCODED FILL
      </span>
    )}
  </div>
)

// ---------------------------------------------------------------------------
// Stories
// ---------------------------------------------------------------------------

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Icons',
}
export default meta

export const AllIcons: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 1100 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        All Icons ({allIconNames.length})
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 16,
        }}
      >
        Source: <code>Icon.tsx</code> — 71 inline SVGs in a single switch
        statement (1,543 lines). Toggle dark mode in the toolbar to see which
        icons disappear.
      </p>
      <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
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
          Defaults to #1A2634 — invisible in dark mode
        </span>
        <span
          style={{
            border: '2px solid #ff9f43',
            borderRadius: 2,
            display: 'inline-block',
            height: 12,
            marginLeft: 16,
            width: 12,
          }}
        />
        <span style={{ color: 'var(--colorTextSecondary)', fontSize: 12 }}>
          Hardcoded fill — not overridable via props
        </span>
      </div>
      <div
        style={{
          display: 'grid',
          gap: 8,
          gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))',
        }}
      >
        {allIconNames.map((name) => (
          <IconCell
            key={name}
            name={name}
            broken={darkModeBreakageIcons.includes(name)}
            hardcoded={hardcodedFillIcons.includes(name)}
          />
        ))}
      </div>
    </div>
  ),
}

export const DarkModeBroken: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 1100 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Dark Mode Broken Icons ({darkModeBreakageIcons.length})
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 16,
        }}
      >
        These icons default to <code>fill=&quot;#1A2634&quot;</code> (dark
        navy). On the dark background (<code>#101628</code>), they are
        invisible.
        <br />
        <br />
        <strong>Fix:</strong> Replace{' '}
        <code>
          fill={'{'}fill || &apos;#1A2634&apos;{'}'}
        </code>{' '}
        with{' '}
        <code>
          fill={'{'}fill || &apos;currentColor&apos;{'}'}
        </code>
        .
      </p>
      <div
        style={{
          display: 'grid',
          gap: 8,
          gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))',
        }}
      >
        {darkModeBreakageIcons.map((name) => (
          <IconCell key={name} name={name} broken />
        ))}
      </div>
    </div>
  ),
}

export const HardcodedFills: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 1100 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Hardcoded Fill Icons ({hardcodedFillIcons.length})
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 16,
        }}
      >
        These icons have fill colours baked into the SVG paths. The{' '}
        <code>fill</code> prop has no effect. Some (like Google) intentionally
        use brand colours, others (like
        <code>github</code> and <code>pr-draft</code>) use <code>#1A2634</code>{' '}
        which breaks in dark mode.
      </p>
      <div
        style={{
          display: 'grid',
          gap: 8,
          gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))',
        }}
      >
        {hardcodedFillIcons.map((name) => (
          <IconCell key={name} name={name} hardcoded />
        ))}
      </div>
    </div>
  ),
}

export const SemanticDefaults: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 1100 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Icons with Semantic Defaults
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 16,
        }}
      >
        These icons use meaningful default fill colours (success, danger, info
        etc.) rather than the generic <code>#1A2634</code>.
      </p>
      {Object.entries(semanticDefaultIcons).map(
        ([label, { colour, icons }]) => (
          <div key={label} style={{ marginBottom: 20 }}>
            <h4
              style={{
                color: 'var(--colorTextStandard)',
                fontSize: 14,
                marginBottom: 8,
              }}
            >
              {label}{' '}
              <span
                style={{
                  background: colour,
                  border: '1px solid rgba(128,128,128,0.3)',
                  borderRadius: 2,
                  display: 'inline-block',
                  height: 12,
                  verticalAlign: 'middle',
                  width: 12,
                }}
              />
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {icons.map((name) => (
                <IconCell key={name} name={name} />
              ))}
            </div>
          </div>
        ),
      )}
    </div>
  ),
}

export const SeparateSvgComponents: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 4 }}>
        Separate SVG Components ({separateSvgComponents.length})
      </h2>
      <p
        style={{
          color: 'var(--colorTextSecondary)',
          fontSize: 14,
          marginBottom: 16,
        }}
      >
        These icons exist as individual <code>.tsx</code> files outside of{' '}
        <code>Icon.tsx</code>. They are imported directly by components, not via
        the <code>&lt;Icon name=&quot;...&quot; /&gt;</code> API.
        <br />
        <br />
        <strong>Consolidation opportunity:</strong> Either move these into the
        Icon.tsx switch statement, or extract Icon.tsx&apos;s inline SVGs into
        individual files and use a consistent pattern for all icons.
      </p>
      <table
        style={{ borderCollapse: 'collapse', fontSize: 13, width: '100%' }}
      >
        <thead>
          <tr style={{ borderBottom: '2px solid var(--colorStrokeStandard)' }}>
            <th
              style={{
                color: 'var(--colorTextSecondary)',
                padding: '8px 12px',
                textAlign: 'left',
              }}
            >
              Component
            </th>
            <th
              style={{
                color: 'var(--colorTextSecondary)',
                padding: '8px 12px',
                textAlign: 'left',
              }}
            >
              File Path
            </th>
          </tr>
        </thead>
        <tbody>
          {separateSvgComponents.map(({ name, path }) => (
            <tr
              key={name}
              style={{ borderBottom: '1px solid var(--colorStrokeStandard)' }}
            >
              <td
                style={{
                  color: 'var(--colorTextStandard)',
                  fontWeight: 600,
                  padding: '6px 12px',
                }}
              >
                {name}
              </td>
              <td style={{ padding: '6px 12px' }}>
                <code
                  style={{ color: 'var(--colorTextSecondary)', fontSize: 11 }}
                >
                  {path}
                </code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ),
}

export const IconSystemSummary: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
      <h2 style={{ color: 'var(--colorTextHeading)', marginBottom: 16 }}>
        Icon System Summary
      </h2>
      <table
        style={{ borderCollapse: 'collapse', fontSize: 14, width: '100%' }}
      >
        <tbody>
          {[
            ['Total icon names in Icon.tsx', '71'],
            [
              'Inline SVGs in switch statement',
              '70 (paste declared but not implemented)',
            ],
            ['Separate SVG components', '23 files across 3 directories'],
            ['Integration SVG files', '37 in /static/images/integrations/'],
            [
              'Icons defaulting to #1A2634',
              `${darkModeBreakageIcons.length} — invisible in dark mode`,
            ],
            [
              'Icons with hardcoded fills',
              `${hardcodedFillIcons.length} — cannot be overridden via props`,
            ],
            ['Icons using currentColor', '0'],
            ['Icon.tsx total lines', '1,543'],
            ['Unused dependency: ionicons', 'v7.2.1 installed but not used'],
          ].map(([label, value]) => (
            <tr
              key={label}
              style={{ borderBottom: '1px solid var(--colorStrokeStandard)' }}
            >
              <td
                style={{
                  color: 'var(--colorTextStandard)',
                  fontWeight: 600,
                  padding: '8px 12px',
                }}
              >
                {label}
              </td>
              <td
                style={{
                  color: 'var(--colorTextSecondary)',
                  padding: '8px 12px',
                }}
              >
                {value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ),
}
