import { ClientFunction, Selector } from 'testcafe';

fixture`Submit a Form`
    .before((ctx) => {

    })
    .page`http://localhost:3000/`;

test('Submit a Form', async (t) => {
    await t.expect(Selector('[name="email"]').visible).ok();
});
