import './lib/gapi';
// import './lib/fb';

export const Facebook = {
    init: (appId) => {
        window.fbAsyncInit = function () {
            FB.init({
                appId,
                xfbml: true,
                version: 'v2.7',
            });
        };
    },
    login(permissions) {
        return new Promise((resolve) => {
            if (typeof FB !== 'undefined') {
                FB.login(() => {
                    if (FB.getAccessToken()) {
                        resolve(FB.getAccessToken());
                    }
                }, { scope: permissions || 'public_profile,email' });
                return true;
            }
            return false;
        });
    },
    logout: () => new Promise((resolve) => {
        if (typeof FB !== 'undefined') {
            FB.logout((response) => {
                resolve();
                return true;
            });
        } else {
            return false;
        }
    }),
};

let _apiKey;
let _clientId;
export const Google = {
    init: (apiKey, clientId) => {
        _apiKey = apiKey;
        _clientId = clientId;
    },
    login: () => new Promise((resolve) => {
        gapi.client.setApiKey(_apiKey);
        gapi.auth.authorize({
            'client_id': _clientId,
            scope: 'email profile',
            prompt: 'select_account',
        }, (r) => {
            if (r.access_token) {
                resolve(r.access_token);
            }
        });
    }),
};
