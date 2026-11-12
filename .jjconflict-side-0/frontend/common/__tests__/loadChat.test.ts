import AccountStore from 'common/stores/account-store'
import Utils from 'common/utils/utils'
import { getHubspotChatToken } from 'common/services/useHubspotChatToken'
import { Res } from 'common/types/responses'
import {
  getChatProvider,
  hideChat,
  identifyChatUser,
  openChat,
} from 'common/loadChat'

jest.mock('common/utils/utils', () => ({
  getFlagsmithHasFeature: jest.fn(),
  getFlagsmithValue: jest.fn(),
  isOrgOnFreePlan: jest.fn(),
}))
jest.mock('common/stores/account-store', () => ({ getUser: jest.fn() }))
jest.mock('common/store', () => ({ getStore: () => 'store' }))
jest.mock('common/services/useHubspotChatToken', () => ({
  getHubspotChatToken: jest.fn(),
}))
jest.mock('common/project', () => ({ api: 'https://api.test/api/v1/' }))

const mockUtils = Utils as jest.Mocked<typeof Utils>
const mockAccountStore = AccountStore as jest.Mocked<typeof AccountStore>
const mockGetToken = getHubspotChatToken as jest.MockedFunction<
  typeof getHubspotChatToken
>

const USER_ID = 1
const TOKEN: Res['hubspotChatToken'] = {
  email: 'user@example.com',
  token: 'test-token',
}

type TokenResult = { data?: Res['hubspotChatToken']; error?: unknown }

// Lets a test decide when (and with what) the token request resolves.
const deferredToken = () => {
  let resolve: (result: TokenResult) => void = () => {}
  const promise = new Promise<TokenResult>((r) => {
    resolve = r
  })
  return { promise, resolve }
}

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
  mockAccountStore.getUser.mockReturnValue({ id: USER_ID })
  mockGetToken.mockResolvedValue({ data: TOKEN })
  // jest runs in node, so give the module a minimal window.
  ;(global as any).window = {
    hsConversationsSettings: { loadImmediately: false },
    location: { href: '' },
  }
  // Resets the module's HubSpot load state between tests.
  hideChat()
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
    expect(mockGetToken).toHaveBeenCalledWith(
      'store',
      { userId: USER_ID },
      { subscribe: false },
    )
    expect(settingsAtLoad).toEqual({
      identificationEmail: TOKEN.email,
      identificationToken: TOKEN.token,
      loadImmediately: false,
    })
  })

  it.each([
    { logged: false, status: 404 },
    { logged: true, status: 500 },
  ])(
    'loads the widget anonymously when the token request returns $status',
    async ({ logged, status }) => {
      // Given
      setFlags(['hubspot_chat'])
      mockGetToken.mockResolvedValue({ error: { status } })
      const consoleError = jest
        .spyOn(console, 'error')
        .mockImplementation(() => {})
      const widget = hubSpotWidget(false)
      window.HubSpotConversations = { widget }

      // When
      identifyChatUser()
      await flushPromises()

      // Then
      expect(widget.load).toHaveBeenCalledWith({ widgetOpen: false })
      expect(window.hsConversationsSettings).toEqual({ loadImmediately: false })
      expect(consoleError).toHaveBeenCalledTimes(logged ? 1 : 0)
    },
  )

  it("drops a previous user's identity when no new token comes back", async () => {
    // Given
    setFlags(['hubspot_chat'])
    mockGetToken.mockResolvedValue({})
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
    expect(mockGetToken).toHaveBeenCalledTimes(1)
    expect(widget.load).toHaveBeenCalledTimes(1)
    expect(widget.load).toHaveBeenCalledWith({ widgetOpen: true })
  })

  it('does not fetch or load again while the widget is still loading', async () => {
    // Given
    setFlags(['hubspot_chat'])
    // status().loaded stays false until HubSpot's iframe is ready.
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }
    identifyChatUser()
    await flushPromises()

    // When
    identifyChatUser()
    openChat()
    await flushPromises()

    // Then
    expect(mockGetToken).toHaveBeenCalledTimes(1)
    expect(widget.load).toHaveBeenCalledTimes(1)
    expect(widget.open).toHaveBeenCalled()
  })

  it('does not fetch a token when the widget is already loaded', async () => {
    // Given
    setFlags(['hubspot_chat'])
    window.HubSpotConversations = { widget: hubSpotWidget(true) }

    // When
    identifyChatUser()
    await flushPromises()

    // Then
    expect(mockGetToken).not.toHaveBeenCalled()
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

  it('does not load the widget when the user logs out during the fetch', async () => {
    // Given
    setFlags(['hubspot_chat'])
    const token = deferredToken()
    mockGetToken.mockReturnValue(token.promise)
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }

    // When
    identifyChatUser()
    hideChat()
    token.resolve({ data: TOKEN })
    await flushPromises()

    // Then
    expect(widget.remove).toHaveBeenCalled()
    expect(widget.load).not.toHaveBeenCalled()
    expect(window.hsConversationsSettings).toEqual({ loadImmediately: false })
  })

  it("loads the next user's identity when they log in during the previous fetch", async () => {
    // Given
    setFlags(['hubspot_chat'])
    const previousToken = deferredToken()
    const nextToken = deferredToken()
    const NEXT_TOKEN: Res['hubspotChatToken'] = {
      email: 'next@example.com',
      token: 'next-token',
    }
    mockGetToken
      .mockReturnValueOnce(previousToken.promise)
      .mockReturnValueOnce(nextToken.promise)
    const widget = hubSpotWidget(false)
    window.HubSpotConversations = { widget }

    // When
    identifyChatUser()
    hideChat()
    mockAccountStore.getUser.mockReturnValue({ id: 2 })
    identifyChatUser()
    nextToken.resolve({ data: NEXT_TOKEN })
    await flushPromises()
    previousToken.resolve({ data: TOKEN })
    await flushPromises()

    // Then
    expect(mockGetToken).toHaveBeenLastCalledWith(
      'store',
      { userId: 2 },
      { subscribe: false },
    )
    expect(widget.load).toHaveBeenCalledTimes(1)
    expect(window.hsConversationsSettings).toEqual({
      identificationEmail: NEXT_TOKEN.email,
      identificationToken: NEXT_TOKEN.token,
      loadImmediately: false,
    })
  })
})
