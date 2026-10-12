import { watchScript } from 'common/hooks/useScript'

const SCRIPT_URL = 'https://example.com/script.js'

// jest runs in node, so stand in for the few DOM pieces watchScript uses.
class FakeScript extends EventTarget {
  async = false
  dataset: Record<string, string> = {}
  src = ''
}

let scripts: FakeScript[]

beforeEach(() => {
  scripts = []
  ;(global as any).document = {
    createElement: () => new FakeScript(),
    head: { appendChild: (script: FakeScript) => scripts.push(script) },
    querySelector: (selector: string) =>
      scripts.find((script) => selector === `script[src="${script.src}"]`) ??
      null,
  }
})

describe('watchScript', () => {
  it('adds the script once and reports when it loads', () => {
    // Given
    const onResult = jest.fn()

    // When
    watchScript(SCRIPT_URL, onResult)
    scripts[0].dispatchEvent(new Event('load'))

    // Then
    expect(scripts).toHaveLength(1)
    expect(onResult).toHaveBeenCalledWith('loaded')
  })

  it('waits for a script that is still loading', () => {
    // Given
    watchScript(SCRIPT_URL, jest.fn())
    const onResult = jest.fn()

    // When
    watchScript(SCRIPT_URL, onResult)

    // Then
    expect(onResult).not.toHaveBeenCalled()
    scripts[0].dispatchEvent(new Event('load'))
    expect(onResult).toHaveBeenCalledWith('loaded')
    expect(scripts).toHaveLength(1)
  })

  it('reports a script that failed to load', () => {
    // Given
    watchScript(SCRIPT_URL, jest.fn())
    scripts[0].dispatchEvent(new Event('error'))
    const onResult = jest.fn()

    // When
    watchScript(SCRIPT_URL, onResult)

    // Then
    expect(onResult).toHaveBeenCalledWith('error')
  })

  it('treats a script added elsewhere as loaded', () => {
    // Given
    const script = new FakeScript()
    script.src = SCRIPT_URL
    scripts.push(script)
    const onResult = jest.fn()

    // When
    watchScript(SCRIPT_URL, onResult)

    // Then
    expect(onResult).toHaveBeenCalledWith('loaded')
  })
})
