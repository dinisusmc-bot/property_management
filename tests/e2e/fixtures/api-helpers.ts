import type { APIRequestContext } from '@playwright/test'

const KONG_BASE_URL = process.env.KONG_API_URL || 'http://localhost:8080'

let adminToken: string | null = null

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export const getKongBaseUrl = () => KONG_BASE_URL

export const requestWithRetry = async (
  request: APIRequestContext,
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  options: Record<string, any> = {},
  retries = 2,
  delayMs = 1500,
) => {
  let lastError: unknown

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const response = await (request as any)[method](url, options)
      return response
    } catch (error) {
      lastError = error
      if (attempt === retries) {
        throw error
      }
      await sleep(delayMs)
    }
  }

  throw lastError
}

export const getAdminAuthHeaders = async (request: APIRequestContext) => {
  if (!adminToken) {
    const response = await request.post(`${KONG_BASE_URL}/api/v1/auth/token`, {
      form: {
        username: 'admin@athena.com',
        password: 'admin123',
      },
    })

    if (!response.ok()) {
      throw new Error(`Failed to authenticate admin via Kong: ${response.status()} ${response.statusText()}`)
    }

    const data = await response.json()
    adminToken = data.access_token
  }

  return {
    Authorization: `Bearer ${adminToken}`,
  }
}

export const ensureClient = async (request: APIRequestContext) => {
  const headers = await getAdminAuthHeaders(request)

  const listResponse = await request.get(`${KONG_BASE_URL}/api/v1/clients`, { headers })
  if (!listResponse.ok()) {
    throw new Error(`Failed to load clients via Kong: ${listResponse.status()} ${listResponse.statusText()}`)
  }

  const clients = await listResponse.json()
  if (Array.isArray(clients) && clients.length > 0) {
    return clients[0]
  }

  const stamp = Date.now()
  const createResponse = await request.post(`${KONG_BASE_URL}/api/v1/clients`, {
    headers,
    data: {
      name: `Test Client ${stamp}`,
      type: 'corporate',
      email: `test.client.${stamp}@example.com`,
      phone: '555-0199',
      address: '100 Market St',
      city: 'San Francisco',
      state: 'CA',
      zip_code: '94105',
    },
  })

  if (!createResponse.ok()) {
    throw new Error(`Failed to create client via Kong: ${createResponse.status()} ${createResponse.statusText()}`)
  }

  return await createResponse.json()
}

export const ensureVehicle = async (request: APIRequestContext) => {
  const headers = await getAdminAuthHeaders(request)

  const response = await request.get(`${KONG_BASE_URL}/api/v1/vehicles`, { headers })
  if (!response.ok()) {
    throw new Error(`Failed to load vehicles via Kong: ${response.status()} ${response.statusText()}`)
  }

  const vehicles = await response.json()
  if (!Array.isArray(vehicles) || vehicles.length === 0) {
    throw new Error('No vehicles available via Kong. Ensure charter service seed data is loaded.')
  }

  return vehicles[0]
}

export const ensureCharter = async (request: APIRequestContext) => {
  const headers = await getAdminAuthHeaders(request)

  try {
    const listResponse = await request.get(`${KONG_BASE_URL}/api/v1/charters`, { headers })
    if (listResponse.ok()) {
      const charters = await listResponse.json()
      if (Array.isArray(charters) && charters.length > 0) {
        for (const charter of charters) {
          if (!charter?.id) {
            continue
          }

          const detailResponse = await request.get(`${KONG_BASE_URL}/api/v1/charters/${charter.id}`, { headers })
          if (detailResponse.ok()) {
            return await detailResponse.json()
          }
        }
      }
    }
  } catch (error) {
    // Ignore list failures and create a charter instead.
  }

  const client = await ensureClient(request)
  const vehicle = await ensureVehicle(request)

  const tripDate = new Date()
  tripDate.setDate(tripDate.getDate() + 10)

  const createResponse = await request.post(`${KONG_BASE_URL}/api/v1/charters`, {
    headers,
    data: {
      client_id: client.id,
      vehicle_id: vehicle.id,
      trip_date: tripDate.toISOString().split('T')[0],
      passengers: 20,
      trip_hours: 4,
      is_overnight: false,
      is_weekend: false,
      base_cost: 250,
      mileage_cost: 100,
      additional_fees: 0,
      total_cost: 350,
      status: 'quote',
    },
  })

  if (!createResponse.ok()) {
    throw new Error(`Failed to create charter via Kong: ${createResponse.status()} ${createResponse.statusText()}`)
  }

  return await createResponse.json()
}
