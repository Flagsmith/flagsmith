let initialised = false

if (Project.fpr) {
  // Load first promoter
  ;(function (w) {
    w.fpr =
      w.fpr ||
      function () {
        w.fpr.q = w.fpr.q || []
        w.fpr.q[arguments[0] == 'set' ? 'unshift' : 'push'](arguments)
      }
  })(window)
  fpr('init', { cid: Project.fpr })
}

export default function () {
  if (initialised) {
    return
  }
  initialised = true
  // Pass First Promoter tid to chargebee as a custom field
  if (typeof fpr !== 'undefined' && fprom.data) {
    const tid = fprom.data.tid
    let chargebeeInstance
    try {
      chargebeeInstance = Chargebee.getInstance()
    } catch (err) {}
    if (tid && chargebeeInstance) {
      let cart = chargebeeInstance.getCart()
      cart.setCustomer({ cf_tid: tid })
    }
  }
}
