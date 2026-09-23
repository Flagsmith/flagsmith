import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import SdkPicker from 'components/pages/onboarding/OnboardingConnectPanel/SdkPicker'
import {
  SDK_LANGS,
  SdkLang,
} from 'components/pages/onboarding/OnboardingConnectPanel/sdkLangs'

const meta: Meta<typeof SdkPicker> = {
  component: SdkPicker,
  parameters: {
    docs: {
      description: {
        component:
          'The SDK / framework picker: popular SDKs as quick-pick Chips, the long tail behind "More". Controlled - the selected SDK lives in the parent.',
      },
    },
    layout: 'padded',
  },
  title: 'Pages/Onboarding/SdkPicker',
}
export default meta

type Story = StoryObj<typeof SdkPicker>

const Controlled = () => {
  const [selected, setSelected] = useState<SdkLang>(SDK_LANGS[0])
  return <SdkPicker selected={selected} onSelect={setSelected} />
}

export const Default: Story = {
  render: () => <Controlled />,
}
