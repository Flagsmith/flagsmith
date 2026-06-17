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
  // Display label and the key into codeHelp.INIT.
  label: string
  // Key into codeHelp.INSTALL (occasionally differs, e.g. Next.js).
  installKey: string
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
    installKey: 'React',
    label: 'React',
    language: 'javascript',
    logo: ReactLogo,
    popular: true,
  },
  {
    installKey: 'JavaScript',
    label: 'JavaScript',
    language: 'javascript',
    logo: JavascriptLogo,
    popular: true,
  },
  {
    installKey: 'Python',
    label: 'Python',
    language: 'python',
    logo: PythonLogo,
    popular: true,
  },
  {
    installKey: 'Node JS',
    label: 'Node.js',
    language: 'javascript',
    logo: NodejsLogo,
    popular: true,
  },
  {
    installKey: 'Go',
    label: 'Go',
    language: 'go',
    logo: GoLogo,
    popular: true,
  },
  {
    installKey: 'Ruby',
    label: 'Ruby',
    language: 'ruby',
    logo: RubyLogo,
    popular: true,
  },
  {
    installKey: '.NET',
    label: '.NET',
    language: 'csharp',
    logo: DotnetLogo,
    popular: false,
  },
  {
    installKey: 'Flutter',
    label: 'Flutter',
    language: 'dart',
    logo: FlutterLogo,
    popular: false,
  },
  {
    installKey: 'Next.js',
    label: 'Next.js (app router)',
    language: 'javascript',
    logo: NextjsLogo,
    popular: false,
  },
  {
    installKey: 'Next.js',
    label: 'Next.js (pages router)',
    language: 'javascript',
    logo: NextjsLogo,
    popular: false,
  },
  {
    installKey: 'Java',
    label: 'Java',
    language: 'java',
    logo: JavaLogo,
    popular: false,
  },
  {
    installKey: 'PHP',
    label: 'PHP',
    language: 'php',
    logo: PhpLogo,
    popular: false,
  },
  {
    installKey: 'React Native',
    label: 'React Native',
    language: 'javascript',
    logo: ReactLogo,
    popular: false,
  },
  {
    installKey: 'Rust',
    label: 'Rust',
    language: 'rust',
    logo: RustLogo,
    popular: false,
  },
  {
    installKey: 'iOS',
    label: 'iOS',
    language: 'swift',
    logo: IosLogo,
    popular: false,
  },
]
