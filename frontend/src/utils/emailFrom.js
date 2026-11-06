/**
 * Options for the From dropdown in the email composer.
 *
 * `accounts` comes from `crm.api.user.get_sending_accounts`: the session
 * user's own email accounts that have outgoing on. Returns [] (row hidden)
 * when there is nothing to choose: no account, or one account whose address
 * is the user's own login, which is what the email is sent as anyway.
 *
 * @param {Array<{email_account: string, email_id: string}>} accounts
 * @param {string} sessionUser
 * @returns {Array<{label: string, value: string}>}
 */
export function buildFromOptions(accounts, sessionUser) {
  const options = (accounts || [])
    .filter((a) => a?.email_id)
    .map((a) => ({
      label: `${a.email_account} <${a.email_id}>`,
      value: a.email_id,
    }))

  if (options.length === 1 && options[0].value === sessionUser) return []

  return options
}
