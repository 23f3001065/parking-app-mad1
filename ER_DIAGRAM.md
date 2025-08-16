# ER Diagram - Vehicle Parking Management System

## Database Schema Visual Representation

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│      User       │      │    UserRole     │      │      Role       │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│ id (PK)         │◄────►│ id (PK)         │◄────►│ id (PK)         │
│ email           │      │ user_id (FK)    │      │ name            │
│ password        │      │ role_id (FK)    │      └─────────────────┘
│ created_at      │      └─────────────────┘              │
└─────────────────┘                                       │
        │                                                 │
        │ 1:M                                             │
        ▼                                                 │
┌─────────────────┐                                       │
│   Reservation   │                                       │
├─────────────────┤                                       │
│ id (PK)         │                                       │
│ spot_id (FK)    │                                       │
│ user_id (FK)    │                                       │
│ vehicle_number  │                                       │
│ parking_timestamp│                                      │
│ leaving_timestamp│                                      │
│ parking_cost    │                                       │
│ is_active       │                                       │
└─────────────────┘                                       │
        ▲                                                 │
        │ M:1                                             │
        │                                                 │
┌─────────────────┐                                       │
│  ParkingSpot    │                                       │
├─────────────────┤                                       │
│ id (PK)         │                                       │
│ lot_id (FK)     │                                       │
│ spot_number     │                                       │
│ status          │                                       │
└─────────────────┘                                       │
        ▲                                                 │
        │ M:1                                             │
        │                                                 │
┌─────────────────┐                                       │
│   ParkingLot    │                                       │
├─────────────────┤                                       │
│ id (PK)         │                                       │
│ prime_location_name                                      │
│ price           │                                       │
│ address         │                                       │
│ pin_code        │                                       │
│ maximum_number_of_spots                                  │
│ created_at      │                                       │
└─────────────────┘                                       │
```

## Relationship Details

### 1. User ↔ Role (Many-to-Many)
- **Connection**: Through UserRole junction table
- **Business Logic**: Users can have multiple roles (e.g., admin, user)
- **Implementation**: Flask-SQLAlchemy relationship with secondary table

### 2. User → Reservation (One-to-Many)
- **Connection**: user_id foreign key in Reservation table
- **Business Logic**: One user can make multiple reservations over time
- **Constraints**: Only one active reservation per user at a time

### 3. ParkingLot → ParkingSpot (One-to-Many)
- **Connection**: lot_id foreign key in ParkingSpot table
- **Business Logic**: Each parking lot contains multiple numbered spots
- **Cascade**: DELETE CASCADE - removing lot removes all its spots

### 4. ParkingSpot → Reservation (One-to-Many)
- **Connection**: spot_id foreign key in Reservation table
- **Business Logic**: Each spot can have multiple reservations over time
- **Constraints**: Only one active reservation per spot at a time

## Data Integrity Rules

### Constraints:
1. **Unique Email**: Each user must have a unique email address
2. **Unique Role Names**: Role names must be unique
3. **Spot Numbering**: Spot numbers are unique within each parking lot
4. **Active Reservations**: Only one active reservation per user and per spot
5. **Non-negative Pricing**: Parking lot prices must be positive values

### Indexes (Implicit):
- Primary keys on all id fields
- Unique index on User.email
- Unique index on Role.name
- Foreign key indexes for optimal join performance

## Business Rules Implementation

### Cost Calculation:
```python
def calculate_cost(self):
    if self.leaving_timestamp and self.parking_timestamp:
        duration = self.leaving_timestamp - self.parking_timestamp
        hours = duration.total_seconds() / 3600
        hours = math.ceil(hours)  # Round up to nearest hour
        return hours * self.parking_spot.parking_lot.price
    return 0
```

### Dynamic Properties:
- `available_spots_count`: Real-time count of available spots
- `occupied_spots_count`: Real-time count of occupied spots

### Status Management:
- Spot Status: 'A' (Available) / 'O' (Occupied)
- Reservation Status: is_active (Boolean)
