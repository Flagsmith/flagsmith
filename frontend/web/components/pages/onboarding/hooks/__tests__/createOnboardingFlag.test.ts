import {
  createOnboardingFlag,
  ensureOnboardingVariation,
} from 'components/pages/onboarding/hooks/createOnboardingFlag'
import { ProjectFlag } from 'common/types/responses'

const initiate = jest.fn((args: unknown) => ({ args, type: 'createFlag' }))
const createMultivariateOption = jest.fn()

jest.mock('common/services/useProjectFlag', () => ({
  projectFlagService: {
    endpoints: { createProjectFlag: { initiate: (a: unknown) => initiate(a) } },
  },
}))
jest.mock('common/services/useMultivariateOption', () => ({
  createMultivariateOption: (...a: unknown[]) => createMultivariateOption(...a),
}))

const flag = (multivariate_options: unknown[] = []) =>
  ({
    id: 7,
    multivariate_options,
    name: 'show_demo_button',
    project: 3,
  } as unknown as ProjectFlag)

const storeReturning = (created: ProjectFlag) =>
  ({
    dispatch: jest.fn(() => ({ unwrap: () => Promise.resolve(created) })),
  } as any)

const expectedOption = {
  body: {
    default_percentage_allocation: 0,
    feature: 7,
    key: 'variant',
    string_value: 'variant',
    type: 'unicode',
  },
  feature_id: 7,
  project_id: 3,
}

beforeEach(() => {
  initiate.mockClear()
  createMultivariateOption.mockReset().mockResolvedValue({ data: {} })
})

describe('createOnboardingFlag', () => {
  it('creates a multivariate flag with a control value and one 0% variation', async () => {
    const store = storeReturning(flag())

    const created = await createOnboardingFlag(store, {
      description: 'desc',
      name: 'show_demo_button',
      projectId: 3,
      tags: [1],
    })

    expect(created).toEqual(flag())
    expect(initiate).toHaveBeenCalledWith({
      body: {
        description: 'desc',
        initial_value: 'control',
        name: 'show_demo_button',
        project: 3,
        tags: [1],
        type: 'MULTIVARIATE',
      },
      project_id: 3,
    })
    expect(createMultivariateOption).toHaveBeenCalledTimes(1)
    expect(createMultivariateOption).toHaveBeenCalledWith(store, expectedOption)
  })

  it('throws when the variation request fails', async () => {
    createMultivariateOption.mockResolvedValue({ error: { status: 500 } })

    await expect(
      createOnboardingFlag(storeReturning(flag()), {
        name: 'show_demo_button',
        projectId: 3,
      }),
    ).rejects.toEqual({ status: 500 })
  })
})

describe('ensureOnboardingVariation', () => {
  it.each`
    options        | calls
    ${[]}          | ${1}
    ${[{ id: 1 }]} | ${0}
    ${undefined}   | ${1}
  `(
    'creates the variation $calls time(s) when options are $options',
    async ({ calls, options }) => {
      await ensureOnboardingVariation(storeReturning(flag()), flag(options))

      expect(createMultivariateOption).toHaveBeenCalledTimes(calls)
    },
  )
})
