# backend/app/modules/appointments/routes.py

from datetime import datetime
import logging
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.modules.appointments.models import Appointment
from app.modules.leads.models import Lead
from app.modules.leads.state_machine import apply_lead_stage, can_transition

logger = logging.getLogger(__name__)

appointments_bp = Blueprint('appointments', __name__)


@appointments_bp.route('', methods=['POST'])
def create_appointment():
    body = request.get_json()
    lead_id = body.get('lead_id') if body else None
    scheduled_at_raw = body.get('scheduled_at') if body else None
    duration_minutes = body.get('duration_minutes', 30) if body else 30
    notes = body.get('notes') if body else None

    if not lead_id or not scheduled_at_raw:
        return jsonify({"error": "lead_id and scheduled_at are required"}), 400

    lead = Lead.query.filter_by(id=lead_id).first()
    if not lead:
        return jsonify({"error": "lead not found"}), 404

    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_raw)
    except ValueError:
        return jsonify({"error": "scheduled_at must be a valid ISO datetime"}), 400

    if not can_transition(lead.lead_stage, "BOOKED"):
        return jsonify({
            "error": f"Cannot book appointment — lead is at '{lead.lead_stage}', which cannot transition to BOOKED"
        }), 409

    appointment = Appointment(
        organization_id=lead.organization_id,
        lead_id=lead.id,
        property_id=lead.property_id,
        scheduled_at=scheduled_at,
        duration_minutes=duration_minutes,
        notes=notes,
        status="PENDING"
    )
    db.session.add(appointment)
    db.session.commit()

    apply_lead_stage(lead, "BOOKED")
    db.session.commit()

    logger.info(f"Agent notification stub: new appointment {appointment.id} for lead {lead.id}")

    return jsonify({
        "appointment_id": appointment.id,
        "lead_id": lead.id,
        "scheduled_at": appointment.scheduled_at.isoformat(),
        "status": appointment.status,
        "lead_stage": lead.lead_stage
    }), 201