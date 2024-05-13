export type AsyncStorageType = {
  getItemSync: (key: string) => string | null
  getItem: (
    key: string,
    cb?: (err: Error | null, res: string | null) => void,
  ) => Promise<string | null>
  setItem: (key: string, value: string) => Promise<string | null>
  removeItem: (key: string) => Promise<string | null>
  clear: () => Promise<string | null>
}
const AsyncStorage: AsyncStorageType = {
  clear: async function () {
    try {
      localStorage.clear()
      return null
    } catch (e) {
      return null
    }
  },
  getItem: function (key, cb) {
    return new Promise<any>((resolve, reject) => {
      try {
        const result = this.getItemSync!(key)
        cb?.(null, result)
        resolve(result)
      } catch (err) {
        cb && cb(err as Error, null)
        reject(err)
      }
    })
  },
  getItemSync: function (key) {
    try {
      const data = localStorage.getItem(key)
      return data || null
    } catch (e) {
      return null
    }
  },
  removeItem: async function (key) {
    try {
      localStorage.removeItem(key)
      return null
    } catch (e) {
      return null
    }
  },
  setItem: function (
    key: string,
    value: string,
    cb?: (err: Error | null, res: string | null) => void,
  ) {
    return new Promise<any>((resolve, reject) => {
      try {
        localStorage.setItem(key, value)
        cb && cb(null, value)
        resolve(value)
      } catch (err) {
        cb && cb(err as Error, null)
        reject(err)
      }
    })
  },
}

export default AsyncStorage
