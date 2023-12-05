let initialised = false

if (Project.fpr) {
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
  if (typeof fpr !== 'undefined') {
    var chargebeeTrackFunc = function (fprom) {
      let tid = fprom.tid
      let chargebeeInstance
      try {
        chargebeeInstance = Chargebee.getInstance()
      } catch (err) {}
      if (tid && chargebeeInstance) {
        let cart = chargebeeInstance.getCart()
        cart.setCustomer({ cf_tid: tid })
      } else if (tid) {
        document.addEventListener('DOMContentLoaded', function () {
          chargebeeTrackFunc(fprom)
        })
      }
    }
    fpr('onReady', chargebeeTrackFunc)
  }
}
