import flagsmith from '@flagsmith/flagsmith';
import * as Sentry from '@sentry/browser';
import { isMobile } from 'react-device-detect';
import propTypes from 'prop-types';
import Project from 'common/project';
import moment from 'moment/min/moment.min';
import React from 'react';
import ReactDOM from 'react-dom';
import { Link, NavLink } from 'react-router-dom';

window.isMobile = isMobile || $(window).width() <= 576;

window.flagsmith = flagsmith;
window.moment = moment;


window.React = React;
window.ReactDOM = ReactDOM;

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

window.Link = Link;
window.NavLink = NavLink;

// Analytics — not loaded in E2E runs, where widgets can overlay the UI
const disableThirdPartyScripts = !!window.E2E

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
if(Project.hubspot && !disableThirdPartyScripts) {
    // Must be set before the script loads. The chat widget is loaded by
    // common/loadChat behind the hubspot_chat flag, not by chatflow targeting.
    window.hsConversationsSettings = { loadImmediately: false };
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.id = "hs-script-loader";
    script.async = true;
    script.defer = true;
    script.src = Project.hubspot;

    document.head.appendChild(script);
}
