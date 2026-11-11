/**
 * @jest-environment jsdom
 */
import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Chip from './..'

describe('Chip', () => {
  it('is not a control when it has no handlers', () => {
    render(<Chip>Production</Chip>)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
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

  describe('toggle mode', () => {
    const Toggle = () => {
      const [checked, setChecked] = useState(false)
      return (
        <Chip checked={checked} onChange={setChecked}>
          Production
        </Chip>
      )
    }

    it('is a checkbox named by its label', () => {
      render(<Toggle />)
      expect(
        screen.getByRole('checkbox', { name: 'Production' }),
      ).not.toBeChecked()
    })

    it('toggles from a click and from Space', async () => {
      const user = userEvent.setup()
      render(<Toggle />)
      const checkbox = screen.getByRole('checkbox', { name: 'Production' })

      await user.click(checkbox)
      expect(checkbox).toBeChecked()

      await user.keyboard(' ')
      expect(checkbox).not.toBeChecked()
    })

    it('can be reached with Tab', async () => {
      const user = userEvent.setup()
      render(<Toggle />)

      await user.tab()

      expect(screen.getByRole('checkbox', { name: 'Production' })).toHaveFocus()
    })
  })
})
