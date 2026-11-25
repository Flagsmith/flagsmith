import JSONUpload from 'components/JSONUpload'

type DropHandler = (files: File[]) => void

let capturedOnDrop: DropHandler | undefined
let cachedCallback: DropHandler | undefined
let cachedDeps: unknown[] | undefined

jest.mock('react', () => {
  const actual = jest.requireActual('react')
  return {
    ...actual,
    useCallback: (fn: DropHandler, deps: unknown[]) => {
      const depsChanged =
        !cachedDeps ||
        deps.length !== cachedDeps.length ||
        deps.some((dep, index) => !Object.is(dep, cachedDeps?.[index]))
      if (depsChanged) {
        cachedCallback = fn
        cachedDeps = deps
      }
      return cachedCallback
    },
    useState: (initial: unknown) => [initial, jest.fn()],
  }
})

jest.mock('react-dropzone', () => ({
  useDropzone: ({ onDrop }: { onDrop: DropHandler }) => {
    capturedOnDrop = onDrop
    return {
      getInputProps: () => ({}),
      getRootProps: () => ({}),
      isDragActive: false,
    }
  },
}))

jest.mock('components/icons/DropIcon', () => () => null)
jest.mock('components/base/forms/Button', () => () => null)

describe('JSONUpload', () => {
  const originalFileReader = global.FileReader

  beforeEach(() => {
    capturedOnDrop = undefined
    cachedCallback = undefined
    cachedDeps = undefined
  })

  afterEach(() => {
    global.FileReader = originalFileReader
  })

  const mockFileReaderWith = (result: string | ArrayBuffer | null) => {
    const listeners: Record<string, () => void> = {}
    global.FileReader = jest.fn(() => ({
      addEventListener: (event: string, cb: () => void) => {
        listeners[event] = cb
      },
      readAsText: () => {
        listeners.load?.()
      },
      result,
    })) as unknown as typeof FileReader
  }

  const getCapturedOnDrop = (): DropHandler => {
    if (!capturedOnDrop) {
      throw new Error('Expected useDropzone to receive an onDrop handler')
    }
    return capturedOnDrop
  }

  it('invokes the latest onChange callback after rerender instead of a stale closure', () => {
    const firstOnChange = jest.fn()
    const secondOnChange = jest.fn()
    const file = { name: 'flags.json' } as File

    JSONUpload({ onChange: firstOnChange, value: null })
    JSONUpload({ onChange: secondOnChange, value: null })

    mockFileReaderWith('{"flags":[1,2]}')
    getCapturedOnDrop()([file])

    expect(firstOnChange).not.toHaveBeenCalled()
    expect(secondOnChange).toHaveBeenCalledTimes(1)
    expect(secondOnChange).toHaveBeenCalledWith(file, { flags: [1, 2] })
  })

  it('does not invoke onChange when the dropped file contains invalid JSON', () => {
    const onChange = jest.fn()
    const file = { name: 'broken.json' } as File

    JSONUpload({ onChange, value: null })

    mockFileReaderWith('{not-valid-json')
    getCapturedOnDrop()([file])

    expect(onChange).not.toHaveBeenCalled()
  })
})
