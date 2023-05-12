from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Flight, Price, Reservation, Location, Passenger
import json
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def home(request):
    return HttpResponse("<h1> Homepage </h1>")

def list_flights(request):
    cancel_old_reservations()
    if(request.method == 'GET'):
        # {‘dateOfDeparture’, 'cityOfDeparture', ‘arrivalCity’, ‘numberOftickets' }
        data = json.loads(request.body)
        departureDateString = data.get('dateOfDeparture')
        departureCity = data.get('cityOfDeparture')
        arrivalCity = data.get('cityOfArrival')
        totalNumTickets = data.get('totalNoOfTickets')

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
                return JsonResponse({"status": "fail"})

            listOfFlights = {}
            for flight in flights:
                flightDict = {  
                                "cityOfDeparture" : flight.startLocation.airport,
                                "cityOfArrival" : flight.endLocation.airport,
                                "dateOfDeparture" : flight.departureDate,
                                "timeOfDeparture" : flight.departureTime,
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


@csrf_exempt
def make_reservation(request):
    cancel_old_reservations()
    #  {"flight ID", "seats": {econ, business, first class}, "email"}
    data = json.loads(request.body)
    flightID = data.get('flightID')
    flightID = flightID[2:]
    numberOfSeats = data.get('seats')
    email = data.get('email')
    economySeats = numberOfSeats.get('noOfEconomy')
    businessSeats = numberOfSeats.get('noOfBusiness')
    firstClassSeats = numberOfSeats.get('noOfFirstClass')

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

@csrf_exempt
def cancel_reservation(request):  
    try:
        #  {"bookingID"}
        cancel_old_reservations()
        data = json.loads(request.body)
        reservationID = data.get('bookingID')
        reservationID = reservationID[2:]
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
    
    except:
        return JsonResponse({"status": "fail"})

@csrf_exempt   
def confirm_booking(request):
    cancel_old_reservations()
    try:
        #  {"bookingID", "amount"}
        data = json.loads(request.body) 
        reservationID = data.get('bookingID')
        reservationID = int(reservationID[2:])
        amount = float(data.get('amount'))
        reservation = Reservation.objects.get(pk = reservationID)
        flight = reservation.flightID
        prices = flight.priceID
        checkAmount = 0.0
        checkAmount = float((reservation.numberOfEconomy * prices.EconomyPrice) + (reservation.numberOfBusiness * prices.BusinessPrice) + (reservation.numberOfFirstClass * prices.FirstClassPrice))
        print(checkAmount)
        print(amount)
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
    old_reservations = Reservation.objects.filter(timeStarted__lte = change_in_time,confirmedStatus = False)
    for reservation in old_reservations:
        flight = reservation.flightID
        flight.totalAvailable += (reservation.numberOfEconomy + reservation.numberOfBusiness + reservation.numberOfFirstClass)
        flight.numberAvailableEconomy += reservation.numberOfEconomy
        flight.numberAvailableBuisness += reservation.numberOfBusiness
        flight.numberAvailableFirtsClass += reservation.numberOfFirstClass
        flight.numberPassengers -= (reservation.numberOfEconomy + reservation.numberOfBusiness + reservation.numberOfFirstClass) 
        flight.save()

        reservation.delete()