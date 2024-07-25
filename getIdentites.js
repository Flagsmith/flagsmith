"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
var axios_1 = require("axios");
var apiKey = 'cH6prysA.mZ3RZon2oiiEuDA9JamZTFXVYFt7dERa';
var baseUrl = 'https://api.flagsmith.com/api/v1';
var api = axios_1.default.create({
    baseURL: baseUrl,
    headers: {
        Authorization: "Api-Key ".concat(apiKey),
        'Content-Type': 'application/json',
    },
});
var fetchProjects = function () { return __awaiter(void 0, void 0, void 0, function () {
    var response, error_1;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 2, , 3]);
                return [4 /*yield*/, api.get('/projects/')];
            case 1:
                response = _a.sent();
                return [2 /*return*/, response.data];
            case 2:
                error_1 = _a.sent();
                console.error('Error fetching projects:', error_1);
                throw error_1;
            case 3: return [2 /*return*/];
        }
    });
}); };
var fetchEnvironments = function (projectId) { return __awaiter(void 0, void 0, void 0, function () {
    var response, error_2;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 2, , 3]);
                return [4 /*yield*/, api.get("/projects/".concat(projectId, "/environments/"))];
            case 1:
                response = _a.sent();
                return [2 /*return*/, response.data];
            case 2:
                error_2 = _a.sent();
                console.error("Error fetching environments for project ".concat(projectId, ":"), error_2);
                throw error_2;
            case 3: return [2 /*return*/];
        }
    });
}); };
var fetchIdentities = function (environmentApiKey) { return __awaiter(void 0, void 0, void 0, function () {
    var response, error_3;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 2, , 3]);
                return [4 /*yield*/, api.get("/environments/".concat(environmentApiKey, "/identities/"))];
            case 1:
                response = _a.sent();
                return [2 /*return*/, response.data];
            case 2:
                error_3 = _a.sent();
                console.error("Error fetching identities for environment ".concat(environmentApiKey, ":"), error_3);
                throw error_3;
            case 3: return [2 /*return*/];
        }
    });
}); };
var main = function () { return __awaiter(void 0, void 0, void 0, function () {
    var projects, projectId, environments, environmentApiKey, identities, error_4;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 8, , 9]);
                return [4 /*yield*/, fetchProjects()];
            case 1:
                projects = _a.sent();
                console.log('Projects:', projects);
                if (!(projects.length > 0)) return [3 /*break*/, 6];
                projectId = projects[0].id;
                return [4 /*yield*/, fetchEnvironments(projectId)];
            case 2:
                environments = _a.sent();
                console.log('Environments:', environments);
                if (!(environments.length > 0)) return [3 /*break*/, 4];
                environmentApiKey = environments[0].api_key;
                return [4 /*yield*/, fetchIdentities(environmentApiKey)];
            case 3:
                identities = _a.sent();
                console.log('Identities:', identities);
                return [3 /*break*/, 5];
            case 4:
                console.log('No environments found.');
                _a.label = 5;
            case 5: return [3 /*break*/, 7];
            case 6:
                console.log('No projects found.');
                _a.label = 7;
            case 7: return [3 /*break*/, 9];
            case 8:
                error_4 = _a.sent();
                console.error('Error:', error_4);
                return [3 /*break*/, 9];
            case 9: return [2 /*return*/];
        }
    });
}); };
// Run the main function
main();
