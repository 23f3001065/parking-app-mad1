from flask import render_template, request, flash, redirect, url_for, session, jsonify
from controllers.models import *
from controllers.database import db
from datetime import datetime
import math

# Import app after it's created
from app import app

def require_login(f):
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_admin(f):
    def decorated_function(*args, **kwargs):
        if 'email' not in session or 'admin' not in session.get('roles', []):
            flash('Admin access required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def home():
    if 'email' in session:
        if 'admin' in session.get('roles', []):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('login'))
        
        if user.password != password:
            flash('Incorrect password.', 'error')
            return redirect(url_for('login'))
        
        session['email'] = user.email
        session['user_id'] = user.id
        session['roles'] = [role.name for role in user.roles]

        flash('Login successful!', 'success')
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('user_id', None)
    session.pop('roles', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        
        user_role = Role.query.filter_by(name='user').first()
        user = User(
            email=email,
            password=password,
            roles=[user_role]
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

# Admin Routes
@app.route('/admin/dashboard')
@require_admin
def admin_dashboard():
    parking_lots = ParkingLot.query.all()
    total_lots = len(parking_lots)
    total_spots = sum(lot.maximum_number_of_spots for lot in parking_lots)
    total_available = sum(lot.available_spots_count for lot in parking_lots)
    total_occupied = sum(lot.occupied_spots_count for lot in parking_lots)
    
    users = User.query.join(UserRole).join(Role).filter(Role.name == 'user').all()
    
    return render_template('admin_dashboard.html', 
                         parking_lots=parking_lots,
                         total_lots=total_lots,
                         total_spots=total_spots,
                         total_available=total_available,
                         total_occupied=total_occupied,
                         users=users)

@app.route('/admin/add_parking_lot', methods=['GET', 'POST'])
@require_admin
def add_parking_lot():
    if request.method == 'GET':
        return render_template('add_parking_lot.html')
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        max_spots = request.form.get('max_spots')

        if not all([name, price, address, pin_code, max_spots]):
            flash('All fields are required.', 'error')
            return redirect(url_for('add_parking_lot'))
        
        try:
            price = float(price)
            max_spots = int(max_spots)
        except ValueError:
            flash('Price must be a number and spots must be an integer.', 'error')
            return redirect(url_for('add_parking_lot'))
        
        if max_spots <= 0:
            flash('Number of spots must be greater than 0.', 'error')
            return redirect(url_for('add_parking_lot'))
        
        parking_lot = ParkingLot(
            prime_location_name=name,
            price=price,
            address=address,
            pin_code=pin_code,
            maximum_number_of_spots=max_spots
        )
        db.session.add(parking_lot)
        db.session.commit()
        
        # Create parking spots
        for spot_num in range(1, max_spots + 1):
            spot = ParkingSpot(
                lot_id=parking_lot.id,
                spot_number=spot_num,
                status='A'
            )
            db.session.add(spot)
        
        db.session.commit()
        flash('Parking lot added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_parking_lot/<int:lot_id>', methods=['GET', 'POST'])
@require_admin
def edit_parking_lot(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == 'GET':
        return render_template('edit_parking_lot.html', parking_lot=parking_lot)
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        max_spots = request.form.get('max_spots')

        if not all([name, price, address, pin_code, max_spots]):
            flash('All fields are required.', 'error')
            return redirect(url_for('edit_parking_lot', lot_id=lot_id))
        
        try:
            price = float(price)
            max_spots = int(max_spots)
        except ValueError:
            flash('Price must be a number and spots must be an integer.', 'error')
            return redirect(url_for('edit_parking_lot', lot_id=lot_id))
        
        if max_spots <= 0:
            flash('Number of spots must be greater than 0.', 'error')
            return redirect(url_for('edit_parking_lot', lot_id=lot_id))
        
        current_spots = len(parking_lot.parking_spots)
        
        # Update parking lot details
        parking_lot.prime_location_name = name
        parking_lot.price = price
        parking_lot.address = address
        parking_lot.pin_code = pin_code
        parking_lot.maximum_number_of_spots = max_spots
        
        # Adjust parking spots if needed
        if max_spots > current_spots:
            # Add new spots
            for spot_num in range(current_spots + 1, max_spots + 1):
                spot = ParkingSpot(
                    lot_id=parking_lot.id,
                    spot_number=spot_num,
                    status='A'
                )
                db.session.add(spot)
        elif max_spots < current_spots:
            # Remove excess spots (only if they're available)
            spots_to_remove = ParkingSpot.query.filter_by(
                lot_id=lot_id, 
                status='A'
            ).filter(
                ParkingSpot.spot_number > max_spots
            ).all()
            
            for spot in spots_to_remove:
                db.session.delete(spot)
        
        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_parking_lot/<int:lot_id>')
@require_admin
def delete_parking_lot(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)
    
    # Check if all spots are available
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='O').count()
    if occupied_spots > 0:
        flash('Cannot delete parking lot. Some spots are still occupied.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(parking_lot)
    db.session.commit()
    flash('Parking lot deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/view_parking_lot/<int:lot_id>')
@require_admin
def view_parking_lot(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)
    parking_spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    
    # Get active reservations for this lot
    active_reservations = db.session.query(Reservation, User, ParkingSpot).join(
        User, Reservation.user_id == User.id
    ).join(
        ParkingSpot, Reservation.spot_id == ParkingSpot.id
    ).filter(
        ParkingSpot.lot_id == lot_id,
        Reservation.is_active == True
    ).all()
    
    return render_template('view_parking_lot.html', 
                         parking_lot=parking_lot, 
                         parking_spots=parking_spots,
                         active_reservations=active_reservations,
                         current_time=datetime.utcnow())

# User Routes
@app.route('/user/dashboard')
@require_login
def user_dashboard():
    user_id = session['user_id']
    
    # Get user's active reservations
    active_reservations = db.session.query(Reservation, ParkingSpot, ParkingLot).join(
        ParkingSpot, Reservation.spot_id == ParkingSpot.id
    ).join(
        ParkingLot, ParkingSpot.lot_id == ParkingLot.id
    ).filter(
        Reservation.user_id == user_id,
        Reservation.is_active == True
    ).all()
    
    # Get user's reservation history
    reservation_history = db.session.query(Reservation, ParkingSpot, ParkingLot).join(
        ParkingSpot, Reservation.spot_id == ParkingSpot.id
    ).join(
        ParkingLot, ParkingSpot.lot_id == ParkingLot.id
    ).filter(
        Reservation.user_id == user_id,
        Reservation.is_active == False
    ).order_by(Reservation.parking_timestamp.desc()).limit(10).all()
    
    # Get available parking lots
    parking_lots = ParkingLot.query.all()
    
    return render_template('user_dashboard.html', 
                         active_reservations=active_reservations,
                         reservation_history=reservation_history,
                         parking_lots=parking_lots)

@app.route('/user/book_parking/<int:lot_id>', methods=['GET', 'POST'])
@require_login
def book_parking(lot_id):
    user_id = session['user_id']
    parking_lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == 'GET':
        # Check if user already has an active reservation
        active_reservation = Reservation.query.filter_by(user_id=user_id, is_active=True).first()
        if active_reservation:
            flash('You already have an active parking reservation.', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Check if there are available spots
        if parking_lot.available_spots_count == 0:
            flash('No available spots in this parking lot.', 'error')
            return redirect(url_for('user_dashboard'))
        
        return render_template('book_parking.html', parking_lot=parking_lot)
    
    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number')
        
        if not vehicle_number:
            flash('Vehicle number is required.', 'error')
            return render_template('book_parking.html', parking_lot=parking_lot)
        
        # Check if user already has an active reservation
        active_reservation = Reservation.query.filter_by(user_id=user_id, is_active=True).first()
        if active_reservation:
            flash('You already have an active parking reservation.', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Find first available spot
        available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
        if not available_spot:
            flash('No available spots in this parking lot.', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Create reservation
        reservation = Reservation(
            spot_id=available_spot.id,
            user_id=user_id,
            vehicle_number=vehicle_number.upper(),
            parking_timestamp=datetime.utcnow(),
            is_active=True
        )
        
        # Mark spot as occupied
        available_spot.status = 'O'
        
        db.session.add(reservation)
        db.session.commit()
        
        flash(f'Parking spot {available_spot.spot_number} booked successfully for vehicle {vehicle_number.upper()}!', 'success')
        return redirect(url_for('user_dashboard'))

@app.route('/user/release_parking/<int:reservation_id>')
@require_login
def release_parking(reservation_id):
    user_id = session['user_id']
    
    reservation = Reservation.query.filter_by(
        id=reservation_id, 
        user_id=user_id, 
        is_active=True
    ).first()
    
    if not reservation:
        flash('Reservation not found.', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Calculate cost and update reservation
    reservation.leaving_timestamp = datetime.utcnow()
    reservation.parking_cost = reservation.calculate_cost()
    reservation.is_active = False
    
    # Mark spot as available
    parking_spot = ParkingSpot.query.get(reservation.spot_id)
    parking_spot.status = 'A'
    
    db.session.commit()
    
    flash(f'Parking released successfully! Total cost: ₹{reservation.parking_cost:.2f}', 'success')
    return redirect(url_for('user_dashboard'))

# Chart Data API Routes
@app.route('/api/admin/revenue-chart-data')
@require_admin
def admin_revenue_chart_data():
    # Get revenue data for each parking lot
    revenue_data = db.session.query(
        ParkingLot.prime_location_name,
        db.func.coalesce(db.func.sum(Reservation.parking_cost), 0).label('total_revenue')
    ).outerjoin(
        ParkingSpot, ParkingLot.id == ParkingSpot.lot_id
    ).outerjoin(
        Reservation, db.and_(
            ParkingSpot.id == Reservation.spot_id,
            Reservation.is_active == False,
            Reservation.parking_cost.isnot(None)
        )
    ).group_by(ParkingLot.id, ParkingLot.prime_location_name).all()
    
    labels = [row.prime_location_name for row in revenue_data]
    data = [float(row.total_revenue) for row in revenue_data]
    
    return jsonify({
        'labels': labels,
        'data': data
    })

@app.route('/api/admin/occupancy-chart-data')
@require_admin
def admin_occupancy_chart_data():
    # Get occupancy data for each parking lot
    occupancy_data = []
    parking_lots = ParkingLot.query.all()
    
    for lot in parking_lots:
        occupancy_data.append({
            'name': lot.prime_location_name,
            'occupied': lot.occupied_spots_count,
            'available': lot.available_spots_count
        })
    
    return jsonify(occupancy_data)

@app.route('/api/user/parking-history-chart-data')
@require_login
def user_parking_history_chart_data():
    user_id = session['user_id']
    
    # Get user's parking history by parking lot
    history_data = db.session.query(
        ParkingLot.prime_location_name,
        db.func.count(Reservation.id).label('total_bookings')
    ).join(
        ParkingSpot, ParkingLot.id == ParkingSpot.lot_id
    ).join(
        Reservation, ParkingSpot.id == Reservation.spot_id
    ).filter(
        Reservation.user_id == user_id,
        Reservation.is_active == False
    ).group_by(ParkingLot.id, ParkingLot.prime_location_name).all()
    
    labels = [row.prime_location_name for row in history_data]
    data = [row.total_bookings for row in history_data]
    
    return jsonify({
        'labels': labels,
        'data': data
    })