function async(u, c) {
    const d = document; const t = 'script';


    const o = d.createElement(t);


    const s = d.getElementsByTagName(t)[0];
    o.src = `${u}`;
    if (c) {
        o.addEventListener('load', (e) => {
            c(null, e);
        }, false);
    }
    s.parentNode.insertBefore(o, s);
}

export default function (clientId, cb) {
    const el = document.createElement('meta');
    el.name = 'google-signin-client_id';
    el.content = `${clientId}.apps.googleusercontent.com`;
    const instance = document.getElementsByTagName('meta')[0];
    instance.parentNode.insertBefore(el, instance);
    async('https://apis.google.com/js/platform.js', () => {
        setTimeout(() => {
            gapi.load('auth2', () => {
              cb();
            });
        }, 0);
    });
}
