// =============================================================================
// Design Tokens — Flagsmith
// =============================================================================
//
// Semantic colour tokens using CSS custom properties with fallback values.
// Import these in TS/TSX files for inline styles that automatically respond
// to light/dark mode. The CSS custom properties are defined in _tokens.scss.
//
// Naming convention: color{Category}{Variant}{State}
//   Category: Text, Surface, Icon, Stroke, Brand, Feedback
//   Variant:  Standard, Secondary, Tertiary, Inverse, Muted
//   State:    Hover, Active, Focus, Disabled (optional)
//
// =============================================================================

// ---------------------------------------------------------------------------
// Text
// ---------------------------------------------------------------------------

/** Primary text colour — dark in light mode, white in dark mode */
export const colorTextStandard = 'var(--colorTextStandard, #1a2634)'

/** Secondary/muted text */
export const colorTextSecondary = 'var(--colorTextSecondary, #656d7b)'

/** Tertiary/placeholder text */
export const colorTextTertiary =
  'var(--colorTextTertiary, rgba(157, 164, 174, 1))'

/** Inverse text — white in light mode, dark in dark mode */
export const colorTextInverse = 'var(--colorTextInverse, #ffffff)'

/** Text used on dark/branded backgrounds — always white */
export const colorTextOnBrand = 'var(--colorTextOnBrand, #ffffff)'

/** Header/label text — slightly different from standard body text */
export const colorTextHeading = 'var(--colorTextHeading, #1e0d26)'

// ---------------------------------------------------------------------------
// Surface (backgrounds)
// ---------------------------------------------------------------------------

/** Primary surface — white in light, dark navy in dark mode */
export const colorSurfaceStandard = 'var(--colorSurfaceStandard, #ffffff)'

/** Subtle off-white / raised dark surface */
export const colorSurfaceSecondary = 'var(--colorSurfaceSecondary, #fafafb)'

/** Stronger contrast surface — e.g. table headers, pills */
export const colorSurfaceTertiary = 'var(--colorSurfaceTertiary, #eff1f4)'

/** Muted/faint surface */
export const colorSurfaceMuted = 'var(--colorSurfaceMuted, #e0e3e9)'

/** Inverse surface — dark in light mode */
export const colorSurfaceInverse = 'var(--colorSurfaceInverse, #101628)'

/** Panel/card surface */
export const colorSurfacePanel = 'var(--colorSurfacePanel, #ffffff)'
export const colorSurfacePanelSecondary =
  'var(--colorSurfacePanelSecondary, #fafafb)'

/** Modal surface */
export const colorSurfaceModal = 'var(--colorSurfaceModal, #ffffff)'

/** Input surface */
export const colorSurfaceInput = 'var(--colorSurfaceInput, #ffffff)'

// ---------------------------------------------------------------------------
// Icon
// ---------------------------------------------------------------------------

/** Standard icon colour — inherits from text standard */
export const colorIconStandard = 'var(--colorIconStandard, #1a2634)'

/** Secondary/muted icon */
export const colorIconSecondary = 'var(--colorIconSecondary, #656d7b)'

/** Tertiary/faint icon */
export const colorIconTertiary =
  'var(--colorIconTertiary, rgba(157, 164, 174, 1))'

/** Inverse icon — white in light mode */
export const colorIconInverse = 'var(--colorIconInverse, #ffffff)'

// ---------------------------------------------------------------------------
// Stroke (borders, dividers)
// ---------------------------------------------------------------------------

/** Standard border */
export const colorStrokeStandard =
  'var(--colorStrokeStandard, rgba(101, 109, 123, 0.16))'

/** Stronger border */
export const colorStrokeSecondary =
  'var(--colorStrokeSecondary, rgba(101, 109, 123, 0.24))'

/** Focus ring border */
export const colorStrokeFocus = 'var(--colorStrokeFocus, #6837fc)'

/** Inverse border — for dark mode */
export const colorStrokeInverse =
  'var(--colorStrokeInverse, rgba(255, 255, 255, 0.16))'

