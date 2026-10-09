import Utils from 'common/utils/utils'
import { getChatProvider, identifyChatUser, openChat } from 'common/loadChat'

jest.mock('common/utils/utils', () => ({
  getFlagsmithHasFeature: jest.fn(),
  getFlagsmithValue: jest.fn(),
  isOrgOnFreePlan: jest.fn(),
}))
jest.mock('common/stores/account-store', () => ({ getUser: jest.fn() }))
jest.mock('common/project', () => ({}))

const mockUtils = Utils as jest.Mocked<typeof Utils>

const setFlags = (enabled: string[], hubspotChatValue?: string) => {
  mockUtils.getFlagsmithHasFeature.mockImplementation((name: string) =>
    enabled.includes(name),
  )
  mockUtils.getFlagsmithValue.mockImplementation(((name: string) =>
    name === 'hubspot_chat' ? hubspotChatValue ?? null : null) as any)
}

const hubSpotWidget = (loaded: boolean) => ({
  load: jest.fn(),
  open: jest.fn(),
  remove: jest.fn(),
  status: jest.fn(() => ({ loaded })),
})

beforeEach(() => {
  jest.resetAllMocks()
  mockUtils.isOrgOnFreePlan.mockReturnValue(false)
  // jest runs in node, so give the module a minimal window.
  ;(global as any).window = { location: { href: '' } }
})

describe('getChatProvider', () => {
  it('returns hubspot when only hubspot_chat is on', () => {
    // Given
    setFlags(['hubspot_chat'])

    // When / Then
    expect(getChatProvider()).toBe('hubspot')
  })

  it('prefers hubspot while both flags are on', () => {
    // Given
    setFlags(['hubspot_chat', 'pylon_chat'])

    // When / Then
    expect(getChatProvider()).toBe('hubspot')
  })

  it('returns pylon when only pylon_chat is on', () => {
    // Given
    setFlags(['pylon_chat'])

    // When / Then
    expect(getChatProvider()).toBe('pylon')
  })

  it('keeps HubSpot to paid plans when hubspot_chat has no value', () => {
    // Given
    setFlags(['hubspot_chat', 'pylon_chat'])
    mockUtils.isOrgOnFreePlan.mockReturnValue(true)

    // When / Then
    expect(getChatProvider()).toBeNull()
  })

  it('keeps HubSpot to paid plans for any value other than all', () => {
    // Given
    setFlags(['hubspot_chat'], 'paid')
    mockUtils.isOrgOnFreePlan.mockReturnValue(true)

    // When / Then
    expect(getChatProvider()).toBeNull()
  })

  it('opens HubSpot to free plans when hubspot_chat is all', () => {
    // Given
    // Typed by hand in the dashboard, so case and spaces are forgiven.
    setFlags(['hubspot_chat'], ' All ')
    mockUtils.isOrgOnFreePlan.mockReturnValue(true)

    // When / Then
    expect(getChatProvider()).toBe('hubspot')
  })

  it('keeps Pylon to paid plans', () => {
    // Given
    setFlags(['pylon_chat'])
    mockUtils.isOrgOnFreePlan.mockReturnValue(true)

    // When / Then
    expect(getChatProvider()).toBeNull()
  })
})

describe('openChat', () => {
  it('opens a loaded HubSpot widget', () => {
    // Given
    setFlags(['hubspot_chat'])
    const widget = hubSpotWidget(true)
    window.HubSpotConversations = { widget }

    // When
    openChat()

    // Then
    expect(widget.open).toHaveBeenCalled()
    expect(window.location.href).toBe('')
  })

  it('loads the HubSpot widget open when it is not loaded yet', () => {
    // Given
    setFlags(['hubspot_chat'])
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }

    // When
    openChat()

    // Then
    expect(widget.load).toHaveBeenCalledWith({ widgetOpen: true })
  })

  it('falls back to email when the HubSpot script never loaded', () => {
    // Given
    setFlags(['hubspot_chat'])

    // When
    openChat()

    // Then
    expect(window.location.href).toBe('mailto:support@flagsmith.com')
  })

  it('falls back to email when the org has no chat', () => {
    // Given
    setFlags([])

    // When
    openChat()

    // Then
    expect(window.location.href).toBe('mailto:support@flagsmith.com')
  })
})

describe('identifyChatUser', () => {
  it('hides Pylon and loads HubSpot when hubspot_chat is on', () => {
    // Given
    setFlags(['hubspot_chat', 'pylon_chat'])
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }
    window.Pylon = jest.fn()

    // When
    identifyChatUser()

    // Then
    expect(window.Pylon).toHaveBeenCalledWith('hideChatBubble')
    expect(widget.load).toHaveBeenCalledWith()
  })

  it('queues the HubSpot load until the API is ready', () => {
    // Given
    setFlags(['hubspot_chat'])

    // When
    identifyChatUser()
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }
    window.hsConversationsOnReady?.forEach((callback) => callback())

    // Then
    expect(widget.load).toHaveBeenCalledWith()
  })

  it('removes HubSpot when the org moves to the free plan', () => {
    // Given
    setFlags(['hubspot_chat'])
    mockUtils.isOrgOnFreePlan.mockReturnValue(true)
    const widget = hubSpotWidget(true)
    window.HubSpotConversations = { widget }

    // When
    identifyChatUser()

    // Then
    expect(widget.remove).toHaveBeenCalled()
    expect(widget.load).not.toHaveBeenCalled()
  })
})
