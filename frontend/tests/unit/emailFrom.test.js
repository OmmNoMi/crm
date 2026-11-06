import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { buildFromOptions } from '../../src/utils/emailFrom'

const hello = {
  email_account: "Taniya D'silva",
  email_id: 'hello@taniyadsilva.com',
}
const gmail = {
  email_account: 'Its Taniya Dsilva',
  email_id: 'its.taniya.dsilva@gmail.com',
}

describe('buildFromOptions', () => {
  it('lists every sending account as "Account <address>"', () => {
    expect(buildFromOptions([hello, gmail], 'hello@taniyadsilva.com')).toEqual([
      {
        label: "Taniya D'silva <hello@taniyadsilva.com>",
        value: 'hello@taniyadsilva.com',
      },
      {
        label: 'Its Taniya Dsilva <its.taniya.dsilva@gmail.com>',
        value: 'its.taniya.dsilva@gmail.com',
      },
    ])
  })

  it('hides the row when the only account is the login address', () => {
    expect(buildFromOptions([hello], 'hello@taniyadsilva.com')).toEqual([])
  })

  it('keeps a single account that is not the login address', () => {
    expect(buildFromOptions([gmail], 'hello@taniyadsilva.com')).toHaveLength(1)
  })

  it('returns nothing before the accounts have loaded', () => {
    expect(buildFromOptions(undefined, 'a@b.c')).toEqual([])
    expect(buildFromOptions(null, 'a@b.c')).toEqual([])
    expect(buildFromOptions([], 'a@b.c')).toEqual([])
  })

  it('skips rows without an address', () => {
    expect(
      buildFromOptions([{ email_account: 'x', email_id: '' }, gmail], 'a@b.c'),
    ).toHaveLength(1)
  })
})

describe('EmailEditor From source', () => {
  // User.user_emails is permlevel 1 (System Manager only). Reading it off the
  // User document hides the From row for every other user.
  const source = readFileSync(
    resolve(import.meta.dirname, '../../src/components/EmailEditor.vue'),
    'utf8',
  )

  it('loads From accounts from the server method, not the User document', () => {
    expect(source).toContain("url: 'crm.api.user.get_sending_accounts'")
    expect(source).toContain(
      'buildFromOptions(sendingAccounts.data, sessionUser)',
    )
    expect(source).not.toMatch(/\.doc\??\.user_emails/)
    expect(source).not.toMatch(/useDocument\(\s*'User'/)
  })
})
