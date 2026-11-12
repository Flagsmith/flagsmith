import { ComponentType } from 'react'
import {
  DotnetLogo,
  FlutterLogo,
  GoLogo,
  IosLogo,
  JavaLogo,
  JavascriptLogo,
  NextjsLogo,
  NodejsLogo,
  PhpLogo,
  PythonLogo,
  ReactLogo,
  RubyLogo,
  RustLogo,
} from './logos'

export type SdkLang = {
  label: string
  // Key into codeHelp's INSTALL and INIT maps. Differs from the display label,
  // e.g. 'Node JS' (not 'Node.js') and 'Next.js' (not 'Next.js (app router)').
  codeHelpKey: string
  // codeHelp keys INIT per router for Next.js ('Next.js (app router)' / '(pages
  // router)') but INSTALL by plain 'Next.js'. Set this where the INIT key differs
  // from codeHelpKey, so the wire snippet still resolves; defaults to codeHelpKey.
  initKey?: string
  // highlight.js language for the wire snippet (install is always shell).
  language: string
  // Brand logo component for the chip. Imported by name so unreferenced logos
  // shake out of the bundle.
  logo: ComponentType
  // Popular SDKs show as quick-pick chips; the rest live behind "More".
  popular: boolean
}

// Order matters: popular ones first (chips), then the long tail (More menu).
// React Native reuses the React logo; both Next.js routers share the Next mark.
export const SDK_LANGS: SdkLang[] = [
  {
    codeHelpKey: 'React',
    label: 'React',
    language: 'javascript',
    logo: ReactLogo,
    popular: true,
  },
  {
    codeHelpKey: 'JavaScript',
    label: 'JavaScript',
    language: 'javascript',
    logo: JavascriptLogo,
    popular: true,
  },
  {
    codeHelpKey: 'Python',
    label: 'Python',
    language: 'python',
    logo: PythonLogo,
    popular: true,
  },
  {
    codeHelpKey: 'Node JS',
    label: 'Node.js',
    language: 'javascript',
    logo: NodejsLogo,
    popular: true,
  },
  {
    codeHelpKey: 'Go',
    label: 'Go',
    language: 'go',
    logo: GoLogo,
    popular: true,
  },
  {
    codeHelpKey: 'Ruby',
    label: 'Ruby',
    language: 'ruby',
    logo: RubyLogo,
    popular: true,
  },
  {
    codeHelpKey: '.NET',
    label: '.NET',
    language: 'csharp',
    logo: DotnetLogo,
    popular: false,
  },
  {
    codeHelpKey: 'Flutter',
    label: 'Flutter',
    language: 'dart',
    logo: FlutterLogo,
    popular: false,
  },
  {
    codeHelpKey: 'Next.js',
    initKey: 'Next.js (app router)',
    label: 'Next.js (app router)',
    language: 'javascript',
    logo: NextjsLogo,
    popular: false,
  },
  {
    codeHelpKey: 'Next.js',
    initKey: 'Next.js (pages router)',
    label: 'Next.js (pages router)',
    language: 'javascript',
    logo: NextjsLogo,
    popular: false,
  },
  {
    codeHelpKey: 'Java',
    label: 'Java',
    language: 'java',
    logo: JavaLogo,
    popular: false,
  },
  {
    codeHelpKey: 'PHP',
    label: 'PHP',
    language: 'php',
    logo: PhpLogo,
    popular: false,
  },
  {
    codeHelpKey: 'React Native',
    label: 'React Native',
    language: 'javascript',
    logo: ReactLogo,
    popular: false,
  },
  {
    codeHelpKey: 'Rust',
    label: 'Rust',
    language: 'rust',
    logo: RustLogo,
    popular: false,
  },
  {
    codeHelpKey: 'iOS',
    label: 'iOS',
    language: 'swift',
    logo: IosLogo,
    popular: false,
  },
]
