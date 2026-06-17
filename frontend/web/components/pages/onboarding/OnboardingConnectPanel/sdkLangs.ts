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
  hljs: string
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
    hljs: 'javascript',
    installKey: 'React',
    label: 'React',
    logo: ReactLogo,
    popular: true,
  },
  {
    hljs: 'javascript',
    installKey: 'JavaScript',
    label: 'JavaScript',
    logo: JavascriptLogo,
    popular: true,
  },
  {
    hljs: 'python',
    installKey: 'Python',
    label: 'Python',
    logo: PythonLogo,
    popular: true,
  },
  {
    hljs: 'javascript',
    installKey: 'Node JS',
    label: 'Node.js',
    logo: NodejsLogo,
    popular: true,
  },
  { hljs: 'go', installKey: 'Go', label: 'Go', logo: GoLogo, popular: true },
  {
    hljs: 'ruby',
    installKey: 'Ruby',
    label: 'Ruby',
    logo: RubyLogo,
    popular: true,
  },
  {
    hljs: 'csharp',
    installKey: '.NET',
    label: '.NET',
    logo: DotnetLogo,
    popular: false,
  },
  {
    hljs: 'dart',
    installKey: 'Flutter',
    label: 'Flutter',
    logo: FlutterLogo,
    popular: false,
  },
  {
    hljs: 'javascript',
    installKey: 'Next.js',
    label: 'Next.js (app router)',
    logo: NextjsLogo,
    popular: false,
  },
  {
    hljs: 'javascript',
    installKey: 'Next.js',
    label: 'Next.js (pages router)',
    logo: NextjsLogo,
    popular: false,
  },
  {
    hljs: 'java',
    installKey: 'Java',
    label: 'Java',
    logo: JavaLogo,
    popular: false,
  },
  {
    hljs: 'php',
    installKey: 'PHP',
    label: 'PHP',
    logo: PhpLogo,
    popular: false,
  },
  {
    hljs: 'javascript',
    installKey: 'React Native',
    label: 'React Native',
    logo: ReactLogo,
    popular: false,
  },
  {
    hljs: 'rust',
    installKey: 'Rust',
    label: 'Rust',
    logo: RustLogo,
    popular: false,
  },
  {
    hljs: 'swift',
    installKey: 'iOS',
    label: 'iOS',
    logo: IosLogo,
    popular: false,
  },
]
