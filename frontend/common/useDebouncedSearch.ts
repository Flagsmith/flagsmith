import { useState, useEffect } from 'react'
import useDebounce from './useDebounce'

export default function useDebouncedSearch(initialValue = '') {
  const [searchInput, setSearchInput] = useState(initialValue)
  const [search, setSearch] = useState(initialValue)
  const [debounceTime, setDebounceTime] = useState(750)

  useEffect(() => {
    setDebounceTime(searchInput.length < 1 ? 0 : 750)
  }, [searchInput])

  const debouncedSearch = useDebounce((value: string) => {
    setSearch(value)
  }, debounceTime)

  const handleSearchInput = (value: string) => {
    setSearchInput(value)
    debouncedSearch(value)
  }

  return {
    search,
    searchInput,
    setSearchInput: handleSearchInput,
  }
}

/* Usage example:
const searchItems = useDebounce((search:string) => {
  doThing()
}, 500)
*/
