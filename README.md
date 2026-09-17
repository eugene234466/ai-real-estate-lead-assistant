# AI Real Estate Lead Assistant

AI-powered lead management and appointment automation for real estate businesses.

The platform helps real estate agents respond to inbound property inquiries, qualify prospects, automate follow-ups, and convert qualified leads into appointments while keeping humans in control.

## 🚀 MVP

The initial MVP focuses on one core workflow:

```text
Lead Inquiry
     ↓
AI Understanding
     ↓
AI Response
     ↓
Lead Qualification
     ↓
Follow-up
     ↓
Appointment
     ↓
Agent Notification
```

Agents can monitor conversations and take over whenever human intervention is required.

---

## ✨ Core Features

* 🤖 AI-powered lead conversations
* 🏠 Property management
* 👤 Lead management
* 💬 Real-time web chat
* 🧠 AI lead qualification
* 🔄 Automated follow-ups
* 📅 Appointment scheduling
* 👨‍💼 Human takeover
* 📊 Lead pipeline
* 📝 Conversation and event logging
* 🔐 Organization-based access and tenant isolation

---

## 🏗️ Architecture

```text
React + TypeScript
        │
        ↓
     Flask API
        │
   ┌────┴────┐
   ↓         ↓
PostgreSQL   AI Layer
             │
             ↓
        Groq / LLM
        │
        ↓
 Structured Output
        │
        ↓
 Business Logic
```

The LLM does not directly control the application.

The intended flow is:

```text
LLM
 ↓
Structured Output
 ↓
Validation
 ↓
Business Rules
 ↓
Application Action
```

---

## 🛠️ Tech Stack

### Frontend

* React
* TypeScript
* Vite

### Backend

* Python
* Flask
* SQLAlchemy
* Alembic

### Database

* PostgreSQL
* pgvector

### AI

* Groq
* `openai/gpt-oss-120b`

### Infrastructure

* Redis
* Background workers
* SSE for realtime updates
* Docker

---

## 📁 Project Structure

```text
.
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── features/
│       ├── api/
│       ├── hooks/
│       ├── types/
│       └── utils/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── ai/
│   │   ├── workflows/
│   │   ├── repositories/
│   │   └── tasks/
│   ├── migrations/
│   └── tests/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔄 Lead Lifecycle

The MVP uses an explicit lead state machine:

```text
NEW
 ↓
ENGAGED
 ↓
QUALIFYING
 ↓
QUALIFIED
 ↓
BOOKING
 ↓
BOOKED
```

Alternative paths:

```text
QUALIFYING → NURTURE
QUALIFYING → HUMAN_HANDOFF
ENGAGED → HUMAN_HANDOFF
BOOKING → HUMAN_HANDOFF
BOOKED → CLOSED
```

State transitions are controlled by the backend.

---

## 🤖 AI Responsibilities

The AI is responsible for:

### Understanding

Extract:

* Intent
* Property of interest
* Buying/renting
* Budget
* Location
* Timeline
* Missing information

### Responding

Generate concise, natural responses using verified business and property information.

### Qualifying

Progressively collect information needed to determine whether a lead is ready for the next step.

### Escalating

Identify conversations that require human intervention.

---

## 📦 Structured AI Output

The AI should return structured JSON rather than directly controlling application logic.

Example:

```json
{
  "intent": "property_inquiry",
  "property_id": "property_123",
  "buy_or_rent": "rent",
  "budget": 1500,
  "timeline": "next_month",
  "missing_information": [
    "viewing_preference"
  ],
  "lead_stage": "QUALIFYING",
  "next_action": "ASK_VIEWING_PREFERENCE",
  "human_handoff_required": false,
  "response": "Great. What day or time would you prefer for a viewing?"
}
```

Application flow:

```text
LLM
 ↓
Structured Output
 ↓
Validation
 ↓
Business Logic
 ↓
Action
```

The LLM must not directly:

* Modify database records
* Create appointments
* Change critical business state
* Execute arbitrary application actions

---

## 🏠 Property Data

Properties contain:

* Title
* Description
* Property type
* Sale/Rent
* Price
* Currency
* Location
* Bedrooms
* Bathrooms
* Amenities
* Availability

The AI must only use verified property information.

It must never invent:

* Prices
* Availability
* Amenities
* Property specifications
* Locations
* Business policies

If reliable information is unavailable, the AI should defer to a human agent.

---

## 👤 Lead Data

Leads contain:

* Name
* Email
* Phone
* Source
* Property
* Buy/Rent
* Budget
* Location preference
* Timeline
* Lead stage
* Assigned agent
* Last contact
* Next follow-up

Qualification should happen progressively rather than asking every question at once.

---

## 💬 Web Chat

The MVP supports **web chat only**.

A prospect can send a property inquiry and receive an AI response.

Example:

> "Hi, I'm interested in the 3-bedroom apartment. My budget is around $1,500 and I'd like to move next month."

The system should automatically:

1. Create/find the lead.
2. Identify the property.
3. Extract the budget.
4. Extract the timeline.
5. Retrieve verified property information.
6. Generate a response.
7. Store the conversation.
8. Continue qualification.

Future channels such as WhatsApp, SMS, and social media should be added later.

---

## 🔄 Follow-ups

If a lead stops responding:

```text
Lead inactive
 ↓
Follow-up scheduled
 ↓
AI generates contextual message
 ↓
Message sent
 ↓
Lead responds?
 /       \
YES       NO
 ↓         ↓
