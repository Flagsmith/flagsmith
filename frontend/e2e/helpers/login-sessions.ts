import { Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// The API allows 20 logins a minute, fewer than the suite needs, so each user
// logs in through the form once per run and later logins reuse the token.
const SESSIONS_DIR = path.join(__dirname, '..', '.sessions');
const TOKEN_COOKIE = 't';

const sessionFile = (email: string) => path.join(SESSIONS_DIR, `${email}.json`);

export const clearLoginSessions = () => {
  fs.rmSync(SESSIONS_DIR, { force: true, recursive: true });
};

export const saveLoginSession = async (page: Page, email: string) => {
  const cookies = await page.context().cookies();
  const token = cookies.find((cookie) => cookie.name === TOKEN_COOKIE);
  if (!token) return;
  fs.mkdirSync(SESSIONS_DIR, { recursive: true });
  // Written then renamed, so a parallel worker never reads half a file
  const tmp = `${sessionFile(email)}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(token));
  fs.renameSync(tmp, sessionFile(email));
};

export const forgetLoginSession = (email: string) => {
  fs.rmSync(sessionFile(email), { force: true });
};

export const restoreLoginSession = async (page: Page, email: string) => {
  if (!fs.existsSync(sessionFile(email))) return false;
  const token = JSON.parse(fs.readFileSync(sessionFile(email), 'utf8'));
  await page.context().clearCookies({ name: TOKEN_COOKIE });
  await page.context().addCookies([token]);
  return true;
};
