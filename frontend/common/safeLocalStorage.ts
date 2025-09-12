export function storageGet(key: string): string | null {
  try {
    return localStorage?.getItem(key) ?? null
  } catch (err) {
    //Storage / privacy errors
    console.error(err)
    return null
  }
}

export function storageSet(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch (err) {
    //Storage / privacy errors
    console.error(err)
  }
}
