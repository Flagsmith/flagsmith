import { ProjectFlag, Tag } from 'common/types/responses'
import {
  DEMO_FLAG_NAME,
  ONBOARDING_TAG,
  canResumeDemoFlag,
  findDemoFlag,
  findOnboardingTag,
  shouldSeedDemoFlag,
} from 'components/pages/onboarding/bootstrap/demoFlag'

const flag = (name: string, tags: number[] = []): ProjectFlag =>
  ({ id: name.length, name, tags } as ProjectFlag)

const onboardingTag = { id: 7, ...ONBOARDING_TAG } as Tag

describe('findOnboardingTag', () => {
  it('finds the tag a previous run created', () => {
    expect(
      findOnboardingTag([{ id: 3, label: 'Backend' } as Tag, onboardingTag]),
    ).toBe(onboardingTag)
  })

  it('ignores a tag the customer labelled Onboarding themselves', () => {
    const theirs = {
      description: 'Flags behind our signup flow',
      id: 9,
      label: 'Onboarding',
    } as Tag
    expect(findOnboardingTag([theirs])).toBeUndefined()
  })
})

describe('shouldSeedDemoFlag', () => {
  it('seeds into an empty project', () => {
    expect(shouldSeedDemoFlag([])).toBe(true)
  })

  it('seeds nothing once the project has flags of its own', () => {
    expect(shouldSeedDemoFlag([flag('checkout_v2')])).toBe(false)
  })
})

describe('findDemoFlag', () => {
  it('finds a previous run by its tag, whatever it was renamed to', () => {
    const renamed = flag('my_own_name', [onboardingTag.id])
    expect(findDemoFlag([flag('checkout_v2'), renamed], onboardingTag)).toBe(
      renamed,
    )
  })

  it('prefers the tag over the name when both are present', () => {
    const tagged = flag('renamed_by_hand', [onboardingTag.id])
    const named = flag(DEMO_FLAG_NAME)
    expect(findDemoFlag([named, tagged], onboardingTag)).toBe(tagged)
  })

  it('falls back to the name when the tag is missing', () => {
    const seeded = flag(DEMO_FLAG_NAME)
    expect(findDemoFlag([flag('checkout_v2'), seeded], undefined)).toBe(seeded)
  })

  it('finds nothing in a project that never ran the tour', () => {
    expect(findDemoFlag([flag('checkout_v2')], onboardingTag)).toBeUndefined()
  })

  it('finds nothing in an empty project', () => {
    expect(findDemoFlag([], onboardingTag)).toBeUndefined()
  })
})

describe('canResumeDemoFlag', () => {
  it('resumes the run a refresh interrupted, where ours is the only flag', () => {
    const seeded = flag(DEMO_FLAG_NAME, [onboardingTag.id])
    expect(canResumeDemoFlag([seeded], seeded)).toBe(true)
  })

  it('stops once the project holds flags of its own', () => {
    const seeded = flag(DEMO_FLAG_NAME, [onboardingTag.id])
    expect(canResumeDemoFlag([seeded, flag('checkout_v2')], seeded)).toBe(false)
  })
})