/** Input border */
export const colorStrokeInput =
  'var(--colorStrokeInput, rgba(101, 109, 123, 0.16))'
export const colorStrokeInputHover =
  'var(--colorStrokeInputHover, rgba(101, 109, 123, 0.24))'
export const colorStrokeInputFocus = 'var(--colorStrokeInputFocus, #6837fc)'

// ---------------------------------------------------------------------------
// Brand
// ---------------------------------------------------------------------------

/** Primary brand colour */
export const colorBrandPrimary = 'var(--colorBrandPrimary, #6837fc)'
export const colorBrandPrimaryHover = 'var(--colorBrandPrimaryHover, #4e25db)'
export const colorBrandPrimaryActive = 'var(--colorBrandPrimaryActive, #3919b7)'

/** Brand accent (secondary — yellow/gold) */
export const colorBrandSecondary = 'var(--colorBrandSecondary, #F7D56E)'
export const colorBrandSecondaryHover =
  'var(--colorBrandSecondaryHover, #e5c55f)'

/** Primary with alpha (for subtle backgrounds, chips, outlines) */
export const colorBrandPrimaryAlpha8 =
  'var(--colorBrandPrimaryAlpha8, rgba(149, 108, 255, 0.08))'
export const colorBrandPrimaryAlpha16 =
  'var(--colorBrandPrimaryAlpha16, rgba(149, 108, 255, 0.16))'
export const colorBrandPrimaryAlpha24 =
  'var(--colorBrandPrimaryAlpha24, rgba(149, 108, 255, 0.24))'

// ---------------------------------------------------------------------------
// Feedback (semantic status colours)
// ---------------------------------------------------------------------------

export const colorFeedbackSuccess = 'var(--colorFeedbackSuccess, #27ab95)'
export const colorFeedbackSuccessLight =
  'var(--colorFeedbackSuccessLight, #56ccad)'
export const colorFeedbackSuccessSurface =
  'var(--colorFeedbackSuccessSurface, rgba(238, 248, 247))'

export const colorFeedbackDanger = 'var(--colorFeedbackDanger, #ef4d56)'
export const colorFeedbackDangerLight =
  'var(--colorFeedbackDangerLight, #f57c78)'
export const colorFeedbackDangerSurface =
  'var(--colorFeedbackDangerSurface, rgba(254, 239, 241))'

export const colorFeedbackWarning = 'var(--colorFeedbackWarning, #ff9f43)'
export const colorFeedbackWarningSurface =
  'var(--colorFeedbackWarningSurface, rgba(255, 248, 240))'

export const colorFeedbackInfo = 'var(--colorFeedbackInfo, #0aaddf)'
export const colorFeedbackInfoSurface =
  'var(--colorFeedbackInfoSurface, rgba(236, 249, 252))'

// ---------------------------------------------------------------------------
// Interactive (buttons, switches)
// ---------------------------------------------------------------------------

/** Secondary button / subtle interactive surface */
export const colorInteractiveSecondary =
  'var(--colorInteractiveSecondary, rgba(101, 109, 123, 0.08))'
export const colorInteractiveSecondaryHover =
  'var(--colorInteractiveSecondaryHover, rgba(101, 109, 123, 0.16))'
export const colorInteractiveSecondaryActive =
  'var(--colorInteractiveSecondaryActive, rgba(101, 109, 123, 0.24))'

/** Switch (off state) */
export const colorInteractiveSwitchOff =
  'var(--colorInteractiveSwitchOff, rgba(101, 109, 123, 0.24))'
export const colorInteractiveSwitchOffHover =
  'var(--colorInteractiveSwitchOffHover, rgba(101, 109, 123, 0.48))'

// ---------------------------------------------------------------------------
// Misc
// ---------------------------------------------------------------------------

export const borderRadiusSm = 'var(--borderRadiusSm, 4px)'
export const borderRadiusStandard = 'var(--borderRadiusStandard, 6px)'
export const borderRadiusLg = 'var(--borderRadiusLg, 8px)'
export const borderRadiusXl = 'var(--borderRadiusXl, 10px)'
