const listeners: Record<string, ((event: Event) => void)[]> = {}
let systemDarkMode = false
let systemListener: (() => void) | undefined

const createClassList = () => {
  const classes = new Set<string>()
  return {
    add: (className: string) => classes.add(className),
    contains: (className: string) => classes.has(className),
    remove: (className: string) => classes.delete(className),
  }
}

const loadDarkMode = async () => {
  jest.resetModules()
  return import('./darkMode')
}

const dispatchStorageEvent = (key: string) => {
  window.dispatchEvent({
    key,
    type: 'storage',
  } as StorageEvent)
}

describe('darkMode', () => {
  beforeEach(() => {
    const storage = new Map<string, string>()
    const documentElementAttributes = new Map<string, string>()
    systemDarkMode = false
    systemListener = undefined
    Object.keys(listeners).forEach((key) => {
      listeners[key] = []
    })

    Object.defineProperty(global, 'localStorage', {
      configurable: true,
      value: {
        getItem: jest.fn((key: string) => storage.get(key) ?? null),
        setItem: jest.fn((key: string, value: string) => {
          storage.set(key, value)
        }),
      },
    })

    Object.defineProperty(global, 'document', {
      configurable: true,
      value: {
        body: {
          classList: createClassList(),
        },
        documentElement: {
          getAttribute: jest.fn(
            (name: string) => documentElementAttributes.get(name) ?? null,
          ),
          removeAttribute: jest.fn((name: string) => {
            documentElementAttributes.delete(name)
          }),
          setAttribute: jest.fn((name: string, value: string) => {
            documentElementAttributes.set(name, value)
          }),
        },
      },
    })

    Object.defineProperty(global, 'window', {
      configurable: true,
      value: {
        addEventListener: jest.fn(
          (eventName: string, callback: (event: Event) => void) => {
            listeners[eventName] = listeners[eventName] ?? []
            listeners[eventName].push(callback)
          },
        ),
        dispatchEvent: jest.fn((event: Event) => {
          listeners[event.type]?.forEach((callback) => callback(event))
          return true
        }),
        matchMedia: jest.fn(() => ({
          addEventListener: jest.fn(
            (_eventName: string, callback: () => void) => {
              systemListener = callback
            },
          ),
          addListener: jest.fn((callback: () => void) => {
            systemListener = callback
          }),
          get matches() {
            return systemDarkMode
          },
        })),
        removeEventListener: jest.fn(
          (eventName: string, callback: (event: Event) => void) => {
            listeners[eventName] = (listeners[eventName] ?? []).filter(
              (listener) => listener !== callback,
            )
          },
        ),
      },
    })
  })

  it('uses the legacy dark mode value when no theme preference exists', async () => {
    localStorage.setItem('dark_mode', 'true')

    const { getDarkMode, getThemePreference } = await loadDarkMode()

    expect(getThemePreference()).toBe('dark')
    expect(getDarkMode()).toBe(true)
    expect(document.body.classList.contains('dark')).toBe(true)
    expect(document.documentElement.getAttribute('data-bs-theme')).toBe('dark')
  })

  it('stores explicit light and dark preferences', async () => {
    const { getDarkMode, getThemePreference, setThemePreference } =
      await loadDarkMode()

    setThemePreference('dark')
    expect(getThemePreference()).toBe('dark')
    expect(getDarkMode()).toBe(true)
    expect(localStorage.getItem('theme_preference')).toBe('dark')
    expect(localStorage.getItem('dark_mode')).toBe('true')

    setThemePreference('light')
    expect(getThemePreference()).toBe('light')
    expect(getDarkMode()).toBe(false)
    expect(localStorage.getItem('dark_mode')).toBe('false')
    expect(document.body.classList.contains('dark')).toBe(false)
    expect(document.documentElement.getAttribute('data-bs-theme')).toBeNull()
  })

  it('resolves the system preference from prefers-color-scheme', async () => {
    systemDarkMode = true
    const { getDarkMode, getThemePreference, setThemePreference } =
      await loadDarkMode()

    setThemePreference('system')

    expect(getThemePreference()).toBe('system')
    expect(getDarkMode()).toBe(true)
    expect(localStorage.getItem('theme_preference')).toBe('system')
    expect(localStorage.getItem('dark_mode')).toBe('true')
  })

  it('updates when another tab changes the preference', async () => {
    const { getDarkMode, listenToThemePreference } = await loadDarkMode()
    const callback = jest.fn()

    listenToThemePreference(callback)
    localStorage.setItem('theme_preference', 'dark')
    dispatchStorageEvent('theme_preference')

    expect(callback).toHaveBeenCalledTimes(1)
    expect(getDarkMode()).toBe(true)
    expect(document.body.classList.contains('dark')).toBe(true)
  })

  it('ignores legacy storage events once a theme preference exists', async () => {
    systemDarkMode = true
    const { getDarkMode, listenToThemePreference } = await loadDarkMode()
    const callback = jest.fn()

    listenToThemePreference(callback)
    localStorage.setItem('theme_preference', 'system')
    dispatchStorageEvent('theme_preference')

    expect(callback).toHaveBeenCalledTimes(1)
    expect(getDarkMode()).toBe(true)
    expect(document.body.classList.contains('dark')).toBe(true)

    localStorage.setItem('dark_mode', 'false')
    dispatchStorageEvent('dark_mode')

    expect(callback).toHaveBeenCalledTimes(1)
    expect(getDarkMode()).toBe(true)
    expect(document.body.classList.contains('dark')).toBe(true)
  })

  it('still updates from legacy storage when no theme preference exists', async () => {
    const { getDarkMode, listenToThemePreference } = await loadDarkMode()
    const callback = jest.fn()

    listenToThemePreference(callback)
    localStorage.setItem('dark_mode', 'true')
    dispatchStorageEvent('dark_mode')

    expect(callback).toHaveBeenCalledTimes(1)
    expect(getDarkMode()).toBe(true)
    expect(document.body.classList.contains('dark')).toBe(true)
  })

  it('reacts to system colour scheme changes while using the system preference', async () => {
    systemDarkMode = false
    const { getDarkMode, setThemePreference } = await loadDarkMode()

    setThemePreference('system')
    expect(getDarkMode()).toBe(false)

    systemDarkMode = true
    systemListener?.()

    expect(getDarkMode()).toBe(true)
    expect(document.body.classList.contains('dark')).toBe(true)
  })
})
