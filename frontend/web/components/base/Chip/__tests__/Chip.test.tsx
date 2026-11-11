/**
 * @jest-environment jsdom
 */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Chip from './..'

describe('Chip', () => {
  it('is not a control when it has no handlers', () => {
    render(<Chip>Production</Chip>)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('calls onClick from a click, Enter or Space', async () => {
    const user = userEvent.setup()
    const onClick = jest.fn()
    render(<Chip onClick={onClick}>Production</Chip>)

    await user.click(screen.getByRole('button', { name: 'Production' }))
    await user.keyboard('{Enter}')
    await user.keyboard(' ')

    expect(onClick).toHaveBeenCalledTimes(3)
  })

  it('removes without also clicking the chip', async () => {
    const user = userEvent.setup()
    const onClick = jest.fn()
    const onRemove = jest.fn()
    render(
      <Chip onClick={onClick} onRemove={onRemove}>
        Production
      </Chip>,
    )

    await user.click(screen.getByRole('button', { name: 'Remove' }))

    expect(onRemove).toHaveBeenCalledTimes(1)
    expect(onClick).not.toHaveBeenCalled()
  })
})
