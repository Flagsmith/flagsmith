/**
 * @jest-environment jsdom
 */
import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SegmentedControl from './..'

const OPTIONS = [
  { label: 'Everything', value: 'all' },
  { label: 'Organisation', value: 'organisation' },
  { label: 'Project', value: 'project' },
]

const Scope = ({ onChange }: { onChange?: (value: string) => void }) => {
  const [value, setValue] = useState('all')
  return (
    <SegmentedControl
      aria-label='Scope'
      options={OPTIONS}
      value={value}
      onChange={(next) => {
        setValue(next)
        onChange?.(next)
      }}
    />
  )
}

describe('SegmentedControl', () => {
  it('is a radio group with the value checked', () => {
    render(<Scope />)
    expect(
      screen.getByRole('radiogroup', { name: 'Scope' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Everything' })).toBeChecked()
  })

  it('selects an option on click', async () => {
    const user = userEvent.setup()
    const onChange = jest.fn()
    render(<Scope onChange={onChange} />)

    await user.click(screen.getByRole('radio', { name: 'Organisation' }))

    expect(onChange).toHaveBeenCalledWith('organisation')
    expect(screen.getByRole('radio', { name: 'Organisation' })).toBeChecked()
  })

  it('tabs to the checked option only, and arrows move the selection', async () => {
    const user = userEvent.setup()
    render(<Scope />)

    await user.tab()
    expect(screen.getByRole('radio', { name: 'Everything' })).toHaveFocus()

    await user.keyboard('{ArrowLeft}')
    const project = screen.getByRole('radio', { name: 'Project' })
    expect(project).toHaveFocus()
    expect(project).toBeChecked()
  })
})
