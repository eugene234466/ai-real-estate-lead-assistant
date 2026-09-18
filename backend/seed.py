from app import create_app          # adjust to your actual app factory name/path
from extensions import db
from backend.app.modules.organizations.models import Organization


def seed_demo_organization():
    existing = Organization.query.filter_by(name="Example Realty").first()

    if existing:
        print("Demo organization already seeded, skipping")
        return existing

    demo_org = Organization(name="Example Realty")
    db.session.add(demo_org)
    db.session.commit()

    print(f"Seeded organization: {demo_org.id}")
    return demo_org


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_demo_organization()