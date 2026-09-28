from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

celery = Celery(
    'ai_real_estate_assistant',
    broker = os.getenv('REDIS_URL', default='redis://localhost:6379/0'),
    backend= os.getenv('REDIS_URL', default='redis://localhost:6379/0'),
    include = ['app.modules.followups.tasks']
)

celery.conf.update(
    task_serializer = 'json',
    accept_content = ['json'],
    result_serializer = 'json',
    timezone = 'UTC',
    enable_utc = True,
    beat_schedule = {
        'scan-inactive-leads':{
            'task': 'app.modules.followups.tasks.scan_inactive_leads',
            'schedule': 60
        }
    
    }
)
