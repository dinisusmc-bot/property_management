import type { Locator } from '@playwright/test'

type SafeClickOptions = {
  force?: boolean
  timeout?: number
}

export const safeClick = async (locator: Locator, options: SafeClickOptions = {}) => {
  const timeout = options.timeout ?? 10000

  await locator.waitFor({ state: 'visible', timeout })
  await locator.scrollIntoViewIfNeeded()

  try {
    await locator.click({ trial: true, timeout })
    await locator.click({ timeout })
  } catch (error) {
    if (options.force === false) {
      throw error
    }
    await locator.click({ force: true, timeout })
  }
}
