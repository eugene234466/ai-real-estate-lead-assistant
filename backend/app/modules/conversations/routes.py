from flask import Blueprint, request, jsonify
from app.extensions import db
from app.modules.conversations.models import Conversation, Message
from app.modules.organizations.models import Organization
from app.modules.ai_engine.service import generate_ai_response