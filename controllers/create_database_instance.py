# from app import app
from flask import current_app as app
from controllers.database import db
from controllers.models import User, Role, UserRole, ParkingLot, ParkingSpot

def create_tables():
    with app.app_context():
        db.create_all()
        
        # Create roles
        user_role = Role.query.filter_by(name='user').first()
        admin_role = Role.query.filter_by(name='admin').first()

        if not user_role:
            user_role = Role(name='user')
            db.session.add(user_role)

        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)

        db.session.commit()

        # Create admin user
        admin = User.query.filter_by(email='admin@gmail.com').first()
        if not admin:
            admin_role = Role.query.filter_by(name='admin').first()
            admin = User(
                email='admin@gmail.com',
                password='admin123',
                roles=[admin_role]
            )
            db.session.add(admin)

        db.session.commit()

        # Create sample parking lots for demonstration
        if ParkingLot.query.count() == 0:
            # Sample parking lot 1
            lot1 = ParkingLot(
                prime_location_name='Downtown Plaza',
                price=50.0,
                address='123 Main Street, Downtown',
                pin_code='110001',
                maximum_number_of_spots=20
            )
            db.session.add(lot1)
            
            # Sample parking lot 2
            lot2 = ParkingLot(
                prime_location_name='Mall Complex',
                price=30.0,
                address='456 Shopping Avenue, City Center',
                pin_code='110002',
                maximum_number_of_spots=50
            )
            db.session.add(lot2)
            
            db.session.commit()
            
            # Create parking spots for each lot
            for lot in [lot1, lot2]:
                for spot_num in range(1, lot.maximum_number_of_spots + 1):
                    spot = ParkingSpot(
                        lot_id=lot.id,
                        spot_number=spot_num,
                        status='A'  # Available
                    )
                    db.session.add(spot)
            
            db.session.commit()
