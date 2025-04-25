import Project from 'common/project'

class TokenManager {
  private static refreshLock: Promise<void> | null = null
  /**
   * @param [client] - Fetch client to use for the refresh request
   * @returns Promise that resolves when the token is refreshed
   */
  public static async refreshJWTToken(client: Function = fetch): Promise<void> {
    if (this.refreshLock) {
      return this.refreshLock
    }

    this.refreshLock = (async () => {
      try {
        const response = await client(`${Project.api}auth/token/refresh/`, {
          credentials: 'include',
          method: 'POST',
        })

        if (!response.ok) {
          throw new Error('Failed to refresh token')
        }
      } catch (error) {
        console.error('Token refresh failed', error)
        throw error
      } finally {
        this.refreshLock = null
      }
    })()

    return this.refreshLock
  }
}

export default TokenManager
