# ⚡ Quick Start

## 1. Clone & Setup

```bash
cd ~/projects/property_management

# Create .env file from example
cp .env.example .env

# Edit .env with your config (DB, Stripe keys, etc.)
nano .env  # or vim, etc.
```

## 2. Start Services

```bash
# Start all services (background)
./start-all.sh

# Or manually with Docker Compose
docker-compose -f docker-compose.staging.yml up -d
```

## 3. Verify Health

```bash
# Check all services
curl http://localhost:8015/health  # owners
curl http://localhost:8016/health  # properties
curl http://localhost:8017/health  # units
curl http://localhost:8018/health  # tenants
curl http://localhost:8019/health  # maintenance
```

## 4. Access Frontend

Open your browser: **http://localhost:3002**

**Default login**:
- Email: `admin@pm-demo.com`
- Password: `password`

## 5. API Testing (Postman/curl)

```bash
# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@pm-demo.com","password":"password"}'

# Get owners (replace TOKEN with your access_token)
curl http://localhost:8080/api/v1/owners/owners \
  -H "Authorization: Bearer TOKEN"
```

## 6. Stop Services

```bash
docker-compose -f docker-compose.staging.yml down
# or
./stop-all.sh
```

---

*For more details, see [docs/architecture.md](architecture.md) and [docs/api-guide.md](api-guide.md)*
