import React from 'react'
import classNames from 'classnames'
import ReactMarkdown from 'react-markdown'
import className = ReactMarkdown.propTypes.className

interface RadioProps {
  label: string
  onChange: (value: boolean) => void
  checked: boolean
}

const Radio: React.FC<RadioProps> = ({ checked, label, onChange }) => {
  const handleChange = () => {
    onChange(!checked)
  }

  return (
    <label
      onClick={handleChange}
      className='relative cursor-pointer flex-row align-items-center'
    >
      {checked && <CheckedSVG />} {!checked && <UncheckedSVG />}
      {<span className={classNames('ml-2', className)}>{label}</span>}
    </label>
  )
}

// SVG components (you can replace these with your own SVG components)
const CheckedSVG: React.FC = () => (
  <svg
    className='no-pointer'
    width='20'
    height='20'
    viewBox='0 0 20 20'
    fill='none'
    xmlns='http://www.w3.org/2000/svg'
  >
    <path
      fillRule='evenodd'
      clipRule='evenodd'
      d='M10 18.8889C14.9092 18.8889 18.8889 14.9092 18.8889 10C18.8889 5.0908 14.9092 1.11111 10 1.11111C5.0908 1.11111 1.11111 5.0908 1.11111 10C1.11111 14.9092 5.0908 18.8889 10 18.8889ZM10 20C4.47715 20 0 15.5228 0 10C0 4.47715 4.47715 0 10 0C15.5228 0 20 4.47715 20 10C20 15.5228 15.5228 20 10 20ZM10 16C13.3137 16 16 13.3137 16 10C16 6.68629 13.3137 4 10 4C6.68629 4 4 6.68629 4 10C4 13.3137 6.68629 16 10 16Z'
      fill='#6837FC'
    />
  </svg>
)

const UncheckedSVG: React.FC = () => (
  <svg
    className='no-pointer'
    width='20'
    height='20'
    viewBox='0 0 20 20'
    fill='none'
    xmlns='http://www.w3.org/2000/svg'
  >
    <circle cx='10' cy='10' r='9.5' stroke='#6837FC' />
  </svg>
)

export default Radio
