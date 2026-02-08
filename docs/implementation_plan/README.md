# Frontend Implementation Plan
## Athena Admin Portal - Complete Build Guide

**Project**: Athena Charter Management System  
**Date Started**: February 4, 2026  
**Current Status**: Backend 100% Complete | Frontend 35% Complete  
**Target Completion**: 16-18 weeks with 2 developers

---

## Table of Contents

- [Phase 1: Sales Agent Core Features](phase_1.md) - 4 weeks
- [Phase 2: Change Management & Sales Support](phase_2.md) - 3 weeks
- [Phase 3: Client & Vendor Portals](phase_3.md) - 4 weeks
- [Phase 4: Dispatch & Operations](phase_4.md) - 3 weeks
- [Phase 5: Accounting & Reporting](phase_5.md) - 3 weeks
- [Phase 6: Analytics & Configuration](phase_6.md) - 3 weeks
- [Phase 7: Advanced Features & Polish](phase_7.md) - 2 weeks

---

## Implementation Philosophy

### Core Principles

1. **Backend First Approach**: All backend APIs are complete and tested. Frontend implementation is purely UI/UX integration.

2. **Feature-Based Organization**: Group related components, hooks, and services by feature domain, not by type.

3. **Incremental Development**: Build, test, and deploy in small increments. Each feature should be independently testable.

4. **Type Safety First**: Use TypeScript strictly. Define interfaces before implementation.

5. **Reusable Components**: Build shared components for common patterns (tables, forms, dialogs, etc.).

6. **Consistent Patterns**: Follow existing codebase conventions for API calls, state management, and component structure.

---

## Technology Stack (Existing)

### Core Framework
- **React 18.2**: Modern React with hooks
- **TypeScript 5.2**: Strict type checking
- **Vite 5.0**: Fast build tool and dev server

### UI Library
- **Material-UI 5.14**: Component library
- **@mui/icons-material**: Icon set
- **@emotion/react & @emotion/styled**: CSS-in-JS

### State Management
- **Zustand 4.4**: Lightweight state management (auth currently)
- **@tanstack/react-query 5.12**: Server state management (TO BE ADDED)

### Routing
- **React Router 6.20**: Client-side routing with protected routes

### Forms & Validation
- **React Hook Form 7.49**: Form state management
- **Zod 3.22**: Schema validation
- **@hookform/resolvers**: Hook form + Zod integration

### HTTP Client
- **Axios 1.6**: HTTP client with interceptors

### Utilities
- **date-fns 3.0**: Date manipulation and formatting

---

## Project Structure

