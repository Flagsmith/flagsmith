import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

if (ExecutionEnvironment.canUseDOM) {
    !function() {
        var e, t, n;
        e = '33be044a44400f2', t = function() {
            Reo.init({ clientID: '33be044a44400f2' });
        }, (n = document.createElement('script')).src = 'https://static.reo.dev/' + e + '/reo.js', n.defer = !0, n.onload = t, document.head.appendChild(n);
    }();
}
