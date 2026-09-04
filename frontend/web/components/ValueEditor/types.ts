// 'ini' is the highlight.js grammar name; the label we show for it is '.toml'.
export type ValueEditorLanguage = 'txt' | 'json' | 'xml' | 'ini' | 'yaml'

/** Display order of the format labels above the editor. */
export const LANGUAGES: ValueEditorLanguage[] = [
  'txt',
  'json',
  'xml',
  'ini',
  'yaml',
]

export const LANGUAGE_LABELS: Record<ValueEditorLanguage, string> = {
  ini: '.toml',
  json: '.json',
  txt: '.txt',
  xml: '.xml',
  yaml: '.yaml',
}
