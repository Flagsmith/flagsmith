import React, { useState, useEffect } from 'react'
import { DocsContainer as BaseContainer } from '@storybook/addon-docs/blocks'
import { create } from 'storybook/theming'
import { addons } from 'storybook/preview-api'

const darkTheme = create({
  base: 'dark',
  appBg: '#15192b',
  appContentBg: '#161d30',
  barBg: '#15192b',
  colorPrimary: '#6837fc',
  colorSecondary: '#6837fc',
  textColor: '#e0e3e9',
  textMutedColor: '#9da4ae',
})

const lightTheme = create({
  base: 'light',
  colorPrimary: '#6837fc',
  colorSecondary: '#6837fc',
})

function getInitialTheme(context) {
  try {
    return context?.store?.globals?.globals?.theme === 'dark'
  } catch {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  }
}

export const DocsContainer = ({ children, context, ...props }) => {
  const [isDark, setIsDark] = useState(() => getInitialTheme(context))

  useEffect(() => {
    const channel = addons.getChannel()
    const handleGlobalsUpdate = ({ globals }) => {
      if (globals?.theme !== undefined) {
        setIsDark(globals.theme === 'dark')
      }
    }
    channel.on('globalsUpdated', handleGlobalsUpdate)
    return () => channel.off('globalsUpdated', handleGlobalsUpdate)
  }, [])

  return (
    <BaseContainer {...props} context={context} theme={isDark ? darkTheme : lightTheme}>
      {children}
    </BaseContainer>
  )
}
