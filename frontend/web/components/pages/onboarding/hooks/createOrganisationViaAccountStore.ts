import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'

/**
 * Create an organisation through the legacy account store rather than the RTK
 * mutation. Much of the shell still reads the current organisation from
 * `AccountStore`, and only this path populates it (adds to
 * `AccountStore.model.organisations` and sets the selection). A pure-RTK create
 * leaves `AccountStore.getOrganisation()` empty, which breaks org-scoped calls
 * on the destination page. Resolves with the new organisation id. Mirrors the
 * save/select handling in CreateOrganisationPage.
 *
 * Shared by the stepped flow and the single-page flow.
 */
export const createOrganisationViaAccountStore = (
  name: string,
): Promise<number> =>
  new Promise((resolve, reject) => {
    const cleanup = () => {
      AccountStore.off('saved', onSaved)
      AccountStore.off('problem', onProblem)
      clearTimeout(timer)
    }
    const onSaved = () => {
      cleanup()
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore - savedId is set by the createOrganisation controller
      resolve(AccountStore.savedId as number)
    }
    const onProblem = () => {
      cleanup()
      reject(AccountStore.error || new Error('Failed to create organisation'))
    }
    const timer = setTimeout(() => {
      cleanup()
      reject(new Error('Timed out creating organisation'))
    }, 20000)
    AccountStore.on('saved', onSaved)
    AccountStore.on('problem', onProblem)
    AppActions.createOrganisation(name)
  })