Continue  Nurture
```

Keep the initial follow-up system simple and reliable.

---

## 📅 Appointments

Agents can define:

* Available days
* Available hours
* Appointment duration

Appointment statuses:

```text
PENDING
CONFIRMED
CANCELLED
COMPLETED
NO_SHOW
```

When an appointment is booked:

```text
Lead → BOOKED
Appointment → Created
Agent → Notified
```

---

## 👨‍💼 Human Takeover

Agents remain in control.

At any point an agent can click:

**TAKE OVER**

This disables AI responses for that conversation.

```text
AI Conversation
      ↓
TAKE OVER
      ↓
AI Disabled
      ↓
Agent Responds
```

The agent can later select:

**RESUME AI**

AI should also recommend human handoff when:

* The lead requests an agent
* Negotiation is required
* Legal questions arise
* The AI lacks reliable information
* A complaint occurs
* The conversation becomes complex

---

## 📊 Dashboard

The dashboard should show:

* New leads
* Active conversations
* Qualified leads
* Follow-ups due
* Appointments
* Human handoffs

Advanced analytics are outside the initial MVP.

---

## 📥 Inbox

The agent inbox should display:

* Lead
* Conversation
* Messages
* Lead information
* Property
* Lead stage
* AI summary
* Next action

The interface should feel like a modern CRM/customer-support inbox.

---

## 📝 Event Logging

Track important events:

```text
lead.created
message.received
ai.response.generated
message.sent
lead.stage_changed
followup.scheduled
followup.sent
appointment.created
appointment.confirmed
human.handoff
agent.takeover
```

This is important for debugging, observability, and AI evaluation.

---

## 🔐 Security

Implement:

* Authentication
* Authorization
* Organization/tenant isolation
* Server-side validation
* Rate limiting
* Secure API key handling
* Prompt-injection protection
* AI output validation

Never expose the Groq API key to the frontend.

Never trust organization IDs supplied by the frontend.

---

## 📄 MVP Pages

Minimum pages:

```text
/login
/signup
/dashboard
/leads
/leads/:id
/inbox
/inbox/:conversationId
/properties
/properties/new
/properties/:id
/appointments
/settings
```

---

## 🗄️ Database

Minimum tables:

```text
organizations
users
properties
leads
conversations
messages
appointments
follow_ups
events
```

Tenant-owned records should contain:

```text
organization_id
```

---

## ⚡ Realtime

Use SSE initially for live conversation updates.

```text
Lead sends message
 ↓
Flask receives message
 ↓
AI processes
 ↓
AI response generated
 ↓
Backend saves response
 ↓
SSE pushes update
 ↓
React updates conversation
```

WebSockets can be introduced later if required.

---

## 🧪 MVP Demo

Seed the application with:

### Business

**Example Realty**

### Property

**3 Bedroom Apartment**

* Location: Accra
* Rent: $1,500/month
* Bedrooms: 3
* Bathrooms: 2
* Parking
* Security
* Balcony

### Test Inquiry

> "Hi, I'm interested in the 3-bedroom apartment. Is it available? My budget is around $1,500 and I'd like to move next month."

Expected flow:

```text
Inquiry
 ↓
Lead Created
 ↓
AI Understands
 ↓
Property Data Retrieved
 ↓
AI Responds
 ↓
Lead Information Updated
 ↓
Qualification
 ↓
Follow-up
 ↓
Appointment
 ↓
Agent Notification
```

The agent must be able to take over at any point.

---

## 🗺️ Development Roadmap

### Phase 1 — Foundation

* [ ] React + TypeScript
* [ ] Flask API
* [ ] PostgreSQL
* [ ] Authentication
* [ ] Organizations
* [ ] Properties
* [ ] Leads

### Phase 2 — AI Conversation

* [ ] Web chat
* [ ] Conversation storage
* [ ] Message handling
* [ ] Groq integration
* [ ] Structured AI responses
* [ ] Conversation history

### Phase 3 — Qualification

* [ ] Lead information extraction
* [ ] Qualification logic
* [ ] Lead state machine
* [ ] Human handoff

### Phase 4 — Automation

* [ ] Background jobs
* [ ] Follow-ups
* [ ] Appointment scheduling
* [ ] Agent notifications
* [ ] Realtime updates

### Phase 5 — Reliability

* [ ] AI evaluation tests
* [ ] Error handling
* [ ] Audit logging
* [ ] Security hardening
* [ ] Prompt injection protection
* [ ] Performance improvements

---

## 🚧 Out of Scope for MVP

Do not build yet:

* Flutter/mobile application
* WhatsApp
* SMS
* Voice agents
* Social media integrations
* Advanced CRM integrations
* Advanced analytics
* Enterprise SSO
* Multiple AI providers
* Multi-agent AI systems
* Microservices
* Advanced billing
* Complex autonomous workflows

---

## 🎯 MVP Definition of Done

The MVP is complete when a realistic prospect can go from:

```text
Inquiry
  ↓
AI Response
  ↓
Qualification
  ↓
Follow-up
  ↓
Appointment
```

with minimal manual intervention for the normal path.

At the same time, an agent must be able to intervene at any point.

All important actions must be persisted and observable.

### Priority

**Reliability > Feature Count > Complexity**

---

## 🤝 Development Philosophy

Build incrementally.

Start with the smallest end-to-end slice:

```text
React Chat
    ↓
Flask API
    ↓
PostgreSQL
    ↓
Groq
    ↓
AI Response
    ↓
React Chat
```

Then incrementally add:

```text
Lead Extraction
    ↓
Qualification
    ↓
State Machine
    ↓
Follow-up
    ↓
Appointments
    ↓
Human Handoff
    ↓
Dashboard
```

Avoid premature complexity.

The goal is to build a reliable product that can be tested with real users before expanding the feature set.
