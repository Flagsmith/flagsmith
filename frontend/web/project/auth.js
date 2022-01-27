import _gapi from './lib/gapi';
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

export const Google = {
    login: () => new Promise((resolve) => {
        const json = JSON.parse(flagsmith.getValue('oauth_google'));
        _gapi(json.clientId, (GoogleAuth) => {
            gapi.auth2.authorize({
                client_id: json.clientId,
                scope: 'email profile',
                prompt: 'select_account',
                response_type: 'id_token permission',
            }, (r) => {
                if (r.access_token) {
                    resolve(r.access_token);
                }
            });
        });
    }),
};
