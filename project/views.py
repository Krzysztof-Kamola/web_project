from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Flight, Price, Reservation, Location, Passenger
import json
from django.core.exceptions import ObjectDoesNotExist

# Create your views here.
def home(request):
    return HttpResponse("<h1> Homepage </h1>")

def list_flights(request):
    cancel_old_reservations()
    if(request.method == 'GET'):
        data = json.loads(request.body) # {‘dateOfDeparture’, 'cityOfDeparture', ‘arrivalCity’, ‘numberOftickets' }
        departureDateString = data[list(data.keys())[0]] 
        departureCity = data[list(data.keys())[1]] 
        arrivalCity = data[list(data.keys())[2]]
        totalNumTickets = data[list(data.keys())[3]]

        try:

            departureDate = datetime.strptime(departureDateString, '%Y-%m-%d') if departureDateString else None
            departureCityID = Location.objects.get(airport__iexact = departureCity) if departureCity else None
            arrivalCityID = Location.objects.get(airport__iexact = arrivalCity) if arrivalCity else None

            flights = Flight.objects.all()
            if departureCityID:
                flights = flights.filter(startLocation=departureCityID)
            if arrivalCityID:
                flights = flights.filter(endLocation=arrivalCityID)
            if totalNumTickets:
                flights = flights.filter(totalAvailable__gte=totalNumTickets)
            if departureDate:
                flights = flights.filter(departureDate__gte=departureDate)

            if not flights.exists():
                return JsonResponse({"message": "No flights found"},safe=False)

            listOfFlights = {}
            for flight in flights:
                flightDict = {  
                                "cityOfDeparture" : flight.startLocation.airport,
                                "cityOfArrival" : flight.endLocation.airport,
                                "dateOfDeparture" : flight.departureDate,
                                "timeOfDeparture" : flight.departureTime,
                                "timeOfArrival" : flight.arrivalTime,
                                "seats": {
                                    "noOfEconomy": flight.planeID.numberOfEconomy,
                                    "noOfBusiness": flight.planeID.numberOfBusiness,
                                    "noOfFirstClass": flight.planeID.numberOfFirstClass,
                                },
                                "price" : {
                                        "priceOfEconomy": flight.priceID.EconomyPrice,
                                        "priceOfBusiness": flight.priceID.BusinessPrice,
                                        "priceOfFirstClass": flight.priceID.FirstClassPrice
                                }
                            }
                
                flightID = '02' + str(flight.pk)
                listOfFlights[flightID] = flightDict
                
            return JsonResponse(listOfFlights)
        
        except ObjectDoesNotExist:
            return JsonResponse({"status": "fail"})

    

def make_reservation(request):
    cancel_old_reservations()
    data = json.loads(request.body) #  {‘flight ID’, 'seats: {econ, business, first class}, 'email'}
    flightID = data[list(data.keys())[0]]
    flightID = int(flightID[2:])

    numberOfSeats = data[list(data.keys())[1]]
    email = data[list(data.keys())[2]]
    economySeats = numberOfSeats[list(numberOfSeats.keys())[0]]
    businessSeats = numberOfSeats[list(numberOfSeats.keys())[1]]
    firstClassSeats = numberOfSeats[list(numberOfSeats.keys())[2]]

    try:
        passenger, created = Passenger.objects.get_or_create(email = email)
        if not created:
            passenger.save()
        flight = Flight.objects.get(pk = flightID)
        if flight.numberAvailableEconomy < economySeats or flight.numberAvailableBuisness < businessSeats or flight.numberAvailableFirtsClass < firstClassSeats:
            return JsonResponse({"status": "fail"})
        
        reservation = Reservation(
            flightID= flight,
            passengerID = passenger,
            numberOfEconomy = economySeats,
            numberOfBusiness = businessSeats,
            numberOfFirstClass= firstClassSeats,
            timeStarted = timezone.now(),
            confirmedStatus = False
        )
        reservation.save()

        flight.totalAvailable -= (economySeats + businessSeats + firstClassSeats)
        flight.numberAvailableEconomy -= economySeats
        flight.numberAvailableBuisness -= businessSeats
        flight.numberAvailableFirtsClass -= firstClassSeats
        flight.numberPassengers += (economySeats + businessSeats + firstClassSeats)
        flight.save()

        message ='02' + str(reservation.pk)
        return JsonResponse({"bookingID": message})
    
    except ObjectDoesNotExist:
        return JsonResponse({"status": "fail"})

def cancel_reservation(request):  
    cancel_old_reservations()
    try:
        data = json.loads(request.body)  #  {'bookingID'}
        reservationID = data[list(data.keys())[0]]
        reservationID = int(reservationID[2:])
        reservation = Reservation.objects.get(pk = reservationID)

        flight = reservation.flightID
        flight.totalAvailable += (reservation.numberOfEconomy + reservation.numberOfBusiness + reservation.numberOfFirstClass)
        flight.numberAvailableEconomy += reservation.numberOfEconomy
        flight.numberAvailableBuisness += reservation.numberOfBusiness
        flight.numberAvailableFirtsClass += reservation.numberOfFirstClass
        flight.numberPassengers -= (reservation.numberOfEconomy + reservation.numberOfBusiness + reservation.numberOfFirstClass) 
        flight.save()

        reservation.delete()
        return JsonResponse({"status": "success"})
    
    except Reservation.DoesNotExist:
        return JsonResponse({"status": "fail"})
    
def confirm_booking(request):
    cancel_old_reservations()
    try:
        data = json.loads(request.body)  #  {'bookingID', 'amount'}
        reservationID = data[list(data.keys())[0]]
        reservationID = int(reservationID[2:])
        amount = float(data[list(data.keys())[1]])
        reservation = Reservation.objects.get(pk = reservationID)
        flight = reservation.flightID
        prices = flight.priceID
        checkAmount = 0.0
        checkAmount = float((reservation.numberOfEconomy * prices.EconomyPrice) + (reservation.numberOfBusiness * prices.BusinessPrice) + (reservation.numberOfFirstClass * prices.FirstClassPrice))
        print(checkAmount == amount)
        if checkAmount == amount:
            reservation.confirmedStatus = True
            reservation.save()
            return JsonResponse({"status": "success","sent": amount,"check": checkAmount})
        else:
            return JsonResponse({"status": "fail","sent": amount,"check": checkAmount})
    
    except Reservation.DoesNotExist:
        return JsonResponse({"status": "fail"})
    

def cancel_old_reservations():
    current_time = timezone.now()
    change_in_time = current_time - timedelta(minutes=15)
    old_reservations = Reservation.objects.filter(timeStarted__lte = change_in_time)
    old_reservations = Reservation.objects.filter(confirmedStatus = False)
    for reservation in old_reservations:
        flight = reservation.flightID
        flight.totalAvailable += (reservation.numberOfEconomy + reservation.numberOfBusiness + reservation.numberOfFirstClass)
        flight.numberAvailableEconomy += reservation.numberOfEconomy
        flight.numberAvailableBuisness += reservation.numberOfBusiness
        flight.numberAvailableFirtsClass += reservation.numberOfFirstClass
        flight.numberPassengers -= (reservation.numberOfEconomy + reservation.numberOfBusiness + reservation.numberOfFirstClass) 
        flight.save()

        reservation.delete()