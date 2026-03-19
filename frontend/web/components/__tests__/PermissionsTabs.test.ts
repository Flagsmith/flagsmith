import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import type { Project } from 'common/types/responses'
import PermissionsTabs from 'components/PermissionsTabs'
import OrganisationStore from 'common/stores/organisation-store'

const mockRolePermissionsList = jest.fn(() => React.createElement('div'))

jest.mock('common/stores/organisation-store', () => ({
  __esModule: true,
  default: {
    getProjects: jest.fn(),
  },
}))

jest.mock('components/EditPermissions', () => ({
  EditPermissionsModal: () => React.createElement('div'),
  __esModule: true,
}))

jest.mock('components/navigation/TabMenu/Tabs', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}))

jest.mock('components/navigation/TabMenu/TabItem', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}))

jest.mock('components/base/forms/Input', () => ({
  __esModule: true,
  default: () => React.createElement('input'),
}))

jest.mock('components/RolePermissionsList', () => ({
  __esModule: true,
  default: (props: unknown) => {
    mockRolePermissionsList(props)
    return React.createElement('div')
  },
}))

jest.mock('components/ProjectFilter', () => ({
  __esModule: true,
  default: () => React.createElement('div'),
}))

jest.mock('components/PlanBasedAccess', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}))

jest.mock('components/WarningMessage', () => ({
  __esModule: true,
  default: () => React.createElement('div'),
}))

jest.mock('common/utils/utils', () => ({
  __esModule: true,
  default: {
    safeParseEventValue: () => '',
  },
}))

const getProjectsMock = OrganisationStore.getProjects as jest.MockedFunction<
  typeof OrganisationStore.getProjects
>

describe('PermissionsTabs', () => {
  const globalWithRow = global as typeof globalThis & { Row?: unknown }
  const originalRow = globalWithRow.Row

  beforeAll(() => {
    globalWithRow.Row = ({ children, ...props }: Record<string, unknown>) =>
      React.createElement('div', props, children)
  })

  afterAll(() => {
    if (originalRow) {
      globalWithRow.Row = originalRow
      return
    }

    delete globalWithRow.Row
  })

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('uses an empty project list while organisation projects are loading', () => {
    getProjectsMock.mockReturnValue(undefined as unknown as Project[])

    expect(() =>
      renderToStaticMarkup(React.createElement(PermissionsTabs, { orgId: 1 })),
    ).not.toThrow()

    const projectPermissionsCall = mockRolePermissionsList.mock.calls.find(
      ([props]) => (props as { level?: string }).level === 'project',
    )?.[0] as { mainItems?: unknown[] } | undefined

    expect(projectPermissionsCall?.mainItems).toEqual([])
  })
})
