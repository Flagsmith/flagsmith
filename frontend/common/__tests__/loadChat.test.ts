import AccountStore from 'common/stores/account-store'
import data from 'common/data/base/_data'
import Utils from 'common/utils/utils'
import { getChatProvider, identifyChatUser, openChat } from 'common/loadChat'

jest.mock('common/utils/utils', () => ({
  getFlagsmithHasFeature: jest.fn(),
  getFlagsmithValue: jest.fn(),
  isOrgOnFreePlan: jest.fn(),
}))
jest.mock('common/stores/account-store', () => ({ getUser: jest.fn() }))
jest.mock('common/data/base/_data', () => ({ get: jest.fn() }))
jest.mock('common/project', () => ({ api: 'https://api.test/api/v1/' }))

const mockUtils = Utils as jest.Mocked<typeof Utils>
const mockAccountStore = AccountStore as jest.Mocked<typeof AccountStore>
const mockData = data as jest.Mocked<typeof data>

const USER_EMAIL = 'user@example.com'
const TOKEN_URL = 'https://api.test/api/v1/auth/users/me/hubspot-chat-token/'

// The HubSpot load waits for the token request.
const flushPromises = () => new Promise((resolve) => setImmediate(resolve))

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
  mockAccountStore.getUser.mockReturnValue({ email: USER_EMAIL } as any)
  mockData.get.mockResolvedValue({ token: 'test-token' })
  // jest runs in node, so give the module a minimal window.
  ;(global as any).window = {
    hsConversationsSettings: { loadImmediately: false },
    location: { href: '' },
  }
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

  it('loads the HubSpot widget open when it is not loaded yet', async () => {
    // Given
    setFlags(['hubspot_chat'])
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }

    // When
    openChat()
    await flushPromises()

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
  it('hides Pylon and loads HubSpot when hubspot_chat is on', async () => {
    // Given
    setFlags(['hubspot_chat', 'pylon_chat'])
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }
    window.Pylon = jest.fn()

    // When
    identifyChatUser()
    await flushPromises()

    // Then
    expect(window.Pylon).toHaveBeenCalledWith('hideChatBubble')
    expect(widget.load).toHaveBeenCalledWith({ widgetOpen: false })
  })

  it('queues the HubSpot load until the API is ready', async () => {
    // Given
    setFlags(['hubspot_chat'])

    // When
    identifyChatUser()
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }
    window.hsConversationsOnReady?.forEach((callback) => callback())
    await flushPromises()

    // Then
    expect(widget.load).toHaveBeenCalledWith({ widgetOpen: false })
  })

  it('queues the HubSpot load only once while the API is not ready', () => {
    // Given
    setFlags(['hubspot_chat'])

    // When
    identifyChatUser()
    identifyChatUser()

    // Then
    expect(window.hsConversationsOnReady).toHaveLength(1)
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

describe('HubSpot visitor identification', () => {
  it('identifies the user before loading the widget', async () => {
    // Given
    setFlags(['hubspot_chat'])
    const widget = hubSpotWidget(false)
    let settingsAtLoad
    widget.load.mockImplementation(() => {
      settingsAtLoad = { ...window.hsConversationsSettings }
    })
    window.HubSpotConversations = { widget }

    // When
    identifyChatUser()
    await flushPromises()

    // Then
    expect(mockData.get).toHaveBeenCalledWith(TOKEN_URL)
    expect(settingsAtLoad).toEqual({
      identificationEmail: USER_EMAIL,
      identificationToken: 'test-token',
      loadImmediately: false,
    })
  })

  it('loads the widget anonymously when the token request fails', async () => {
    // Given
    setFlags(['hubspot_chat'])
    mockData.get.mockRejectedValue(new Error('Not found'))
    jest.spyOn(console, 'error').mockImplementation(() => {})
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }

    // When
    identifyChatUser()
    await flushPromises()

    // Then
    expect(widget.load).toHaveBeenCalledWith({ widgetOpen: false })
    expect(window.hsConversationsSettings).toEqual({ loadImmediately: false })
  })

  it("drops a previous user's identity when no new token comes back", async () => {
    // Given
    setFlags(['hubspot_chat'])
    mockData.get.mockResolvedValue({})
    window.hsConversationsSettings = {
      identificationEmail: 'previous@example.com',
      identificationToken: 'previous-token',
      loadImmediately: false,
    }
    window.HubSpotConversations = { widget: hubSpotWidget(false) }

    // When
    identifyChatUser()
    await flushPromises()

    // Then
    expect(window.hsConversationsSettings).toEqual({ loadImmediately: false })
  })

  it('fetches one token and loads once for overlapping calls', async () => {
    // Given
    setFlags(['hubspot_chat'])
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }

    // When
    identifyChatUser()
    openChat()
    await flushPromises()

    // Then
    expect(mockData.get).toHaveBeenCalledTimes(1)
    expect(widget.load).toHaveBeenCalledTimes(1)
    expect(widget.load).toHaveBeenCalledWith({ widgetOpen: true })
  })

  it('does not fetch a token when the widget is already loaded', async () => {
    // Given
    setFlags(['hubspot_chat'])
    window.HubSpotConversations = { widget: hubSpotWidget(true) }

    // When
    identifyChatUser()
    await flushPromises()

    // Then
    expect(mockData.get).not.toHaveBeenCalled()
  })

  it('does not load the widget when the org changed during the fetch', async () => {
    // Given
    setFlags(['hubspot_chat'])
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }

    // When
    identifyChatUser()
    mockUtils.isOrgOnFreePlan.mockReturnValue(true)
    await flushPromises()

    // Then
    expect(widget.load).not.toHaveBeenCalled()
  })
})
