import Promise from 'promise-polyfill';
import 'whatwg-fetch';
import { AsyncStorage, AppState, NetInfo, Clipboard } from 'polyfill-react-native';
import Switch from '../components/Switch';

window.AppState = AppState;
window.NetInfo = NetInfo;
window.Clipboard = Clipboard;
window.AsyncStorage = AsyncStorage;
window.Switch = Switch;

// To add to window
if (!window.Promise) {
    window.Promise = Promise;
}

// Object Assign
if (typeof Object.assign !== 'function') {
    Object.assign = function (target, varArgs) {
        if (target == null) { // TypeError if undefined or null
            throw new TypeError('Cannot convert undefined or null to object');
        }

        const to = Object(target);

        for (let index = 1; index < arguments.length; index++) {
            const nextSource = arguments[index];

            if (nextSource != null) { // Skip over if undefined or null
                for (const nextKey in nextSource) {
                    // Avoid bugs when hasOwnProperty is shadowed
                    if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
                        to[nextKey] = nextSource[nextKey];
                    }
                }
            }
        }
        return to;
    };
}
