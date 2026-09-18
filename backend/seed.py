# backend/seed.py

from app import create_app
from app.extensions import db
from app.modules.organizations.models import Organization
from app.modules.properties.models import Property


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


def seed_demo_property(organization):
    existing = Property.query.filter_by(
        title="3 Bedroom Apartment",
        organization_id=organization.id
    ).first()

    if existing:
        print("Demo property already seeded, skipping")
        return existing

    demo_property = Property(
        organization_id=organization.id,
        title="3 Bedroom Apartment",
        description="Spacious 3-bedroom apartment with modern finishes.",
        property_type="apartment",
        listing_type="rent",
        price=1500.00,
        currency="USD",
        location="Accra",
        bedrooms=3,
        bathrooms=2,
        amenities=["Parking", "Security", "Balcony"],
        availability_status="available"
    )
    db.session.add(demo_property)
    db.session.commit()

    print(f"Seeded property: {demo_property.id}")
    return demo_property


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        org = seed_demo_organization()
        seed_demo_property(org)