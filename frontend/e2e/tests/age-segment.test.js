// // FEATURES


``;/* eslint-disable func-names */
const expect = require('chai').expect;
const helpers = require('../helpers');

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const byId = helpers.byTestID;
const url = `http://localhost:${process.env.PORT || 8080}`;

// module.exports = {
    // '[Age Segment Test] - Login': function (browser) {
//     testHelpers.login(browser, url, email, password);

    //todo: create and goto project
//     browser.waitAndClick('#project-select-0');
// },
//
// // // Age == 18 || Age == 19
// '[Age Segment Test] - Create Segment': function (browser) {
//     testHelpers.gotoSegments(browser);
//
//     // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
//     // Rule 1- Age === 18 || Age === 19
//
//     testHelpers.createSegment(browser, 0, '18_or_19', [
//         // rule 2 =18 || =17
//         {
//             name: 'age',
//             operator: 'EQUAL',
//             value: 18,
//             ors: [
//                 {
//                     name: 'age',
//                     operator: 'EQUAL',
//                     value: 17,
//                 },
//             ],
//         },
//         // rule 2 >17 or <10
//         {
//             name: 'age',
//             operator: 'GREATER_THAN',
//             value: 17,
//             ors: [
//                 {
//                     name: 'age',
//                     operator: 'LESS_THAN',
//                     value: 10,
//                 },
//             ],
//         },
//         // rule 3 !=20
//         {
//             name: 'age',
//             operator: 'NOT_EQUAL',
//             value: 20,
//         },
//         // Rule 4 <= 18
//         {
//             name: 'age',
//             operator: 'LESS_THAN_INCLUSIVE',
//             value: 18,
//         },
//         // Rule 5 >= 18
//         {
//             name: 'age',
//             operator: 'GREATER_THAN_INCLUSIVE',
//             value: 18,
//         },
//     ]);
// },
// '[Age Segment Test] - Add segment trait for user': function (browser) {
//     testHelpers.gotoTraits(browser);
//     testHelpers.createTrait(browser, 0, 'age', 18);
// },
// '[Age Segment Test] - Check user now belongs to segment': function (browser) {
//     browser.waitForElementVisible(byId('segment-0-name'));
//     browser.expect.element(byId('segment-0-name')).text.to.equal('18_or_19');
// },
// '[Age Segment Test] - Delete segment trait for user': function (browser) {
//     testHelpers.deleteTrait(browser, 0);
// },
// '[Age Segment Test] - Delete segment': function (browser) {
//     testHelpers.gotoSegments(browser);
//     testHelpers.deleteSegment(browser, 0, '18_or_19');
// },
// };
