import {
  diffVariations,
  getDefaultVariantKey,
  getDivergedVariantOverride,
  hasApprovableChanges,
  hasUnmatchedIdentityOverride,
  resolveUnmatchedOverride,
  sortMultivariateOptions,
} from 'common/utils/multivariate'

describe('multivariate', () => {
  describe('getDefaultVariantKey', () => {
    it.each`
      index | expected
      ${0}  | ${'Variant_1'}
      ${1}  | ${'Variant_2'}
      ${9}  | ${'Variant_10'}
    `(
      'getDefaultVariantKey($index) returns $expected',
      ({ expected, index }) => {
        expect(getDefaultVariantKey(index)).toBe(expected)
      },
    )
  })

  describe('sortMultivariateOptions', () => {
    it('sorts options by id ascending', () => {
      const options = [{ id: 3 }, { id: 1 }, { id: 2 }]

      expect(sortMultivariateOptions(options)).toEqual([
        { id: 1 },
        { id: 2 },
        { id: 3 },
      ])
    })

    it('sorts unsaved options last, preserving their input order', () => {
      const options = [
        { id: undefined, value: 'new_a' },
        { id: 2, value: 'saved' },
        { id: null, value: 'new_b' },
      ]

      expect(sortMultivariateOptions(options)).toEqual([
        { id: 2, value: 'saved' },
        { id: undefined, value: 'new_a' },
        { id: null, value: 'new_b' },
      ])
    })

    it('does not mutate the input array', () => {
      const options = [{ id: 2 }, { id: 1 }]

      sortMultivariateOptions(options)

      expect(options).toEqual([{ id: 2 }, { id: 1 }])
    })
  })

  describe('hasUnmatchedIdentityOverride', () => {
    it('detects an override kept from before the flag became multivariate', () => {
      expect(
        hasUnmatchedIdentityOverride({
          controlValue: 'ENV_DEFAULT',
          overrideValue: 'MY_OVERRIDE',
          variationOverrides: [],
        }),
      ).toBe(true)
    })

    it('does not flag an identity sitting on the control value', () => {
      expect(
        hasUnmatchedIdentityOverride({
          controlValue: 'ENV_DEFAULT',
          overrideValue: 'ENV_DEFAULT',
          variationOverrides: [],
        }),
      ).toBe(false)
    })

    it('does not flag an identity assigned a variation', () => {
      expect(
        hasUnmatchedIdentityOverride({
          controlValue: 'ENV_DEFAULT',
          overrideValue: 'MY_OVERRIDE',
          variationOverrides: [{ percentage_allocation: 100 }],
        }),
      ).toBe(false)
    })

    it('flags a partially weighted override, which does not pin a variation', () => {
      expect(
        hasUnmatchedIdentityOverride({
          controlValue: 'ENV_DEFAULT',
          overrideValue: 'MY_OVERRIDE',
          variationOverrides: [{ percentage_allocation: 60 }],
        }),
      ).toBe(true)
    })

    // An unloaded feature state must not read as an override: the caller
    // latches this answer, so a verdict from absent data would stick.
    it.each`
      controlValue     | overrideValue    | scenario
      ${'ENV_DEFAULT'} | ${undefined}     | ${'the override has not loaded'}
      ${undefined}     | ${'MY_OVERRIDE'} | ${'the control value has not loaded'}
      ${undefined}     | ${undefined}     | ${'neither has loaded'}
    `(
      'withholds a verdict while $scenario',
      ({ controlValue, overrideValue }) => {
        expect(
          hasUnmatchedIdentityOverride({
            controlValue,
            overrideValue,
            variationOverrides: [],
          }),
        ).toBe(false)
      },
    )

    it.each`
      controlValue | overrideValue | expected
      ${null}      | ${undefined}  | ${false}
      ${undefined} | ${null}       | ${false}
      ${null}      | ${''}         | ${true}
      ${''}        | ${null}       | ${true}
      ${0}         | ${false}      | ${true}
    `(
      'treats control $controlValue against override $overrideValue as $expected',
      ({ controlValue, expected, overrideValue }) => {
        expect(
          hasUnmatchedIdentityOverride({
            controlValue,
            overrideValue,
            variationOverrides: undefined,
          }),
        ).toBe(expected)
      },
    )
  })

  describe('diffVariations', () => {
    const stored = [
      {
        default_percentage_allocation: 60,
        id: 1,
        key: 'a',
        string_value: 'va',
        type: 'unicode',
      },
      {
        default_percentage_allocation: 40,
        id: 2,
        key: 'b',
        string_value: 'vb',
        type: 'unicode',
      },
    ]

    it('reports nothing when nothing was touched', () => {
      expect(diffVariations({ edited: stored, stored })).toEqual({
        added: false,
        values: false,
        weights: false,
      })
    })

    it('separates a value edit from a weight edit', () => {
      const edited = [
        { ...stored[0], string_value: 'va_changed' },
        { ...stored[1], default_percentage_allocation: 35 },
      ]

      expect(diffVariations({ edited, stored })).toEqual({
        added: false,
        values: true,
        weights: true,
      })
    })

    it('reports a weight edit on its own, leaving values untouched', () => {
      const edited = [
        { ...stored[0], default_percentage_allocation: 70 },
        stored[1],
      ]

      expect(diffVariations({ edited, stored })).toEqual({
        added: false,
        values: false,
        weights: true,
      })
    })

    it('counts a renamed label as a value change, since labels are shared too', () => {
      const edited = [{ ...stored[0], key: 'a_renamed' }, stored[1]]

      expect(diffVariations({ edited, stored }).values).toBe(true)
    })

    it('reports an addition separately, since it serves nothing yet', () => {
      const edited = [
        ...stored,
        {
          default_percentage_allocation: 0,
          string_value: 'vc',
          type: 'unicode',
        },
      ]

      expect(diffVariations({ edited, stored })).toEqual({
        added: true,
        values: false,
        weights: false,
      })
    })

    it('counts a removed variation as a value change', () => {
      expect(diffVariations({ edited: [stored[0]], stored }).values).toBe(true)
    })

    it('reports nothing for a standard flag with no variations', () => {
      expect(diffVariations({ edited: undefined, stored: undefined })).toEqual({
        added: false,
        values: false,
        weights: false,
      })
    })
  })

  describe('hasApprovableChanges', () => {
    const unchanged = {
      editedEnabled: true,
      editedValue: 'same',
      segmentOverridesChanged: false,
      storedEnabled: true,
      storedValue: 'same',
      weightsChanged: false,
    }

    it('is false when only variation values were edited', () => {
      expect(hasApprovableChanges(unchanged)).toBe(false)
    })

    it.each`
      field                        | value
      ${'weightsChanged'}          | ${true}
      ${'segmentOverridesChanged'} | ${true}
      ${'editedEnabled'}           | ${false}
      ${'editedValue'}             | ${'different'}
    `('is true when $field changes', ({ field, value }) => {
      expect(hasApprovableChanges({ ...unchanged, [field]: value })).toBe(true)
    })

    it('treats an undefined value as equal to null rather than a change', () => {
      expect(
        hasApprovableChanges({
          ...unchanged,
          editedValue: undefined,
          storedValue: null,
        }),
      ).toBe(false)
    })
  })

  describe('getDivergedVariantOverride', () => {
    const variants = [
      { id: 1, key: 'variant_a', value: 'old_a' },
      { id: 2, key: 'variant_b', value: 'current_b' },
    ]
    const pinnedToVariant2 = [
      { multivariate_feature_option: 2, percentage_allocation: 100 },
    ]

    it('reports the served value when the pinned variation has since changed', () => {
      expect(
        getDivergedVariantOverride({
          overrideValue: 'stale_b',
          variants,
          variationOverrides: pinnedToVariant2,
        }),
      ).toEqual({ key: 'variant_b', servedValue: 'stale_b' })
    })

    it('reports nothing when the served value matches the pinned variation', () => {
      expect(
        getDivergedVariantOverride({
          overrideValue: 'current_b',
          variants,
          variationOverrides: pinnedToVariant2,
        }),
      ).toBeUndefined()
    })

    it('reports nothing when no variation is pinned', () => {
      expect(
        getDivergedVariantOverride({
          overrideValue: 'stale_b',
          variants,
          variationOverrides: [
            { multivariate_feature_option: 1, percentage_allocation: 50 },
            { multivariate_feature_option: 2, percentage_allocation: 50 },
          ],
        }),
      ).toBeUndefined()
    })

    it('reports nothing when the pinned variation no longer exists', () => {
      expect(
        getDivergedVariantOverride({
          overrideValue: 'stale_b',
          variants,
          variationOverrides: [
            { multivariate_feature_option: 99, percentage_allocation: 100 },
          ],
        }),
      ).toBeUndefined()
    })

    it('withholds a verdict while the feature state has not loaded', () => {
      expect(
        getDivergedVariantOverride({
          overrideValue: undefined,
          variants,
          variationOverrides: pinnedToVariant2,
        }),
      ).toBeUndefined()
    })

    it('withholds a verdict while the variations have not loaded', () => {
      expect(
        getDivergedVariantOverride({
          overrideValue: 'stale_b',
          variants: undefined,
          variationOverrides: pinnedToVariant2,
        }),
      ).toBeUndefined()
    })

    it('treats a null served value as a value, not as unloaded', () => {
      expect(
        getDivergedVariantOverride({
          overrideValue: null,
          variants,
          variationOverrides: pinnedToVariant2,
        }),
      ).toEqual({ key: 'variant_b', servedValue: null })
    })

    it('leaves the save-path predicate untouched for a diverged override', () => {
      expect(
        hasUnmatchedIdentityOverride({
          controlValue: 'control',
          overrideValue: 'stale_b',
          variationOverrides: pinnedToVariant2,
        }),
      ).toBe(false)
    })
  })

  describe('resolveUnmatchedOverride', () => {
    it('lists nothing while the identity has no unmatched override', () => {
      expect(
        resolveUnmatchedOverride({
          isSelected: false,
          latchedValue: undefined,
          overrideValue: 'ENV_DEFAULT',
        }),
      ).toBeUndefined()
    })

    it('latches the override value the first time it is seen', () => {
      expect(
        resolveUnmatchedOverride({
          isSelected: true,
          latchedValue: undefined,
          overrideValue: 'MY_OVERRIDE',
        }),
      ).toEqual({ selected: true, value: 'MY_OVERRIDE' })
    })

    // The bug this function exists for: presence used to follow selection, so
    // picking a variation removed the row instead of deselecting it.
    it('keeps a latched override listed once it stops being selected', () => {
      expect(
        resolveUnmatchedOverride({
          isSelected: false,
          latchedValue: 'MY_OVERRIDE',
          overrideValue: 'MY_OVERRIDE',
        }),
      ).toEqual({ selected: false, value: 'MY_OVERRIDE' })
    })

    // Picking the control row rewrites the edited value, which must not drag
    // the listed row along with it — that value is what the user is replacing.
    it('shows the latched value, not the value the user moved to', () => {
      expect(
        resolveUnmatchedOverride({
          isSelected: false,
          latchedValue: 'MY_OVERRIDE',
          overrideValue: 'ENV_DEFAULT',
        }),
      ).toEqual({ selected: false, value: 'MY_OVERRIDE' })
    })

    it('reselects the latched override without relatching it', () => {
      expect(
        resolveUnmatchedOverride({
          isSelected: true,
          latchedValue: 'MY_OVERRIDE',
          overrideValue: 'MY_OVERRIDE',
        }),
      ).toEqual({ selected: true, value: 'MY_OVERRIDE' })
    })

    it('does not latch while the override value is unavailable', () => {
      expect(
        resolveUnmatchedOverride({
          isSelected: true,
          latchedValue: undefined,
          overrideValue: undefined,
        }),
      ).toBeUndefined()
    })

    // `null` is a real override value, so it has to latch like any other —
    // keying the latch on it would leave the row permanently unlisted.
    it('latches a null override value', () => {
      expect(
        resolveUnmatchedOverride({
          isSelected: true,
          latchedValue: undefined,
          overrideValue: null,
        }),
      ).toEqual({ selected: true, value: null })
    })

    it('keeps a latched null override listed once deselected', () => {
      expect(
        resolveUnmatchedOverride({
          isSelected: false,
          latchedValue: null,
          overrideValue: 'ENV_DEFAULT',
        }),
      ).toEqual({ selected: false, value: null })
    })
  })
})
