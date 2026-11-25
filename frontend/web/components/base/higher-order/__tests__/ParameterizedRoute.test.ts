import React from 'react'
import { Route } from 'react-router-dom'
import NotFoundPage from 'components/pages/NotFoundPage'
import { ParameterizedRoute } from 'components/base/higher-order/ParameterizedRoute'

jest.mock('components/pages/NotFoundPage', () => () => null)
jest.mock('components/EnvironmentReadyChecker', () => () => null)
jest.mock('components/providers/RouteContext', () => ({
  RouteProvider: () => null,
}))
jest.mock('react-router-dom', () => ({
  Route: () => null,
}))

const DummyComponent = () => null

describe('ParameterizedRoute', () => {
  it('does not throw when computedMatch is undefined', () => {
    const element = ParameterizedRoute({
      component: DummyComponent,
      path: '/example',
    })

    expect(React.isValidElement(element)).toBe(true)
    expect(element.type).toBe(Route)
    expect(element.props.component).toBe(DummyComponent)
  })

  it('renders NotFoundPage when organisationId or projectId is not numeric', () => {
    const element = ParameterizedRoute({
      component: DummyComponent,
      computedMatch: { params: { organisationId: 'abc' } },
      path: '/organisation/:organisationId',
    })

    expect(element.props.component).toBe(NotFoundPage)
  })

  it('uses render prop when valid numeric params are provided', () => {
    const element = ParameterizedRoute({
      component: DummyComponent,
      computedMatch: { params: { organisationId: '1', projectId: '2' } },
      path: '/organisation/:organisationId/project/:projectId',
    })

    expect(typeof element.props.render).toBe('function')
  })
})
