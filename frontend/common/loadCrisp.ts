export default async function (crispWebsiteId: string) {
  // @ts-ignore
  if (window.$crisp) {
    return
  }
  // @ts-ignore
  window.$crisp = []
  // @ts-ignore
  window.CRISP_WEBSITE_ID = crispWebsiteId
  await new Promise((resolve, reject) => {
    const d = document
    const s = d.createElement('script')
    s.src = 'https://client.crisp.chat/l.js'
    s.async = true
    s.onload = resolve
    s.onerror = reject
    d.getElementsByTagName('head')[0].appendChild(s)
  })
}
