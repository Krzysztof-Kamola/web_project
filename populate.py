import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AirlineAPI.settings')
from datetime import date
from faker import Faker
from project.models import Location, Passenger, Reservation, Price, Plane, Flight
import random


current_date = date.today()  # Get the current date

fake = Faker()

Passenger.objects.all().delete()
Flight.objects.all().delete()
Reservation.objects.all().delete()
Price.objects.all().delete()
Plane.objects.all().delete()
Location.objects.all().delete()

# Define a list of cities and airport codes
cities = [ ('New York', 'JFK'), ('Los Angeles', 'LAX'), ('London', 'LHR'), ('Paris', 'CDG'), ('Dubai', 'DXB'), ('Abu Dhabi', 'AUH'), ('Hong Kong', 'HKG'), ('Tokyo', 'HND'), ('Toronto', 'YYZ'), ('Dehli', 'DEL')]

# Create locations
locations = []
for city, airport in cities:
    location = Location.objects.create(airport=city)
    locations.append(location)

# # Create passengers
# passengers = []
# for i in range(50):
#     passenger = Passenger.objects.create(email=fake.email())
#     passengers.append(passenger)

# Create prices
prices = []
for i in range(10):
    price = Price.objects.create(
        EconomyPrice=random.uniform(100, 500),
        BusinessPrice=random.uniform(500, 1000),
        FirstClassPrice=random.uniform(1000, 2000),
        currency='GBP'
    )
    prices.append(price)

# Create planes
planes = []
for i in range(10):
    plane = Plane.objects.create(
        numberOfEconomy=random.randint(100, 200),
        numberOfBusiness=random.randint(20, 40),
        numberOfFirstClass=random.randint(10, 20)
    )
    planes.append(plane)

flights = []
for i in range(50):
    departure_location = random.choice(locations)
    arrival_location = random.choice(locations)
    while departure_location == arrival_location:
        arrival_location = random.choice(locations)
    fake_date = fake.future_date(end_date='+1y', tzinfo=None)  # Generate a random date after the current date
    planeID = random.choice(planes)
    flight = Flight.objects.create(
        planeID=planeID,
        priceID=random.choice(prices),
        startLocation=departure_location,
        endLocation=arrival_location,
        numberPassengers = 0,
        totalAvailable=planeID.numberOfEconomy + planeID.numberOfBusiness + planeID.numberOfFirstClass,
        numberAvailableEconomy=planeID.numberOfEconomy,
        numberAvailableBuisness=planeID.numberOfBusiness,
        numberAvailableFirtsClass=planeID.numberOfFirstClass,
        departureDate=fake_date,
        arrivalDate=fake_date,
        departureTime=fake.time(),
        arrivalTime=fake.time(),
        flightDuration=fake.time(),
        airline="FlyLo"
    )
    flights.append(flight)

# # Create reservations
# reservations = []
# for i in range(100):
#     passenger = random.choice(passengers)
#     flight = random.choice(flights)
#     #num_seats = random.randint(1, flight.numberAvailableSeats)

#     reservation = Reservation.objects.create(
#         flightID=flight,
#         passengerID=passenger,
#         numberOfEconomy=random.randint(1, flight.numberAvailableEconomy),
#         numberOfBusiness=random.randint(1, flight.numberAvailableBuisness),
#         numberOfFirstClass=random.randint(1, flight.numberAvailableFirtsClass),
#         timeStarted=fake.date_time(),
#         confirmedStatus=random.choice([True, False])
#     )
#     reservations.append(reservation)