import React, { FC } from 'react'
import Input, { InputProps } from './Input'

// `type` and `search` are fixed by this component.
type SearchInputProps = Omit<InputProps, 'type' | 'search'>

// Text input with a search (magnifying-glass) icon.
//
// Phase 1: composes Input, which still owns the icon. This establishes the
// component consumers migrate to; the adornment moves here when Input is
// slimmed to a plain input (the wrapper-less redesign).
const SearchInput: FC<SearchInputProps> = (props) => (
  <Input {...props} type='text' search />
)

export default SearchInput
