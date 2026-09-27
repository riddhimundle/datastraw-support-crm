# ResolveDesk — Support CRM

A full-stack customer support ticket management system built for the Datastraw Technologies AI + Tech Intern assessment.

## Features

- Create support tickets
- Automatic ticket IDs
- Ticket creation timestamps
- View all tickets
- Search tickets by ID, customer, email, subject, or description
- Filter tickets by status
- View ticket details
- Update ticket status
- Add internal notes
- Responsive dashboard UI

## Tech Stack

- Python
- FastAPI
- SQLite
- HTML
- CSS
- JavaScript

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/tickets` | Create ticket |
| GET | `/api/tickets` | List/search/filter tickets |
| GET | `/api/tickets/{ticket_id}` | Get ticket details |
| PUT | `/api/tickets/{ticket_id}` | Update status/add notes |

## Running Locally

```bash
python -m venv venv