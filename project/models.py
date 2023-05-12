from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
import datetime


# Create your models here.

class Location(models.Model):
    airport = models.CharField(max_length= 30)

class Plane(models.Model):
    numberOfEconomy = models.IntegerField(default = 0, validators=[MinValueValidator(0)])
    numberOfBusiness = models.IntegerField(default = 0, validators=[MinValueValidator(0)])
    numberOfFirstClass = models.IntegerField(default = 0, validators=[MinValueValidator(0)])

class Price(models.Model):
    EconomyPrice = models.DecimalField(max_digits= 7, decimal_places=2)
    BusinessPrice = models.DecimalField(max_digits= 7, decimal_places=2)
    FirstClassPrice = models.DecimalField(max_digits= 7, decimal_places=2)
    currency = models.CharField(max_length= 3)
    
class Passenger(models.Model):
    email = models.CharField(max_length= 60)

class Flight(models.Model):
    planeID = models.ForeignKey(Plane, on_delete=models.CASCADE)
    priceID = models.ForeignKey(Price, on_delete=models.CASCADE, null = True)
    startLocation = models.ForeignKey(Location, on_delete=models.CASCADE, related_name = "start_location")
    endLocation = models.ForeignKey(Location, on_delete=models.CASCADE, related_name = "end_location")
    numberPassengers = models.IntegerField(default = 0, validators=[MinValueValidator(0)])
    totalAvailable = models.IntegerField(default = 0, validators=[MinValueValidator(0)])
    numberAvailableEconomy = models.IntegerField(default = 0, validators=[MinValueValidator(0)])
    numberAvailableBuisness = models.IntegerField(default = 0, validators=[MinValueValidator(0)])
    numberAvailableFirtsClass = models.IntegerField(default = 0, validators=[MinValueValidator(0)])
    departureDate = models.DateField(default=timezone.now().date())
    arrivalDate = models.DateField(default=timezone.now().date())
    departureTime = models.TimeField(default=timezone.now().time())
    arrivalTime = models.TimeField(default=timezone.now().time())
    flightDuration = models.TimeField(default=datetime.time(hour=0, minute=0))
    airline = models.CharField(max_length= 30)

class Reservation(models.Model):
    flightID = models.ForeignKey(Flight, on_delete=models.CASCADE)
    passengerID = models.ForeignKey(Passenger, on_delete=models.CASCADE)
    numberOfEconomy = models.IntegerField(default = 0, validators=[MinValueValidator(0)])
    numberOfBusiness = models.IntegerField(default = 0,validators=[MinValueValidator(0)])
    numberOfFirstClass = models.IntegerField(default = 0, validators=[MinValueValidator(0)])
    timeStarted = models.DateTimeField()
    confirmedStatus = models.BooleanField(default=False)
