# backend/app/modules/appointments/routes.py

from datetime import datetime
import logging
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.extensions import db
from app.modules.appointments.models import Appointment
from app.modules.leads.models import Lead
from app.modules.leads.state_machine import apply_lead_stage, can_transition
from app.modules.notifications.models import Notification

logger = logging.getLogger(__name__)

appointments_bp = Blueprint('appointments', __name__)


def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


@appointments_bp.route('', methods=['POST'])
@jwt_required()
def create_appointment():
    org_id = get_jwt()["organization_id"]

    body = request.get_json()
    lead_id = body.get('lead_id') if body else None
    scheduled_at_raw = body.get('scheduled_at') if body else None
    duration_minutes = body.get('duration_minutes', 30) if body else 30
    notes = body.get('notes') if body else None

    if not lead_id or not scheduled_at_raw:
        return jsonify({"error": "lead_id and scheduled_at are required"}), 400

    if not is_valid_uuid(lead_id):
        return jsonify({"error": "lead not found"}), 404

    lead = Lead.query.filter_by(id=lead_id, organization_id=org_id).first()
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

    try:
        appointment = Appointment(
            organization_id=org_id,
            lead_id=lead.id,
            property_id=lead.property_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            notes=notes,
            status="PENDING"
        )
        db.session.add(appointment)
        db.session.flush()  # gets appointment.id without committing

        apply_lead_stage(lead, "BOOKED")

        notification = Notification(
            organization_id=org_id,
            lead_id=lead.id,
            appointment_id=appointment.id,
            type="NEW_APPOINTMENT",
            message=f"New appointment booked for {appointment.scheduled_at.isoformat()}"
        )
        db.session.add(notification)
        db.session.commit()  # appointment, lead stage, and notification land together
    except Exception:
        db.session.rollback()
        logger.exception("Failed to create appointment for lead %s", lead_id)
        return jsonify({"error": "Could not create appointment"}), 500

    logger.info("New appointment %s for lead %s", appointment.id, lead.id)

    return jsonify({
        "appointment_id": appointment.id,
        "lead_id": lead.id,
        "scheduled_at": appointment.scheduled_at.isoformat(),
        "status": appointment.status,
        "lead_stage": lead.lead_stage
    }), 201