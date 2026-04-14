import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import API from 'project/api'

type SelectedOrganisationState = {
  id: number | undefined
}

const initialState: SelectedOrganisationState = {
  id: undefined,
}

const selectedOrganisationSlice = createSlice({
  initialState,
  name: 'selectedOrganisation',
  reducers: {
    setSelectedOrganisationId(state, action: PayloadAction<number>) {
      state.id = action.payload
      API.setCookie('organisation', `${action.payload}`)
    },
  },
})

export const { setSelectedOrganisationId } = selectedOrganisationSlice.actions
export default selectedOrganisationSlice.reducer
