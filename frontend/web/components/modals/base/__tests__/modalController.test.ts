describe('modalController', () => {
  let ctrl: typeof import('../modalController')

  beforeEach(() => {
    jest.resetModules()
    ctrl = require('../modalController')
  })

  it('openModal adds a modal to the stack', () => {
    ctrl.openModal('Title', 'body')
    expect(ctrl.getModalState().modals).toHaveLength(1)
    expect(ctrl.getModalState().modals[0].title).toBe('Title')
  })

  it('openModal replaces the stack and fires the previous onClose', () => {
    const onClose = jest.fn()
    ctrl.openModal('A', 'a', undefined, onClose)
    ctrl.openModal('B', 'b')
    expect(onClose).toHaveBeenCalledTimes(1)
    expect(ctrl.getModalState().modals).toHaveLength(1)
    expect(ctrl.getModalState().modals[0].title).toBe('B')
  })

  it('openModal2 stacks on top of the current modal', () => {
    ctrl.openModal('A', 'a')
    ctrl.openModal2('B', 'b')
    expect(ctrl.getModalState().modals.map((m) => m.title)).toEqual(['A', 'B'])
  })

  it('closeModalByKey removes only the matching entry', () => {
    ctrl.openModal('A', 'a')
    ctrl.openModal2('B', 'b')
    const [first] = ctrl.getModalState().modals
    ctrl.closeModalByKey(first.key)
    expect(ctrl.getModalState().modals.map((m) => m.title)).toEqual(['B'])
  })

  it('openConfirm sets and clearConfirm clears the confirm slot', () => {
    ctrl.openConfirm({ body: 'b', onYes: jest.fn(), title: 'T' })
    expect(ctrl.getModalState().confirm).not.toBeNull()
    ctrl.clearConfirm()
    expect(ctrl.getModalState().confirm).toBeNull()
  })

  it('subscribeModals notifies on change and stops after unsubscribe', () => {
    const listener = jest.fn()
    const unsubscribe = ctrl.subscribeModals(listener)
    ctrl.openModal('A', 'a')
    expect(listener).toHaveBeenCalledTimes(1)
    unsubscribe()
    ctrl.openModal('B', 'b')
    expect(listener).toHaveBeenCalledTimes(1)
  })

  it('setModalTitle calls the registered setter until it is cleared', () => {
    const setter = jest.fn()
    ctrl.registerModalTitleSetter(setter)
    ctrl.setModalTitle('New title')
    expect(setter).toHaveBeenCalledWith('New title')
    ctrl.registerModalTitleSetter(null)
    ctrl.setModalTitle('Ignored')
    expect(setter).toHaveBeenCalledTimes(1)
  })

  it('setInterceptClose stores and clears the guard', () => {
    expect(ctrl.interceptClose).toBeNull()
    const guard = () => Promise.resolve(true)
    ctrl.setInterceptClose(guard)
    expect(ctrl.interceptClose).toBe(guard)
    ctrl.setInterceptClose(null)
    expect(ctrl.interceptClose).toBeNull()
  })
})
