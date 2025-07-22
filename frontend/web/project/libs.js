import flagsmith from 'flagsmith';
import * as Sentry from '@sentry/browser';
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
// Add this line if you're using flagsmith via npm
const _Project = require('../../common/project');

window.isMobile = isMobile || $(window).width() <= 576;

window.flagsmith = flagsmith;
window.moment = require('moment/min/moment.min');

window._ = { each, intersection, sortBy, orderBy, filter, find, partial, findIndex, range, map, cloneDeep, keyBy, throttle, every, get };

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

if (typeof SENTRY_RELEASE_VERSION !== 'undefined' && Project.sentry && typeof Sentry !== 'undefined') {
    Sentry.init({
        dsn: Project.sentry,
        environment: Project.env,
        release: SENTRY_RELEASE_VERSION,
    });
}

if (Project.delighted) {
    !(function (e, t, r, n) { if (!e[n]) { for (var a = e[n] = [], i = ['survey', 'reset', 'config', 'init', 'set', 'get', 'event', 'identify', 'track', 'page', 'screen', 'group', 'alias'], s = 0; s < i.length; s++) { const c = i[s]; a[c] = a[c] || (function (e) { return function () { const t = Array.prototype.slice.call(arguments); a.push([e, t]); }; }(c)); }a.SNIPPET_VERSION = '1.0.1'; const o = t.createElement('script'); o.type = 'text/javascript', o.async = !0, o.src = `https://d2yyd1h5u9mauk.cloudfront.net/integrations/web/v1/library/${r}/${n}.js`; const p = t.getElementsByTagName('script')[0]; p.parentNode.insertBefore(o, p); } }(window, document, Project.delighted, 'delighted'));
}
if(Project.linkedinPartnerTracking) {
    const _linkedin_partner_id = "5747572";
    window._linkedin_data_partner_ids = window._linkedin_data_partner_ids || [];
    window._linkedin_data_partner_ids.push(_linkedin_partner_id);
        (function(l) {
        if (!l){window.lintrk = function(a,b){window.lintrk.q.push([a,b])};
        window.lintrk.q=[]}
        var s = document.getElementsByTagName("script")[0];
        var b = document.createElement("script");
        b.type = "text/javascript";b.async = true;
        b.src = "https://snap.licdn.com/li.lms-analytics/insight.min.js";
        s.parentNode.insertBefore(b, s);})(window.lintrk);
    var img = document.createElement("img");
    img.setAttribute("height", "1");
    img.setAttribute("width", "1");
    img.setAttribute("style", "display:none;");
    img.setAttribute("alt", "");
    img.setAttribute("src", "https://px.ads.linkedin.com/collect/?pid=5747572&fmt=gif");
    document.body.appendChild(img);
}

if(Project.hubspot) {
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.id = "hs-script-loader";
    script.async = true;
    script.defer = true;
    script.src = Project.hubspot;

    document.head.appendChild(script);
}
