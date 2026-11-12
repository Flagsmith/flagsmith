import flagsmith from '@flagsmith/flagsmith'
import {
  decideOnboardingEntry,
  getStoredOnboardingTargetingKey,
  getStoredOnboardingVariant,
  persistOnboardingEntry,
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

const mockFlagsmith = flagsmith as jest.Mocked<typeof flagsmith>

describe('decideOnboardingEntry', () => {
  beforeEach(() => {
    storage.clear()
    jest.resetAllMocks()
    mockFlagsmith.identify.mockResolvedValue(undefined as any)
    mockFlagsmith.getContext.mockReturnValue({
      identity: { identifier: 'anon-123' },
    } as any)
  })

  it('returns the decision without persisting anything', async () => {
    // Given
    mockFlagsmith.getExperimentFlag.mockReturnValue({
      enabled: true,
      variant: 'single_page',
    } as any)

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
    } as any)

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
