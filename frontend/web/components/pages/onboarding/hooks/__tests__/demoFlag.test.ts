import { ProjectFlag, Tag } from 'common/types/responses'
import {
  DEMO_FLAG_NAME,
  findDemoFlag,
  shouldSeedDemoFlag,
} from 'components/pages/onboarding/hooks/demoFlag'

const flag = (name: string, tags: number[] = []): ProjectFlag =>
  ({ id: name.length, name, tags } as ProjectFlag)

const onboardingTag = { id: 7, label: 'Onboarding' } as Tag

describe('shouldSeedDemoFlag', () => {
  it('seeds into an empty project', () => {
    expect(shouldSeedDemoFlag([])).toBe(true)
  })

  it('seeds nothing once the project has flags of its own', () => {
    // The customer's list. A flag they did not ask for would appear in every
    // environment, production included.
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
