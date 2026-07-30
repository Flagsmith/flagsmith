import { createContext } from 'react'

export interface FieldContextValue {
  // The id declared via Field's htmlFor; house controls adopt it as their
  // default id so the caller declares the wiring once.
  controlId: string
  // `${controlId}-error`; controls reference it via aria-describedby while
  // the field has an error.
  errorId: string
  hasError: boolean
}

// Provided by Field only when an explicit htmlFor is passed, so wiring stays
// a visible, declared decision at the call site.
export default createContext<FieldContextValue | null>(null)
