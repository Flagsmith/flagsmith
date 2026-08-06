import { ProjectFlag, Tag } from 'common/types/responses'
import {
  ONBOARDING_FLAG_NAME,
  findOnboardingFlag,
  shouldSeedOnboardingFlag,
} from 'components/pages/onboarding/bootstrap/onboardingFlag'

const flag = (name: string, tags: number[] = []): ProjectFlag =>
  ({ id: name.length, name, tags } as ProjectFlag)

const onboardingTag = { id: 7, label: 'Onboarding' } as Tag

describe('shouldSeedOnboardingFlag', () => {
  it('seeds into an empty project', () => {
    expect(shouldSeedOnboardingFlag([])).toBe(true)
  })

  it('seeds nothing once the project has flags of its own', () => {
    expect(shouldSeedOnboardingFlag([flag('checkout_v2')])).toBe(false)
  })
})

describe('findOnboardingFlag', () => {
  it('finds a previous run by its tag, whatever it was renamed to', () => {
    const renamed = flag('my_own_name', [onboardingTag.id])
    expect(
      findOnboardingFlag([flag('checkout_v2'), renamed], onboardingTag),
    ).toBe(renamed)
  })

  it('prefers the tag over the name when both are present', () => {
    const tagged = flag('renamed_by_hand', [onboardingTag.id])
    const named = flag(ONBOARDING_FLAG_NAME)
    expect(findOnboardingFlag([named, tagged], onboardingTag)).toBe(tagged)
  })

  it('falls back to the name when the tag is missing', () => {
    const seeded = flag(ONBOARDING_FLAG_NAME)
    expect(findOnboardingFlag([flag('checkout_v2'), seeded], undefined)).toBe(
      seeded,
    )
  })

  it('finds nothing in a project that never ran the tour', () => {
    expect(
      findOnboardingFlag([flag('checkout_v2')], onboardingTag),
    ).toBeUndefined()
  })

  it('finds nothing in an empty project', () => {
    expect(findOnboardingFlag([], onboardingTag)).toBeUndefined()
  })
})
