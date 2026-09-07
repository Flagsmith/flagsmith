import { copyToClipboard } from 'common/utils/copyToClipboard'

const writeText = jest.fn()
const toast = jest.fn()
const execCommand = jest.fn()

// Insecure contexts have no navigator.clipboard, so the helper falls back to a
// detached textarea and execCommand.
const withoutClipboard = () => {
  Object.defineProperty(global, 'navigator', {
    configurable: true,
    value: {},
    writable: true,
  })
  const textarea = {
    select: jest.fn(),
    setAttribute: jest.fn(),
    style: {},
    value: '',
  }
  ;(global as any).document = {
    body: { appendChild: jest.fn(), removeChild: jest.fn() },
    createElement: jest.fn(() => textarea),
    execCommand,
  }
  return textarea
}

beforeEach(() => {
  writeText.mockReset().mockResolvedValue(undefined)
  toast.mockReset()
  execCommand.mockReset().mockReturnValue(true)
  ;(global as any).toast = toast
  Object.defineProperty(global, 'navigator', {
    configurable: true,
    value: { clipboard: { writeText } },
    writable: true,
  })
})

describe('copyToClipboard', () => {
  it('writes the value and toasts the default success message', async () => {
    await copyToClipboard('DEFAULT_VALUE')

    expect(writeText).toHaveBeenCalledWith('DEFAULT_VALUE')
    expect(toast).toHaveBeenCalledWith('Copied to clipboard')
  })

  it('toasts a caller-supplied success message instead', async () => {
    await copyToClipboard('prompt', 'Cleanup prompt copied to clipboard')

    expect(toast).toHaveBeenCalledWith('Cleanup prompt copied to clipboard')
  })

  it('toasts the failure and rethrows when the write is rejected', async () => {
    const error = new Error('denied')
    writeText.mockRejectedValue(error)

    await expect(copyToClipboard('value')).rejects.toThrow(error)
    expect(toast).toHaveBeenCalledWith('Failed to copy to clipboard')
  })

  it('toasts a caller-supplied failure message instead', async () => {
    writeText.mockRejectedValue(new Error('denied'))

    await expect(
      copyToClipboard('value', undefined, 'Could not copy the value'),
    ).rejects.toThrow()
    expect(toast).toHaveBeenCalledWith('Could not copy the value')
  })

  describe('without navigator.clipboard', () => {
    it('copies through execCommand and toasts success', async () => {
      const textarea = withoutClipboard()

      await copyToClipboard('DEFAULT_VALUE')

      expect(textarea.value).toBe('DEFAULT_VALUE')
      expect(execCommand).toHaveBeenCalledWith('copy')
      expect(toast).toHaveBeenCalledWith('Copied to clipboard')
    })

    it('removes the textarea it appended', async () => {
      withoutClipboard()

      await copyToClipboard('value')

      expect(document.body.removeChild).toHaveBeenCalled()
    })

    it('toasts the failure and rethrows when execCommand refuses', async () => {
      withoutClipboard()
      execCommand.mockReturnValue(false)

      await expect(copyToClipboard('value')).rejects.toThrow(
        'Clipboard copy was rejected',
      )
      expect(toast).toHaveBeenCalledWith('Failed to copy to clipboard')
    })
  })
})
