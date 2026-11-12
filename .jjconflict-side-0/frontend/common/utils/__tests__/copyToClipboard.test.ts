import { copyToClipboard } from 'common/utils/copyToClipboard'

const writeText = jest.fn()
const toast = jest.fn()

beforeEach(() => {
  writeText.mockReset().mockResolvedValue(undefined)
  toast.mockReset()
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
})
