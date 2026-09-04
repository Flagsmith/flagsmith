import toml from 'toml'
import yaml from 'yaml'

import { ValueEditorLanguage } from './types'

const errorMessage = (e: unknown) =>
  e instanceof Error ? e.message : String(e)

function xmlError(xmlStr: string): string | false {
  const dom = new DOMParser().parseFromString(xmlStr, 'application/xml')
  for (const element of Array.from(dom.querySelectorAll('parsererror'))) {
    // Chrome puts parsererror in the XHTML namespace, so it is an HTMLElement
    // with innerText. Firefox uses its own namespace and gives a plain Element
    // with neither, which is why this reads textContent off Element.
    const message = element.textContent?.trim()
    if (message) {
      return message
    }
  }
  return false
}

/** The parse error for `value` under `language`, or false when it is valid. */
export function validateValue(
  language: ValueEditorLanguage,
  value: string,
): string | false {
  try {
    switch (language) {
      case 'json':
        JSON.parse(value)
        return false
      case 'ini':
        toml.parse(value)
        return false
      case 'yaml':
        yaml.parse(value)
        return false
      case 'xml':
        return xmlError(value)
      default:
        return false
    }
  } catch (e) {
    return language === 'xml' ? 'Failed to parse XML' : errorMessage(e)
  }
}
