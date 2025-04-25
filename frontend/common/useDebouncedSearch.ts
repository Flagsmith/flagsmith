import { useState } from 'react'
import useDebounce from './useDebounce'

export default function useDebouncedSearch(initialValue = '') {
  const [searchInput, setSearchInput] = useState(initialValue)
  const [search, setSearch] = useState(initialValue)

  const debouncedSearch = useDebounce((value: string) => {
    setSearch(value)
  }, 500)

  const handleSearchInput = (value: string) => {
    setSearchInput(value)
    debouncedSearch(value)
  }

  return {
    search,
    searchInput,
    setSearchInput: handleSearchInput
  }
}
/* Usage example:
const searchItems = useDebounce((search:string) => {
  doThing()
}, 500)
*/
