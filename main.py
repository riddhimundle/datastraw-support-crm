from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database import get_connection, create_tables

app = FastAPI(title="ResolveDesk API")

create_tables()


# -------------------------
# Request models
# -------------------------

class TicketCreate(BaseModel):
    customer_name: str
    customer_email: str
    subject: str
    description: str


class TicketUpdate(BaseModel):
    status: str
    notes: str | None = None


# -------------------------
# Frontend
# -------------------------

@app.get("/")
def home():
    return FileResponse("index.html")


# -------------------------
# CREATE TICKET
# -------------------------

@app.post("/api/tickets")
def create_ticket(ticket: TicketCreate):

    connection = get_connection()

    # Find the next ticket number
    row = connection.execute(
        "SELECT COUNT(*) as count FROM tickets"
    ).fetchone()

    next_number = row["count"] + 1
    ticket_id = f"TKT-{next_number:03d}"

    now = datetime.now().isoformat(timespec="seconds")

    connection.execute(
        """
        INSERT INTO tickets
        (
            ticket_id,
            customer_name,
            customer_email,
            subject,
            description,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            ticket.customer_name,
            ticket.customer_email,
            ticket.subject,
            ticket.description,
            "Open",
            now,
            now,
        ),
    )

    connection.commit()
    connection.close()

    return {
        "ticket_id": ticket_id,
        "created_at": now
    }


# -------------------------
# LIST / SEARCH / FILTER
# -------------------------

@app.get("/api/tickets")
def get_tickets(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None)
):

    connection = get_connection()

    query = """
        SELECT
            ticket_id,
            customer_name,
            customer_email,
            subject,
            status,
            created_at
        FROM tickets
        WHERE 1=1
    """

    params = []

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if search:
        query += """
            AND (
                LOWER(ticket_id) LIKE LOWER(?)
                OR LOWER(customer_name) LIKE LOWER(?)
                OR LOWER(customer_email) LIKE LOWER(?)
                OR LOWER(subject) LIKE LOWER(?)
                OR LOWER(description) LIKE LOWER(?)
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
        ])

    query += " ORDER BY created_at DESC"

    rows = connection.execute(query, params).fetchall()

    connection.close()

    return [dict(row) for row in rows]


# -------------------------
# VIEW SINGLE TICKET
# -------------------------

@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):

    connection = get_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,),
    ).fetchone()

    if not ticket:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    notes = connection.execute(
        """
        SELECT note_text, created_at
        FROM notes
        WHERE ticket_id = ?
        ORDER BY created_at DESC
        """,
        (ticket_id,),
    ).fetchall()

    connection.close()

    result = dict(ticket)
    result["notes"] = [dict(note) for note in notes]

    return result


# -------------------------
# UPDATE TICKET
# -------------------------

@app.put("/api/tickets/{ticket_id}")
def update_ticket(
    ticket_id: str,
    update: TicketUpdate
):

    allowed_statuses = {
        "Open",
        "In Progress",
        "Closed"
    }

    if update.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    connection = get_connection()

    ticket = connection.execute(
        "SELECT ticket_id FROM tickets WHERE ticket_id = ?",
        (ticket_id,),
    ).fetchone()

    if not ticket:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    now = datetime.now().isoformat(timespec="seconds")

    connection.execute(
        """
        UPDATE tickets
        SET status = ?, updated_at = ?
        WHERE ticket_id = ?
        """,
        (
            update.status,
            now,
            ticket_id,
        ),
    )

    if update.notes and update.notes.strip():

        connection.execute(
            """
            INSERT INTO notes
            (
                ticket_id,
                note_text,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                ticket_id,
                update.notes.strip(),
                now,
            ),
        )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "updated_at": now
    }