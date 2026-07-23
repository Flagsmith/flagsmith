/**
 * @jest-environment jsdom
 */
import React from 'react'
import { render } from '@testing-library/react'
import '@testing-library/jest-dom'

jest.mock('@flagsmith/flagsmith', () => ({
  __esModule: true,
  default: {
    getContext: jest.fn(),
    loadingState: undefined,
  },
}))
// Identity HOC: keeps the test off config-store, whose import calls
// flagsmith.init(). Re-renders are driven with rerender() instead.
jest.mock('common/providers/ConfigProvider', () => ({
  __esModule: true,
  default: (Component: unknown) => Component,
}))
jest.mock('project/api', () => ({
  __esModule: true,
  default: { trackTraits: jest.fn() },
}))
jest.mock('common/utils/getOnboardingVariant', () => ({
  getOnboardingVariant: jest.fn(),
  isSinglePageOnboarding: jest.fn(),
}))
jest.mock('components/pages/GettingStartedPage', () => {
  const React = require('react')
  return {
    __esModule: true,
    default: () => React.createElement('div', { 'data-testid': 'legacy-page' }),
  }
})
jest.mock('../OnboardingFlow', () => {
  const React = require('react')
  return {
    __esModule: true,
    default: () =>
      React.createElement('div', { 'data-testid': 'onboarding-flow' }),
  }
})

import flagsmith from '@flagsmith/flagsmith'
import API from 'project/api'
import {
  getOnboardingVariant,
  isSinglePageOnboarding,
} from 'common/utils/getOnboardingVariant'
import GettingStartedGate from 'components/pages/onboarding/GettingStartedGate'

const mockGetContext = flagsmith.getContext as jest.Mock
const mockTrackTraits = API.trackTraits as jest.Mock
const mockGetVariant = getOnboardingVariant as jest.Mock
const mockIsSinglePage = isSinglePageOnboarding as jest.Mock

const setLoadingState = (overrides: Record<string, unknown> = {}) => {
  ;(flagsmith as any).loadingState = {
    error: null,
    isFetching: false,
    isLoading: false,
    source: 'SERVER',
    ...overrides,
  }
}

const settled = () => {
  setLoadingState()
  mockGetContext.mockReturnValue({ identity: { identifier: '42' } })
}

beforeEach(() => {
  mockGetVariant.mockReturnValue('single_page')
  mockIsSinglePage.mockReturnValue(true)
  mockGetContext.mockReturnValue({ identity: { identifier: '42' } })
  setLoadingState()
})

describe('GettingStartedGate variant tagging', () => {
  it('does not write the trait while flags are being fetched', () => {
    setLoadingState({ isFetching: true })
    render(<GettingStartedGate />)
    expect(mockTrackTraits).not.toHaveBeenCalled()
  })

  it('does not write the trait when flags come from cache', () => {
    setLoadingState({ source: 'CACHE' })
    render(<GettingStartedGate />)
    expect(mockTrackTraits).not.toHaveBeenCalled()
  })

  it('does not write the trait before an identity is set', () => {
    mockGetContext.mockReturnValue({})
    render(<GettingStartedGate />)
    expect(mockTrackTraits).not.toHaveBeenCalled()
  })

  it('writes the trait once when flags are server-answered for the identity', () => {
    settled()
    render(<GettingStartedGate />)
    expect(mockTrackTraits).toHaveBeenCalledTimes(1)
    expect(mockTrackTraits).toHaveBeenCalledWith({
      onboarding_variant: 'single_page',
    })
  })

  it('mounts mid-fetch, then writes once when the fetch settles', () => {
    setLoadingState({ isFetching: true })
    const { rerender } = render(<GettingStartedGate />)
    expect(mockTrackTraits).not.toHaveBeenCalled()

    settled()
    rerender(<GettingStartedGate />)
    expect(mockTrackTraits).toHaveBeenCalledTimes(1)
  })

  it('does not write again on re-renders when nothing changes', () => {
    settled()
    const { rerender } = render(<GettingStartedGate />)
    rerender(<GettingStartedGate />)
    expect(mockTrackTraits).toHaveBeenCalledTimes(1)
  })

  it('writes again when the variant changes', () => {
    settled()
    const { rerender } = render(<GettingStartedGate />)

    mockGetVariant.mockReturnValue('control')
    rerender(<GettingStartedGate />)
    expect(mockTrackTraits).toHaveBeenCalledTimes(2)
    expect(mockTrackTraits).toHaveBeenLastCalledWith({
      onboarding_variant: 'control',
    })
  })
})

describe('GettingStartedGate routing', () => {
  it('renders the new flow for the single-page variant', () => {
    const { getByTestId } = render(<GettingStartedGate />)
    expect(getByTestId('onboarding-flow')).toBeInTheDocument()
  })

  it('renders the legacy page for the control variant', () => {
    mockIsSinglePage.mockReturnValue(false)
    const { getByTestId } = render(<GettingStartedGate />)
    expect(getByTestId('legacy-page')).toBeInTheDocument()
  })
})
