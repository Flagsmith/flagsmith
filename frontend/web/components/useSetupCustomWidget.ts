import {
  DDClient,
  EventType,
  WidgetSettingsMenuClickData,
} from '@datadog/ui-extensions-sdk'
import * as React from 'react'
import API from 'project/api'

/**
 * This hook performs any app-wide for the custom widget.
 * @param client The initialized {@link DDClient}
 */
function useSetupCustomWidget(client: DDClient): void {
  /**
   * We set up an event listener for the logout widget settings menu item.
   * This event handler lets us perform the actual logging out of a user.
   */
  React.useEffect(() => {
    const unsubscribeLogout = client.events.on(
      EventType.WIDGET_SETTINGS_MENU_CLICK,
      async (data: WidgetSettingsMenuClickData): Promise<void> => {
        /**
         * We only want to handle events from the `'logout'` settings menu item.
         */
        if (data.menuItem.key !== 'logout') {
          return
        }

        /**
         * Perform the actual logout,
         * then make sure to update the auth state so it's reflected in Datadog.
         */
        API.setCookie('t', '')
        await client.auth.updateAuthState()
      },
    )

    /**
     * We make sure to unsubscribe the event listener we set up.
     */
    return () => {
      unsubscribeLogout()
    }
  }, [client.auth, client.events])
}

export { useSetupCustomWidget }
