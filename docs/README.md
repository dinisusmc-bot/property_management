# Documentation Index

Welcome to the Athena Charter Management System documentation.

---

## 📚 Documentation Overview

### Getting Started
- **[README.md](../README.md)** - Project overview, quick start, architecture
- **[QUICKSTART.md](../QUICKSTART.md)** - Step-by-step startup guide and troubleshooting
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and feature list

### Feature Documentation
- **[FEATURES.md](FEATURES.md)** - Comprehensive feature documentation including:
  - Driver Feature
  - Invoice & Payment System
  - Document Management
  - Charter Workflow
  - Monitoring & Dashboards
  - Location Tracking
  - Pricing Engine
  - API Gateway (Kong)

### Specialized Guides
- **[DRIVER_FEATURE.md](DRIVER_FEATURE.md)** - Detailed driver implementation guide
- **[INVOICE_PAYMENT_SYSTEM.md](INVOICE_PAYMENT_SYSTEM.md)** - Payment processing deep dive
- **[GRAFANA_EMAIL_REPORTS.md](GRAFANA_EMAIL_REPORTS.md)** - Email report setup
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide (956 lines)

---

## 🎯 Quick Navigation

### I want to...

**Start the system**
→ Read [QUICKSTART.md](../QUICKSTART.md)

**Understand the architecture**
→ Read [README.md](../README.md) - System Architecture section

**Learn about specific features**
→ Read [FEATURES.md](FEATURES.md)

**Set up for production**
→ Read [DEPLOYMENT.md](DEPLOYMENT.md)

**Configure email reports**
→ Read [GRAFANA_EMAIL_REPORTS.md](GRAFANA_EMAIL_REPORTS.md)

**Implement driver workflow**
→ Read [DRIVER_FEATURE.md](DRIVER_FEATURE.md)

**Set up payment processing**
→ Read [INVOICE_PAYMENT_SYSTEM.md](INVOICE_PAYMENT_SYSTEM.md)

**See what's been built**
→ Read [CHANGELOG.md](../CHANGELOG.md)

---

## 📋 Document Summaries

### README.md (Main)
**Lines:** ~300
**Topics:**
- Quick start (5 commands)
- Default credentials
- System architecture (microservices + infrastructure)
- Key features (charter, financial, automation, monitoring)
- Project structure
- Common tasks
- Troubleshooting
- Security notes

### QUICKSTART.md
**Lines:** ~350
**Topics:**
- Starting/stopping the system
- Login credentials table
- Common workflows (create charter, send quote, book vendor, assign driver)
- View reports
- Troubleshooting by category
- Sample data overview
- Getting help commands

### CHANGELOG.md
**Lines:** ~400
**Topics:**
- Completed features (comprehensive list)
- Recent updates (driver feature, Grafana updates, location fixes)
- Known issues
- Planned features (short/medium/long term)
- Migration notes
- Version history

### FEATURES.md
**Lines:** ~500
**Topics:**
- Driver Feature (DB schema, API, frontend, UX)
- Invoice & Payment System (tables, automation, templates)
- Document Management (infrastructure, API, workflow)
- Charter Workflow (stages, automated actions)
- Monitoring & Dashboards (Grafana, email reports)
- Location Tracking (coordinates, queries, visualization)
- Pricing Engine (calculations, margins)
- API Gateway (routes, features)

### DEPLOYMENT.md
**Lines:** ~956
**Topics:**
- Prerequisites (hardware/software)
- Local deployment
- Production deployment
- Configuration
- Monitoring
- Troubleshooting
- Maintenance
- Security checklist
- Scaling strategies

### DRIVER_FEATURE.md
**Lines:** ~162
**Topics:**
- Overview
- Database changes
- Seed data (4 driver accounts)
- Backend API endpoints (3 new routes)
- Frontend components (DriverDashboard)
- Routing & navigation
- Authentication & permissions
- User experience flow
- Testing scenarios

### INVOICE_PAYMENT_SYSTEM.md
**Lines:** ~270
**Topics:**
- Overview
- Database tables (6 new tables)
- Updated charter fields
- Database functions and triggers
- Airflow automation (DAG details)
- Email templates (5 types)
- Frontend changes
- API endpoints
- Payment flow
- Stripe integration

### GRAFANA_EMAIL_REPORTS.md
**Lines:** ~296
**Topics:**
- Email configuration
- SMTP setup (Gmail, Office 365, SendGrid, AWS SES)
- Restart procedures
- Creating scheduled reports (UI and API methods)
- Report formats (PDF, PNG)
- Scheduling options
- Troubleshooting email delivery
- Example configurations

---

## 🗂️ File Organization

```
coachway_demo/
├── README.md                 # Start here
├── QUICKSTART.md            # Getting started guide
├── CHANGELOG.md             # What's been built
├── docs/
│   ├── README.md            # This file
│   ├── FEATURES.md          # Feature documentation
│   ├── DEPLOYMENT.md        # Production guide
│   ├── DRIVER_FEATURE.md    # Driver implementation
│   ├── INVOICE_PAYMENT_SYSTEM.md  # Payment system
│   └── GRAFANA_EMAIL_REPORTS.md   # Email reports
```

---

## 💡 Documentation Tips

### For New Users
1. Start with [README.md](../README.md)
2. Follow [QUICKSTART.md](../QUICKSTART.md)
3. Explore features in [FEATURES.md](FEATURES.md)

### For Developers
1. Read [README.md](../README.md) - Architecture section
2. Study [FEATURES.md](FEATURES.md) - API details
3. Review [CHANGELOG.md](../CHANGELOG.md) - Implementation history
4. Check [DEPLOYMENT.md](DEPLOYMENT.md) - Infrastructure

### For Operators
1. Follow [QUICKSTART.md](../QUICKSTART.md)
2. Configure using [GRAFANA_EMAIL_REPORTS.md](GRAFANA_EMAIL_REPORTS.md)
3. Deploy with [DEPLOYMENT.md](DEPLOYMENT.md)
4. Monitor using Grafana dashboards (described in [FEATURES.md](FEATURES.md))

### For Product Managers
1. Read [README.md](../README.md) - Key Features
2. Review [CHANGELOG.md](../CHANGELOG.md) - What's complete
3. Check [FEATURES.md](FEATURES.md) - Detailed capabilities

---

## 🔄 Keeping Documentation Updated

When adding new features:
1. Update [CHANGELOG.md](../CHANGELOG.md) with changes
2. Add feature details to [FEATURES.md](FEATURES.md)
3. Update [README.md](../README.md) if architecture changes
4. Create separate guide in `/docs` for major features

---

## 📞 Documentation Questions

If documentation is unclear or incomplete:
1. Check all relevant docs in this index
2. Review code comments in source files
3. Check container logs for runtime behavior
4. Test in development environment

---

Last Updated: December 8, 2025
