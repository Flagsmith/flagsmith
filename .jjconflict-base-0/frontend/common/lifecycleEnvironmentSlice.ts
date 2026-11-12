import { createSlice, PayloadAction } from '@reduxjs/toolkit'

type LifecycleEnvironmentState = {
  // Maps a project id to the environment id selected for lifecycle analysis.
  byProject: Record<number, number>
}

const initialState: LifecycleEnvironmentState = {
  byProject: {},
}

const lifecycleEnvironmentSlice = createSlice({
  initialState,
  name: 'lifecycleEnvironment',
  reducers: {
    setLifecycleEnvironment(
      state,
      action: PayloadAction<{ projectId: number; environmentId: number }>,
    ) {
      state.byProject[action.payload.projectId] = action.payload.environmentId
    },
  },
})

export const { setLifecycleEnvironment } = lifecycleEnvironmentSlice.actions
export default lifecycleEnvironmentSlice.reducer
