import flagsmith from '@flagsmith/flagsmith'
import {
  clearOnboardingEntry,
  decideOnboardingEntry,
  getStoredOnboardingTargetingKey,
  getStoredOnboardingVariant,
  persistOnboardingEntry,
  resolveOnboardingVariant,
} from 'common/utils/onboardingEntry'

jest.mock('@flagsmith/flagsmith', () => ({
  getContext: jest.fn(),
  getExperimentFlag: jest.fn(),
  identify: jest.fn(),
}))

const storage = new Map<string, string>()
jest.mock('common/safeLocalStorage', () => ({
  storageGet: (key: string) => storage.get(key) ?? null,
  storageRemove: (key: string) => storage.delete(key),
  storageSet: (key: string, value: string) => storage.set(key, value),
}))

const mockFlagsmith = jest.mocked(flagsmith)

describe('decideOnboardingEntry', () => {
  beforeEach(() => {
    storage.clear()
    jest.resetAllMocks()
    mockFlagsmith.identify.mockResolvedValue(undefined)
    mockFlagsmith.getContext.mockReturnValue({
      identity: { identifier: 'anon-123' },
    })
  })

  it('returns the decision without persisting anything', async () => {
    // Given
    mockFlagsmith.getExperimentFlag.mockReturnValue({
      enabled: true,
      value: null,
      variant: 'single_page',
    })

    // When
    const decision = await decideOnboardingEntry()

    // Then
    // A decision losing the caller's timeout race must leave no trace.
    expect(decision).toEqual({
      targetingKey: 'anon-123',
      variant: 'single_page',
    })
    expect(getStoredOnboardingVariant()).toBeNull()
    expect(getStoredOnboardingTargetingKey()).toBeNull()
  })

  it('maps a disabled flag to control', async () => {
    // Given
    mockFlagsmith.getExperimentFlag.mockReturnValue({
      enabled: false,
      value: null,
    })

    // When
    const decision = await decideOnboardingEntry()

    // Then
    expect(decision.variant).toBe('control')
  })
})

describe('persistOnboardingEntry', () => {
  beforeEach(() => {
    storage.clear()
  })

  it('stores an accepted decision', () => {
    // When
    const variant = persistOnboardingEntry({
      targetingKey: 'anon-123',
      variant: 'single_page',
    })

    // Then
    expect(variant).toBe('single_page')
    expect(getStoredOnboardingVariant()).toBe('single_page')
    expect(getStoredOnboardingTargetingKey()).toBe('anon-123')
  })

  it('downgrades a non-control variant without an identifier to control', () => {
    // When
    const variant = persistOnboardingEntry({
      targetingKey: null,
      variant: 'single_page',
    })

    // Then
    expect(variant).toBe('control')
    expect(getStoredOnboardingVariant()).toBe('control')
    expect(getStoredOnboardingTargetingKey()).toBeNull()
  })
})

describe('resolveOnboardingVariant', () => {
  beforeEach(() => {
    storage.clear()
  })

  it.each`
    stored           | decision                                          | expected
    ${'single_page'} | ${{ targetingKey: 'anon-1', variant: 'control' }} | ${'single_page'}
    ${'single_page'} | ${null}                                           | ${'single_page'}
    ${null}          | ${null}                                           | ${'control'}
  `(
    'stored $stored with decision $decision routes as $expected',
    ({ decision, expected, stored }) => {
      // When
      const variant = resolveOnboardingVariant(stored, decision)

      // Then
      expect(variant).toBe(expected)
    },
  )

  it('keeps the stored variant instead of persisting a new decision', () => {
    // Given
    storage.set('onboarding_variant', 'single_page')

    // When
    resolveOnboardingVariant('single_page', {
      targetingKey: 'anon-2',
      variant: 'control',
    })

    // Then
    expect(getStoredOnboardingVariant()).toBe('single_page')
    expect(getStoredOnboardingTargetingKey()).toBeNull()
  })

  it('persists a new decision when nothing is stored', () => {
    // When
    resolveOnboardingVariant(null, {
      targetingKey: 'anon-3',
      variant: 'single_page',
    })

    // Then
    expect(getStoredOnboardingVariant()).toBe('single_page')
    expect(getStoredOnboardingTargetingKey()).toBe('anon-3')
  })
})

describe('clearOnboardingEntry', () => {
  it('removes the stored variant and targeting key', () => {
    // Given
    persistOnboardingEntry({ targetingKey: 'anon-1', variant: 'single_page' })

    // When
    clearOnboardingEntry()

    // Then
    expect(getStoredOnboardingVariant()).toBeNull()
    expect(getStoredOnboardingTargetingKey()).toBeNull()
  })
})
