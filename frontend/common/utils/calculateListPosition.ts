// This function is used to calculate the position of a dropdown menu relative to his trigger button element
export function calculateListPosition(
  btnEl: HTMLElement,
  listEl: HTMLElement,
): { top: number; left: number } {
  const listPosition = listEl.getBoundingClientRect()
  const btnPosition = btnEl.getBoundingClientRect()
  const pageTop = window.visualViewport?.pageTop ?? 0
  return {
    left: btnPosition.right - listPosition.width,
    top: pageTop + btnPosition.bottom,
  }
}
