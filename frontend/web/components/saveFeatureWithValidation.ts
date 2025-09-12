export const saveFeatureWithValidation = (cb: (schedule?: boolean) => void) => {
  return (schedule: boolean) => {
    if (document.getElementById('language-validation-error')) {
      openConfirm({
        body: 'Your remote config value does not pass validation for the language you have selected. Are you sure you wish to save?',
        noText: 'Cancel',
        onYes: () => cb(),
        title: 'Validation error',
        yesText: 'Save',
      })
    } else {
      if (schedule) {
        cb(schedule)
      } else {
        cb()
      }
    }
  }
}
