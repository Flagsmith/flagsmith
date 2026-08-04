import { ProjectFlag, Tag } from 'common/types/responses'
import {
  DEMO_FLAG_NAME,
  findDemoFlag,
  shouldSeedDemoFlag,
} from 'components/pages/onboarding/bootstrap/demoFlag'

const flag = (name: string, tags: number[] = []): ProjectFlag =>
  ({ id: name.length, name, tags } as ProjectFlag)

const onboardingTag = { id: 7, label: 'Onboarding' } as Tag

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
    const tagged = flag('renamed_demo', [onboardingTag.id])
    const named = flag(DEMO_FLAG_NAME)
    expect(findDemoFlag([named, tagged], onboardingTag)).toBe(tagged)
  })

  it('falls back to the name when the tag is missing', () => {
    const demo = flag(DEMO_FLAG_NAME)
    expect(findDemoFlag([flag('checkout_v2'), demo], undefined)).toBe(demo)
  })

  it('finds nothing in a project that never ran the tour', () => {
    expect(findDemoFlag([flag('checkout_v2')], onboardingTag)).toBeUndefined()
  })

  it('finds nothing in an empty project', () => {
    expect(findDemoFlag([], onboardingTag)).toBeUndefined()
  })
})
