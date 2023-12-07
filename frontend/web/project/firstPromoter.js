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
  const track = (fprom) => {
    // Pass First Promoter tid to chargebee as a custom field
    if (typeof fprom !== 'undefined') {
      const tid = fprom.tid
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
  if (typeof fpr !== 'undefined') {
    fpr('onReady', track)
    Utils.loadScriptPromise('https://cdn.firstpromoter.com/fpr.js')
  }
}
