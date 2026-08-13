import { ProjectFlag, Tag } from 'common/types/responses'
import {
  DEMO_FLAG_DESCRIPTION,
  DEMO_FLAG_NAME,
  ONBOARDING_TAG,
  findDemoFlag,
  findOnboardingTag,
} from 'components/pages/onboarding/bootstrap/demoFlag'

const flag = (
  name: string,
  { description = '', tags = [] }: { description?: string; tags?: number[] } = {},
): ProjectFlag => ({ description, id: name.length, name, tags } as ProjectFlag)

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

describe('findDemoFlag', () => {
  it('finds a previous run by its tag, whatever it was renamed to', () => {
    const renamed = flag('my_own_name', { tags: [onboardingTag.id] })
    expect(
      findDemoFlag([flag('checkout_v2'), renamed], onboardingTag),
    ).toBe(renamed)
  })

  it('prefers the tag over anything else when both are present', () => {
    const tagged = flag('renamed_by_hand', { tags: [onboardingTag.id] })
    const named = flag(DEMO_FLAG_NAME)
    expect(findDemoFlag([named, tagged], onboardingTag)).toBe(tagged)
  })

  it('falls back to our description when the tag is gone', () => {
    // The rename carries the description over, so it outlives the name.
    const renamed = flag('my_own_name', { description: DEMO_FLAG_DESCRIPTION })
    expect(findDemoFlag([flag('checkout_v2'), renamed], undefined)).toBe(renamed)
  })

  it('falls back to the name for a flag seeded before we set a description', () => {
    const legacy = flag(DEMO_FLAG_NAME)
    expect(findDemoFlag([flag('checkout_v2'), legacy], undefined)).toBe(legacy)
  })

  it('finds nothing in a project that never ran the tour', () => {
    expect(findDemoFlag([flag('checkout_v2')], onboardingTag)).toBeUndefined()
  })

  it('finds nothing in an empty project', () => {
    expect(findDemoFlag([], onboardingTag)).toBeUndefined()
  })
})
