from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime
from .models import Flight, Price, Reservation, Location, Passenger
import json
from django.core.exceptions import ObjectDoesNotExist

# Create your views here.
def index(request):
    return HttpResponse("<h1> Homepage </h1>")

def list_flights(request):
    if(request.method == 'GET'):
        data = json.loads(request.body) # {‘departureDate’, 'departureCity', ‘arrivalCity’, ‘tickets' }
        departureDateString = data[list(data.keys())[0]] # String
        departureCity = data[list(data.keys())[1]] # String
        arrivalCity = data[list(data.keys())[2]] # String
        totalNumTickets = data[list(data.keys())[3]] # Int

        try:

            departureDate = datetime.strptime(departureDateString, '%Y-%m-%d') if departureDateString else None
            departureCityID = Location.objects.get(airport = departureCity) if departureCity else None
            arrivalCityID = Location.objects.get(airport = arrivalCity) if arrivalCity else None

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
                                'departureDate' : flight.departureDate,
                                'departureCity' : flight.startLocation.airport,
                                'arrivalCity' : flight.endLocation.airport,
                                'departureTime' : flight.departureTime,
                                'arrivalTime' : flight.arrivalTime,
                                'seats': {
                                    'noOfEconomy': flight.planeID.numberOfEconomy,
                                    'noOfBusiness': flight.planeID.numberOfBusiness,
                                    'noOfFirstClass': flight.planeID.numberOfFirstClass,
                                },
                                'price' : {
                                        'priceOfEconomy': flight.priceID.EconomyPrice,
                                        'priceOfBusiness': flight.priceID.BusinessPrice,
                                        'priceOfFirstClass': flight.priceID.FirstClassPrice
                                }
                            }
                
                flightID = '02' + str(flight.pk)
                listOfFlights[flightID] = flightDict
                
            return JsonResponse(listOfFlights)
        
        except ObjectDoesNotExist:
            return JsonResponse({'status': 'fail'})

    

def start_reservation_process(request):
    data = json.loads(request.body) #  {‘Flight ID’, 'noOfSeats {econ, business, first class}, 'email'}
    flightID = data[list(data.keys())[0]]
    numberOfSeats = data[list(data.keys())[1]]
    email = data[list(data.keys())[2]]
    economySeats = numberOfSeats[list(numberOfSeats.keys())[0]]
    businessSeats = numberOfSeats[list(numberOfSeats.keys())[1]]
    firstClassSeats = numberOfSeats[list(numberOfSeats.keys())[2]]

    try:
        # Add reservation to the table
        passenger, created = Passenger.objects.get_or_create(email = email)
        if not created:
            passenger.save()
        flight = Flight.objects.get(pk = flightID)
        if flight.numberAvailableEconomy < economySeats or flight.numberAvailableBuisness < businessSeats or flight.numberAvailableFirtsClass < firstClassSeats:
            return JsonResponse({'status': 'fail'})
        
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

        return JsonResponse({'reservationID': reservation.pk})
    
    except ObjectDoesNotExist:
        return JsonResponse({'status': 'fail'})

def cancel_reservation(request):  
    try:
        data = json.loads(request.body)  #  {'ReservationID'}
        reservationID = data[list(data.keys())[0]]
        reservation = Reservation.objects.get(pk = reservationID)

        flight = reservation.flightID
        flight.totalAvailable += (reservation.numberOfEconomy + reservation.numberOfBusiness + reservation.numberOfFirstClass)
        flight.numberAvailableEconomy += reservation.numberOfEconomy
        flight.numberAvailableBuisness += reservation.numberOfBusiness
        flight.numberAvailableFirtsClass += reservation.numberOfFirstClass
        flight.numberPassengers -= (reservation.numberOfEconomy + reservation.numberOfBusiness + reservation.numberOfFirstClass) 
        flight.save()

        reservation.delete()
        return JsonResponse({'status': 'success'})
    
    except Reservation.DoesNotExist:
        return JsonResponse({'status': 'fail'})
    
def confirm_booking(request):
    try:
        data = json.loads(request.body)  #  {'ReservationID'}
        reservationID = data[list(data.keys())[0]]
        reservation = Reservation.objects.get(pk = reservationID)
        reservation.confirmedStatus = True
        reservation.save()
        return JsonResponse({'status': 'success'})
    
    except Reservation.DoesNotExist:
        return JsonResponse({'status': 'fail'})
    
# def cancel_booking(request):
#     data = json.loads(request.body)  #  {'ReservationID'}
#     reservationID = data[list(data.keys())[0]]
    
#     try:
#         reservation = Reservation.objects.get(pk = reservationID)
#         reservation.delete()
#         return JsonResponse({'status': True})
    
#     except reservation.DoesNotExist:
#         return JsonResponse({'status': False})