```
frontend/
├── src/
│   ├── features/              # Feature-based modules (NEW)
│   │   ├── leads/             # Lead management
│   │   ├── quotes/            # Quote builder
│   │   ├── changes/           # Change management
│   │   ├── dispatch/          # Dispatch board
│   │   ├── analytics/         # Reports & analytics
│   │   └── config/            # Configuration management
│   │
│   ├── pages/                 # Page components (EXISTING)
│   │   ├── charters/          # Charter pages
│   │   ├── clients/           # Client pages
│   │   ├── vendors/           # Vendor pages
│   │   ├── users/             # User pages
│   │   ├── payments/          # Payment pages
│   │   └── driver/            # Driver dashboard
│   │
│   ├── components/            # Shared components (EXISTING)
│   │   ├── Layout.tsx
│   │   ├── DocumentUploadDialog.tsx
│   │   └── [new shared components]
│   │
│   ├── shared/                # Shared utilities (NEW)
│   │   ├── components/        # Reusable UI components
│   │   ├── hooks/             # Custom hooks
│   │   ├── utils/             # Helper functions
│   │   └── types/             # Shared TypeScript types
│   │
│   ├── services/              # API services (EXISTING)
│   │   ├── api.ts             # Axios instance
│   │   └── auth.ts            # Auth service
│   │
│   ├── store/                 # State management (EXISTING)
│   │   └── authStore.ts       # Zustand auth store
│   │
│   ├── App.tsx                # Main app component
│   ├── main.tsx               # Entry point
│   └── theme.ts               # MUI theme config
│
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## Lessons Learned from Existing Codebase

### ✅ What's Working Well

1. **Protected Routes Pattern**: The `ProtectedRoute` and `NonVendorRoute` wrappers work well for role-based access control.

2. **Layout Component**: Responsive sidebar navigation with role-based menu filtering is clean and functional.

3. **API Interceptors**: Centralized error handling and token management in axios interceptors is effective.

4. **Material-UI Integration**: Consistent use of MUI components provides professional UI out of the box.

5. **TypeScript Interfaces**: Components that define interfaces for data structures are maintainable and type-safe.

### ⚠️ Areas for Improvement

1. **State Management**: Currently only using Zustand for auth. Need React Query for server state caching and synchronization.

2. **Code Organization**: Pages are getting large (CharterDetail.tsx is 1674 lines). Need to extract components and hooks.

3. **Form Validation**: Not consistently using React Hook Form + Zod. Some forms have manual validation.

4. **Error Handling**: Errors are handled differently across components. Need standardized error handling.

5. **Loading States**: Loading indicators are inconsistent. Need centralized loading state management.

6. **API Service Layer**: API calls are inline in components. Should be extracted to service layer with typed responses.

---

## Implementation Flow

### Step 1: Setup & Foundation (Week 1)

**For every phase:**

1. **Create Feature Directory Structure**
   ```
   src/features/<feature-name>/
   ├── components/        # Feature-specific components
   ├── hooks/             # Custom hooks for this feature
   ├── api/               # API service functions
   ├── types/             # TypeScript interfaces
   └── index.ts           # Public exports
   ```

2. **Define TypeScript Interfaces**
   - Create `types/<feature>.types.ts`
   - Define all data structures
   - Define API request/response types
   - Export from `index.ts`

3. **Create API Service Functions**
   - Create `api/<feature>Api.ts`
   - Define typed API calls
   - Use existing axios instance
   - Handle errors consistently

4. **Build Custom Hooks**
   - Create `hooks/use<Feature>Query.ts` for data fetching
   - Create `hooks/use<Feature>Mutation.ts` for data mutations
   - Use React Query for caching and state management

5. **Build UI Components**
   - Start with list/table view
   - Then detail/form view
   - Then dialogs/modals
   - Use Material-UI components

6. **Add Routes**
   - Update `App.tsx` with new routes
   - Add to navigation menu in `Layout.tsx`
   - Ensure proper route protection

### Step 2: Testing Strategy

**For every feature:**

1. **Manual Testing**
   - Test all CRUD operations
   - Test all form validations
   - Test error scenarios
   - Test different user roles

2. **Integration Testing**
   - Test API integration with backend
   - Test navigation flows
   - Test state persistence

3. **Edge Cases**
   - Empty states (no data)
   - Loading states
   - Error states
   - Permission denied states

### Step 3: Code Review Checklist

**Before marking feature complete:**

- [ ] TypeScript: No `any` types, all interfaces defined
- [ ] Forms: Using React Hook Form + Zod validation
- [ ] API: Using React Query for data fetching
- [ ] Errors: Proper error handling and user feedback
- [ ] Loading: Clear loading indicators
- [ ] Responsive: Works on mobile, tablet, desktop
- [ ] Accessibility: Proper labels, keyboard navigation
- [ ] Code Quality: Components < 300 lines, functions extracted
- [ ] Consistency: Follows existing codebase patterns
- [ ] Documentation: Complex logic has comments

---

## Common Patterns & Reusable Code

### Pattern 1: Data Table with Filters

```typescript
// Example: Lead list with filters
import { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  CircularProgress,
  Alert
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { leadApi } from '@/features/leads/api/leadApi'

export default function LeadList() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState({ status: '', search: '' })
  
  const { data: leads, isLoading, error } = useQuery({
    queryKey: ['leads', filters],
    queryFn: () => leadApi.getAll(filters)
  })
  
  if (isLoading) return <CircularProgress />
  if (error) return <Alert severity="error">Failed to load leads</Alert>
  
  return (
    <Box>
      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <TextField
          label="Search"
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        />
      </Paper>
      
      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {leads?.map((lead) => (
              <TableRow key={lead.id}>
                <TableCell>{lead.id}</TableCell>
                <TableCell>{lead.name}</TableCell>
                <TableCell>{lead.status}</TableCell>
                <TableCell>
                  <Button onClick={() => navigate(`/leads/${lead.id}`)}>
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
```

### Pattern 2: Form with React Hook Form + Zod

```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { TextField, Button, Box, Alert } from '@mui/material'

const leadSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  phone: z.string().min(10, 'Phone must be at least 10 digits'),
})

type LeadFormData = z.infer<typeof leadSchema>

export default function LeadForm({ onSuccess }: { onSuccess: () => void }) {
  const queryClient = useQueryClient()
  
  const { register, handleSubmit, formState: { errors } } = useForm<LeadFormData>({
    resolver: zodResolver(leadSchema)
  })
  
  const mutation = useMutation({
    mutationFn: leadApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      onSuccess()
    }
  })
  
  return (
    <Box component="form" onSubmit={handleSubmit(mutation.mutate)}>
      <TextField
        {...register('name')}
        label="Name"
        error={!!errors.name}
        helperText={errors.name?.message}
        fullWidth
        margin="normal"
      />
      
      <TextField
        {...register('email')}
        label="Email"
        error={!!errors.email}
        helperText={errors.email?.message}
        fullWidth
        margin="normal"
      />
      
      <TextField
        {...register('phone')}
        label="Phone"
        error={!!errors.phone}
        helperText={errors.phone?.message}
        fullWidth
        margin="normal"
      />
      
      {mutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {mutation.error?.message || 'Failed to save'}
        </Alert>
      )}
      
      <Button
        type="submit"
        variant="contained"
        disabled={mutation.isPending}
        sx={{ mt: 2 }}
      >
        {mutation.isPending ? 'Saving...' : 'Save'}
      </Button>
    </Box>
  )
}
```

### Pattern 3: API Service Layer

```typescript
// src/features/leads/api/leadApi.ts
import api from '@/services/api'
import { Lead, CreateLeadRequest, UpdateLeadRequest } from '../types/lead.types'

export const leadApi = {
  getAll: async (filters?: { status?: string; search?: string }) => {
    const params = new URLSearchParams()
    if (filters?.status) params.append('status', filters.status)
    if (filters?.search) params.append('search', filters.search)
    
    const response = await api.get<Lead[]>(`/api/v1/sales/leads?${params}`)
    return response.data
  },
  
  getById: async (id: number) => {
    const response = await api.get<Lead>(`/api/v1/sales/leads/${id}`)
    return response.data
  },
  
  create: async (data: CreateLeadRequest) => {
    const response = await api.post<Lead>('/api/v1/sales/leads', data)
    return response.data
  },
  
  update: async (id: number, data: UpdateLeadRequest) => {
    const response = await api.patch<Lead>(`/api/v1/sales/leads/${id}`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    await api.delete(`/api/v1/sales/leads/${id}`)
  },
  
  convertToQuote: async (id: number) => {
    const response = await api.post<{ charter_id: number }>(`/api/v1/sales/leads/${id}/convert`)
    return response.data
  }
}
```

### Pattern 4: Custom Hook for Data Fetching

```typescript
// src/features/leads/hooks/useLeadQuery.ts
import { useQuery } from '@tanstack/react-query'
import { leadApi } from '../api/leadApi'

export function useLeads(filters?: { status?: string; search?: string }) {
  return useQuery({
    queryKey: ['leads', filters],
    queryFn: () => leadApi.getAll(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useLead(id: number) {
  return useQuery({
    queryKey: ['leads', id],
    queryFn: () => leadApi.getById(id),
    enabled: !!id, // Only fetch if id exists
  })
}
```

### Pattern 5: Custom Hook for Mutations

```typescript
// src/features/leads/hooks/useLeadMutation.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { leadApi } from '../api/leadApi'
import toast from 'react-hot-toast' // TO BE ADDED

export function useCreateLead() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  
  return useMutation({
    mutationFn: leadApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead created successfully')
      navigate(`/leads/${data.id}`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create lead')
    }
  })
}

export function useUpdateLead(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: UpdateLeadRequest) => leadApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads', id] })
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update lead')
    }
  })
}

export function useConvertLeadToQuote(id: number) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  
  return useMutation({
    mutationFn: () => leadApi.convertToQuote(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead converted to quote')
      navigate(`/charters/${data.charter_id}`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to convert lead')
    }
  })
}
```

---

## Backend API Reference

All backend services are available at `http://localhost:8080/api/v1/` through Kong Gateway.

### Available Services

| Service | Port | Base URL | Purpose |
|---------|------|----------|---------|
| Auth | 8000 | `/api/v1/auth` | Authentication, users, roles |
| Charter | 8001 | `/api/v1/charters` | Charter operations |
| Client | 8002 | `/api/v1/clients` | Client management |
| Document | 8003 | `/api/v1/documents` | File storage |
| Payments | 8005 | `/api/v1/payments` | Payment processing |
| Notifications | 8006 | `/api/v1/notifications` | Email/SMS |
| Pricing | 8007 | `/api/v1/pricing` | Dynamic pricing |
| Vendor | 8008 | `/api/v1/vendors` | Vendor management |
| Sales | 8009 | `/api/v1/sales` | Leads, pipeline |
| Portals | 8010 | `/api/v1/portals` | Portal data |
| Changes | 8011 | `/api/v1/changes` | Change management |
| Dispatch | 8012 | `/api/v1/dispatch` | Dispatch operations |
| Analytics | 8013 | `/api/v1/analytics` | Reports, BI |
| Signatures | 8014 | `/api/v1/signatures` | E-signatures |

### Authentication

All API requests require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

Token is automatically added by axios interceptor in `src/services/api.ts`.

---

## Development Workflow

### Daily Process

1. **Morning Standup** (15 min)
   - What did you complete yesterday?
   - What will you work on today?
   - Any blockers?

2. **Development** (6-7 hours)
   - Pick task from current phase
   - Create feature branch: `feature/<phase>-<feature-name>`
   - Implement following patterns above
   - Test locally
   - Commit with clear messages

3. **Code Review** (1 hour)
   - Create PR to `backend_updates` branch
   - Senior dev reviews
   - Address feedback
   - Merge when approved

4. **End of Day** (30 min)
   - Update task status
   - Document any issues or learnings
   - Prepare for tomorrow

### Weekly Process

1. **Monday**: Sprint planning, task breakdown
2. **Wednesday**: Mid-week demo to stakeholders
3. **Friday**: Sprint review, retrospective, deploy to staging

---

## Quality Standards

### Code Quality Metrics

- **TypeScript Coverage**: 100% (no `any` types)
- **Component Size**: < 300 lines (extract if larger)
- **Function Complexity**: < 20 cyclomatic complexity
- **Test Coverage**: > 80% for critical paths
- **Bundle Size**: < 1MB initial load
- **Performance**: < 3s page load time

### Definition of Done

A feature is "done" when:

- [ ] All code is written and committed
- [ ] TypeScript types are defined
- [ ] Forms use React Hook Form + Zod
- [ ] API calls use React Query
- [ ] Error handling is implemented
- [ ] Loading states are shown
- [ ] Responsive on mobile, tablet, desktop
- [ ] Tested manually on all user roles
- [ ] Code reviewed and approved
- [ ] Merged to `backend_updates` branch
- [ ] Deployed to staging and verified
- [ ] Documentation updated

---

## Dependencies to Add

### Required Packages

```bash
# React Query for server state management
npm install @tanstack/react-query@5.12.2

# React Query DevTools (dev only)
npm install -D @tanstack/react-query-devtools@5.12.2

# Toast notifications
npm install react-hot-toast@2.4.1

# Calendar/date picker
npm install @mui/x-date-pickers@6.18.6

# Rich text editor (for email templates)
npm install @tiptap/react@2.1.13 @tiptap/starter-kit@2.1.13

# PDF generation
npm install jspdf@2.5.1 jspdf-autotable@3.8.0

# Excel export
npm install xlsx@0.18.5

# Charts (for analytics)
npm install recharts@2.10.3

# WebSocket (for real-time features)
npm install socket.io-client@4.6.1

# Image cropping (for photo uploads)
npm install react-easy-crop@5.0.2

# Testing libraries
npm install -D @testing-library/react@14.1.2
npm install -D @testing-library/user-event@14.5.1
npm install -D @testing-library/jest-dom@6.1.5
npm install -D vitest@1.0.4
npm install -D @playwright/test@1.40.1
```

### Setup React Query

```typescript
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <App />
        </ThemeProvider>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
)
```

### Setup Toast Notifications

```typescript
// src/main.tsx
import { Toaster } from 'react-hot-toast'

// Add to render:
<Toaster
  position="top-right"
  toastOptions={{
    duration: 4000,
    style: {
      background: '#363636',
      color: '#fff',
    },
    success: {
      duration: 3000,
      iconTheme: {
        primary: '#4caf50',
        secondary: '#fff',
      },
    },
    error: {
      duration: 5000,
      iconTheme: {
        primary: '#f44336',
        secondary: '#fff',
      },
    },
  }}
/>
```

---

## Getting Started

### For Senior Developer

1. Review this README and all phase documents
2. Set up development environment
3. Install new dependencies
4. Create feature branch: `feature/phase-1-setup`
5. Set up React Query and Toast notifications
6. Create shared components folder structure
7. Start Phase 1: Lead Management

### For Junior Developer

1. Read this README thoroughly
2. Review existing codebase patterns
3. Start with small, well-defined tasks
4. Follow patterns exactly as shown
5. Ask questions early and often
6. Test everything manually
7. Submit PRs for review frequently

---

## Support & Resources

### Documentation
- [Material-UI Docs](https://mui.com/material-ui/getting-started/)
- [React Query Docs](https://tanstack.com/query/latest/docs/react/overview)
- [React Hook Form Docs](https://react-hook-form.com/get-started)
- [Zod Docs](https://zod.dev/)

### Internal Resources
- [Frontend Gap Analysis](../FRONTEND_GAP_ANALYSIS.md)
- [Backend API Testing Results](../WORKFLOW_TEST_REPORT.md)
- [Project Structure](../../PROJECT_STRUCTURE.md)
- [Client Requirements](../client_needs.md)

### Getting Help
- **Backend Questions**: Check API documentation, test with curl/Postman
- **Frontend Questions**: Review existing components, check MUI docs
- **Blockers**: Escalate in daily standup
- **Bugs**: Create issue with reproduction steps

---

## Success Criteria

### Phase Completion
Each phase is complete when:
- All features implemented and tested
- All code reviewed and merged
- Documentation updated
- Staging deployment successful
- Stakeholder demo approved

### Project Completion
Project is complete when:
- All 7 phases finished
- 100% of client requirements met
- All tests passing
- Performance targets met
- Production deployment successful
- User training completed

---

**Next Steps**: Begin with [Phase 1: Sales Agent Core Features](phase_1.md)
