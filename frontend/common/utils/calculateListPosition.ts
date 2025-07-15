// This function is used to calculate the position of a dropdown menu relative to his trigger button element
export function calculateListPosition(
  btnEl: HTMLElement,
  listEl: HTMLElement,
  forceInView = false,
): { top: number; left: number } {
  const listPosition = listEl.getBoundingClientRect()
  const btnPosition = btnEl.getBoundingClientRect()
  const pageTop = window.visualViewport?.pageTop ?? 0
  const isOverflowing =
    listPosition.height + btnPosition.top > window.innerHeight

  const defaultTop = pageTop + btnPosition.bottom
  const defaultLeft = btnPosition.right - listPosition.width

  const bottomOverflowOffset = listPosition.height + btnPosition.height + 5

  return {
    left: defaultLeft,
    top: defaultTop - (forceInView && isOverflowing ? bottomOverflowOffset : 0),
  }
}
