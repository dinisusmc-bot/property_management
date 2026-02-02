# Charter Quote Landing Page

## Overview
A public-facing multi-page landing page that allows potential customers to request charter quotes without authentication. The form wizard collects trip details and automatically creates a charter entry with "quote" status in the system.

## Features

### 4-Step Quote Request Form

#### Step 1: Trip Details
- Trip date selection
- Number of passengers
- Estimated trip duration (hours)
- Overnight trip checkbox
- Weekend trip checkbox

#### Step 2: Vehicle Selection
- Interactive card-based vehicle selection
- Three vehicle types:
  - Luxury Coach (55 passengers)
  - Executive Minibus (30 passengers)
  - Shuttle Van (15 passengers)
- Shows capacity, base rate, and per-mile rate for each vehicle
- Smart recommendations based on passenger count

#### Step 3: Itinerary
- Dynamic stop management (minimum 2 stops)
- For each stop:
  - Location address
  - Arrival time (optional)
  - Departure time (optional)
  - Special notes (optional)
- Add/remove stops functionality
- First stop labeled as "Pickup", last as "Drop-off", middle as "Waypoint"

#### Step 4: Contact Information
- Customer name (required)
- Company name (optional)
- Email address (required, validated)
- Phone number
- Additional notes field

### User Experience
- Beautiful gradient design (purple theme)
- Material-UI Stepper showing progress
- Real-time validation with helpful error messages
- Success page with quote reference number
- Responsive design for mobile and desktop

## Technical Implementation

### Frontend
- **Location**: `/frontend/src/pages/QuoteLanding.tsx`
- **Route**: `/quote` (public, no auth required)
- **Framework**: React + TypeScript + Material-UI
- **State Management**: Local useState hooks

### Backend
- **Endpoint**: `POST /api/v1/charters/quotes/submit`
- **Location**: `/backend/services/charters/main.py`
- **Authentication**: None required (public endpoint)
- **Action**: Creates charter with status="quote"

### Data Flow
1. User fills out the 4-step form
2. Frontend validates all fields
3. Simple cost calculation (estimated):
   - Base cost = vehicle hourly rate × trip hours
   - Mileage cost = per mile rate × estimated miles
   - Additional fees = overnight fee if applicable
4. POST request to `/quotes/submit` endpoint
5. Backend creates:
   - Charter record with status="quote"
   - All itinerary stops linked to charter
   - Contact info stored in notes field
6. Success page shows quote reference ID

## Usage

### For Customers
1. Navigate to `http://localhost:3000/quote`
2. Complete the 4-step form
3. Submit quote request
4. Receive confirmation with quote ID
5. Team will email detailed quote within 24 hours

### For Admins
1. Quote requests appear in charter list with "Quote" status
2. Contact information stored in the notes field
3. Can convert quote to approved → booked → confirmed
4. Full charter workflow available

## Routes

### Public Routes (No Auth)
- `/` - Home page with company info and CTA
- `/home` - Same as root
- `/quote` - Quote request form
- `/login` - Login page

### Protected Routes (Auth Required)
- `/dashboard` - Admin/Manager dashboard
- `/charters` - Charter list (includes quotes)
- All other existing routes...

## Customization

### Vehicle Types
Update the `vehicles` state in `QuoteLanding.tsx`:
```typescript
const [vehicles] = useState([
  { id: 1, name: 'Your Vehicle', capacity: 50, base_rate: 150, per_mile_rate: 3.5 }
])
```

### Styling
- Theme colors: Purple gradient background
- Modify in `QuoteLanding.tsx` and `HomePage.tsx`
- Material-UI theme system for consistent styling

### Quote Calculation
Simple estimation in frontend for demo. For production:
- Integrate with distance API for accurate mileage
- Apply business rules (weekend fees, overnight fees)
- Use backend quote calculation endpoint

## Integration with Existing System

The quote landing page seamlessly integrates with the existing charter management system:

1. **Quote → Approval Flow**
   - Quotes start in "quote" status
   - Admin reviews and can approve
   - Transitions through: quote → approved → booked → confirmed → in_progress → completed

2. **Client Management**
   - Temporary client_id=1 used for quotes
   - Admin can create proper client record and reassign

3. **Notifications** (Future Enhancement)
   - Auto-email customer on quote submission
   - Email quote details when admin approves
   - SMS reminders before trip date

## Testing
- All form validations work correctly
- Backend endpoint creates charter records
- Success flow displays quote ID
- Responsive design tested on mobile/desktop

## Future Enhancements
1. Google Maps API integration for address autocomplete
2. Real-time distance/cost calculation
3. Email notifications to customer and admin
4. Multi-language support
5. Payment processing integration
6. Customer portal to view quote status
