# Driver User Type Implementation

## Overview
Added a new "driver" user role that provides restricted access to view only their assigned charter itinerary, leave notes, and track location.

## Features Implemented

### 1. Database Changes
- **Table**: `charters`
- **New Column**: `driver_id` (INTEGER, nullable, indexed)
- **Purpose**: Links a charter to a specific driver user
- **Migration**: 
  ```sql
  ALTER TABLE charters ADD COLUMN driver_id INTEGER;
  CREATE INDEX ix_charters_driver_id ON charters(driver_id);
  ```

### 2. Seed Data
Created 4 driver test users:
- `driver1@athena.com` / `admin123`
- `driver2@athena.com` / `admin123`
- `driver3@athena.com` / `admin123`
- `driver4@athena.com` / `admin123`

9 out of 11 charters have drivers assigned for testing.

### 3. Backend API Endpoints

#### GET `/api/v1/charters/charters/driver/my-charter`
- Returns the charter assigned to the logged-in driver
- Includes: charter details, itinerary stops, vehicle information
- Returns `null` if no charter is assigned

#### PATCH `/api/v1/charters/charters/{charter_id}/driver-notes`
- Allows driver to update `vendor_notes` field
- Validates driver owns the charter (driver_id match)
- Request body: `{ "vendor_notes": "string" }`

#### PATCH `/api/v1/charters/charters/{charter_id}/location`
- Updates driver's current location
- Updates `last_checkin_location` and `last_checkin_time`
- Request body: `{ "location": "lat, long", "timestamp": "ISO-8601" }`
- Validates driver owns the charter

### 4. Frontend Components

#### DriverDashboard Component
**Location**: `frontend/src/pages/driver/DriverDashboard.tsx`

**Features**:
1. **Charter Details Card**
   - Trip date
   - Status
   - Passenger count
   - Vehicle information
   - Charter notes (read-only)

2. **Location Tracking Card**
   - Shows current location (latitude, longitude)
   - "Start/Stop Tracking" button
   - Auto-updates every 2 minutes when active
   - Uses browser Geolocation API

3. **Trip Itinerary Section**
   - Lists all stops in sequence
   - Shows location, arrival time, departure time
   - Stop-specific notes

4. **Driver Notes Section**
   - Multi-line text area for driver notes
   - Saves to `vendor_notes` field
   - "Save Notes" button

### 5. Routing & Navigation

#### App.tsx Changes
- Added `/driver` route pointing to `DriverDashboard`
- Auto-redirects drivers to `/driver` on login
- Blocks drivers from accessing admin pages

#### Layout.tsx Changes
- Hides sidebar navigation for driver role
- Full-width layout for drivers (no sidebar)
- Only shows header with user avatar and logout

### 6. Authentication & Permissions
- Drivers can only access `/driver` route
- Backend validates `driver_id` matches logged-in user
- Drivers blocked from all other pages (charters, clients, vendors, etc.)
- No sidebar menu items displayed

## User Experience

### Driver Login Flow
1. Driver logs in with credentials (e.g., `driver1@athena.com`)
2. Automatically redirected to `/driver` page
3. Sees their assigned charter (if any)
4. Can:
   - View trip itinerary
   - Start location tracking
   - Leave notes about the trip
5. No access to any other system features

### Driver Dashboard Layout
- **No Sidebar**: Full-width interface
- **Header Only**: Shows driver name and logout option
- **Single Page**: All functionality on one screen
- **Mobile Friendly**: Responsive design with Material-UI

## Use Case
Drivers are **temporary users** created 1-2 days before a charter:
- Created by admin/manager when charter is scheduled
- Assigned to specific charter via `driver_id`
- Access expires after trip completion
- Limited scope prevents access to business data

## Testing

### Test Login
```
Email: driver1@athena.com
Password: admin123
```

### Expected Behavior
1. Login redirects to `/driver`
2. See charter #1 details (or whichever charter driver1 is assigned to)
3. Can start location tracking (browser permission required)
4. Can type and save notes
5. Cannot navigate to other pages

## Technical Notes

### Location Tracking
- Uses browser `navigator.geolocation` API
- Updates every 120 seconds (2 minutes)
- Stores lat/long as comma-separated string
- Timestamp in ISO-8601 format

### Security
- All driver endpoints validate `driver_id === user_id`
- Returns 403 Forbidden if driver tries to access another's charter
- Frontend routing blocks access to non-driver pages

### Database Schema
```sql
charters
├── id
├── driver_id  (NEW - links to users.id where role='driver')
├── vendor_notes (used for driver notes)
├── last_checkin_location (updated by location tracking)
└── last_checkin_time (updated by location tracking)
```

## Future Enhancements
- [ ] Map view showing current location on route
- [ ] Push notifications for trip updates
- [ ] Photo upload capability (accident reports, etc.)
- [ ] Automatic trip completion when all stops checked in
- [ ] Driver signature for trip completion
- [ ] Real-time location sharing with dispatch
