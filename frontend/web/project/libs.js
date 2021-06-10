import flagsmith from 'flagsmith'; // Add this line if you're using flagsmith via npm
const _Project = require('../../common/project');

window.Project = {
    ..._Project,
    ...window.projectOverrides, // environment.js (also app.yaml if using app engine)
};
import 'ionicons/dist/css/ionicons.min.css';

// Optimise lodash
import each from 'lodash/each';
import map from 'lodash/map';
import filter from 'lodash/filter';
import find from 'lodash/find';
import orderBy from 'lodash/orderBy';
import intersection from 'lodash/intersection';
import partial from 'lodash/partial';
import cloneDeep from 'lodash/cloneDeep';
import findIndex from 'lodash/findIndex';
import sortBy from 'lodash/sortBy';
import range from 'lodash/range';
import keyBy from 'lodash/keyBy';
import throttle from 'lodash/throttle';
import every from 'lodash/every';
import get from 'lodash/get';
import { isMobile } from 'react-device-detect';
import propTypes from 'prop-types';
import Bootstrap from '../../node_modules/bootstrap/dist/js/bootstrap';


window.isMobile = isMobile || $(window).width() <= 576;

window.flagsmith = flagsmith;
window.moment = require('moment/min/moment.min');

window._ = { each,intersection, sortBy, orderBy, filter, find, partial, findIndex, range, map, cloneDeep, keyBy, throttle, every, get };

window.React = require('react');
window.ReactDOM = require('react-dom');

window.propTypes = propTypes;

window.Any = propTypes.any;
window.OptionalArray = propTypes.array;
window.OptionalBool = propTypes.bool;
window.OptionalFunc = propTypes.func;
window.OptionalNumber = propTypes.number;
window.OptionalObject = propTypes.object;
window.OptionalString = propTypes.string;
window.OptionalNode = propTypes.node;
window.OptionalElement = propTypes.element;
window.oneOf = propTypes.oneOf;
window.oneOfType = propTypes.oneOfType;
window.RequiredArray = propTypes.array.isRequired;
window.RequiredBool = propTypes.bool.isRequired;
window.RequiredFunc = propTypes.func.isRequired;
window.RequiredNumber = propTypes.number.isRequired;
window.RequiredObject = propTypes.object.isRequired;
window.RequiredString = propTypes.string.isRequired;
window.RequiredNode = propTypes.node.isRequired;
window.RequiredElement = propTypes.node.isRequired;

window.Link = require('react-router-dom').Link;
window.NavLink = require('react-router-dom').NavLink;

// Analytics
if (Project.ga) {
    (function (i, s, o, g, r, a, m) {
        i.GoogleAnalyticsObject = r; i[r] = i[r] || function () {
            (i[r].q = i[r].q || []).push(arguments);
        }, i[r].l = 1 * new Date(); a = s.createElement(o),
        m = s.getElementsByTagName(o)[0]; a.async = 1; a.src = g; m.parentNode.insertBefore(a, m);
    }(window, document, 'script', 'https://www.google-analytics.com/analytics.js', 'ga'));
    ga('create', Project.ga, 'auto');
}

if (Project.mixpanel) {
    (function (e, a) {
        if (!a.__SV) {
            let b = window; try {
                var c; let l; let i; const j = b.location; const
                    g = j.hash; c = function (a, b) { return (l = a.match(RegExp(`${b}=([^&]*)`))) ? l[1] : null; }; g && c(g, 'state') && (i = JSON.parse(decodeURIComponent(c(g, 'state'))), i.action === 'mpeditor' && (b.sessionStorage.setItem('_mpcehash', g), history.replaceState(i.desiredHash || '', e.title, j.pathname + j.search)));
            } catch (m) { } let k; let
                h; window.mixpanel = a; a._i = []; a.init = function (b, c, f) {
                function e(b, a) {
                    const c = a.split('.'); c.length == 2 && (b = b[c[0]], a = c[1]); b[a] = function () {
                        b.push([a].concat(Array.prototype.slice.call(arguments,
                            0)));
                    };
                } let d = a; typeof f !== 'undefined' ? d = a[f] = [] : f = 'mixpanel'; d.people = d.people || []; d.toString = function (b) { let a = 'mixpanel'; f !== 'mixpanel' && (a += `.${f}`); b || (a += ' (stub)'); return a; }; d.people.toString = function () { return `${d.toString(1)}.people (stub)`; }; k = 'disable time_event track track_pageview track_links track_forms register register_once alias unregister identify name_tag set_config reset opt_in_tracking opt_out_tracking has_opted_in_tracking has_opted_out_tracking clear_opt_in_out_tracking people.set people.set_once people.unset people.increment people.append people.union people.track_charge people.clear_charges people.delete_user'.split(' ');
                for (h = 0; h < k.length; h++)e(d, k[h]); a._i.push([b, c, f]);
            }; a.__SV = 1.2; b = e.createElement('script'); b.type = 'text/javascript'; b.async = !0; b.src = typeof MIXPANEL_CUSTOM_LIB_URL !== 'undefined' ? MIXPANEL_CUSTOM_LIB_URL : e.location.protocol === 'file:' && 'https://cdn4.mxpnl.com/libs/mixpanel-2-latest.min.js'.match(/^\/\//) ? 'https://cdn4.mxpnl.com/libs/mixpanel-2-latest.min.js' : 'https://cdn4.mxpnl.com/libs/mixpanel-2-latest.min.js'; c = e.getElementsByTagName('script')[0]; c.parentNode.insertBefore(b, c);
        }
    }(document, window.mixpanel || []));
    mixpanel.init(Project.mixpanel);
}

if (typeof SENTRY_RELEASE_VERSION !== 'undefined' && Project.sentry && typeof Sentry !== 'undefined') {
    Sentry.init({
        dsn: Project.sentry,
        environment: Project.env,
        release: SENTRY_RELEASE_VERSION,
    });
}

if (Project.delighted) {
    !(function (e, t, r, n) { if (!e[n]) { for (var a = e[n] = [], i = ['survey', 'reset', 'config', 'init', 'set', 'get', 'event', 'identify', 'track', 'page', 'screen', 'group', 'alias'], s = 0; s < i.length; s++) { const c = i[s]; a[c] = a[c] || (function (e) { return function () { const t = Array.prototype.slice.call(arguments); a.push([e, t]); }; }(c)); }a.SNIPPET_VERSION = '1.0.1'; const o = t.createElement('script'); o.type = 'text/javascript', o.async = !0, o.src = `https://d2yyd1h5u9mauk.cloudfront.net/integrations/web/v1/library/${r}/${n}.js`; const p = t.getElementsByTagName('script')[0]; p.parentNode.insertBefore(o, p); } }(window, document, 'Vq6wXzvfVxa8Xa3H', 'delighted'));
}
