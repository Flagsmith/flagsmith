/**
 * @jest-environment jsdom
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Popover from './..'

const renderPopover = () =>
  render(
    <>
      <Popover
        aria-label='Sort'
        renderTrigger={(props) => <button {...props}>Sort by</button>}
      >
        {(close) => (
          <button type='button' onClick={close}>
            Name
          </button>
        )}
      </Popover>
      <p>Outside</p>
    </>,
  )

const openPopover = async (user: ReturnType<typeof userEvent.setup>) => {
  await user.click(screen.getByRole('button', { name: 'Sort by' }))
  expect(screen.getByRole('dialog', { name: 'Sort' })).toBeInTheDocument()
}

describe('Popover', () => {
  it('opens from the trigger and moves focus inside', async () => {
    const user = userEvent.setup()
    renderPopover()

    await openPopover(user)
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Name' })).toHaveFocus(),
    )
  })

  it('closes on Escape and returns focus to the trigger', async () => {
    const user = userEvent.setup()
    renderPopover()
    const trigger = screen.getByRole('button', { name: 'Sort by' })

    await openPopover(user)
    await user.keyboard('{Escape}')

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('closes on a click outside', async () => {
    const user = userEvent.setup()
    renderPopover()

    await openPopover(user)
    await user.click(screen.getByText('Outside'))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('lets its content close it', async () => {
    const user = userEvent.setup()
    renderPopover()

    await openPopover(user)
    await user.click(screen.getByRole('button', { name: 'Name' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
