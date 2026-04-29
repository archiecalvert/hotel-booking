""" Reservation API wrapper

This class implements a simple wrapper around the reservation API. It
provides automatic retries for server-side errors, delays to prevent
server overloading, and produces sensible exceptions for the different
types of client-side error that can be encountered.
"""

# This file contains areas that need to be filled in with your own
# implementation code. They are marked with "Your code goes here".
# Comments are included to provide hints about what you should do.

import requests
import simplejson
import warnings
import time

from requests.exceptions import HTTPError
from exceptions import (
    BadRequestError, InvalidTokenError, BadSlotError, NotProcessedError,
    SlotUnavailableError,ReservationLimitError)

class RateLimiter:
    '''
    Rate Limiter for API calls.
    To use:
        <br>- Create Object
        <br>- Execute an API request by:
            rate_limiter.run_task(lambda: function(arguments))
          <br>or use one of the provided wrapper methods
    '''
    def __init__(self, rate_limit: float, name: str):
        self.rate_limit = float(rate_limit)
        self.last_timestamp = 0
        self.name = name

    
    def run_task(self, task):
        elapsed_time = time.time() - self.last_timestamp

        if elapsed_time < self.rate_limit:
            print(f"\033[35mRATE LIMIT ({self.name})\033[0m: Rate limit on the API has been reached! API call will resume in {self.rate_limit - elapsed_time:0.1f} second(s)")
            time.sleep(self.rate_limit - elapsed_time)
        
        self.last_timestamp = time.time()
        return task()

class Cache:
    def __init__(self, expire_time_s):
        self.expire_time = expire_time_s
        self.last_access = 0
        self.data = []

    def dirty(self) -> bool:
        ''' Function which returns whether the cache is expired. '''
        elapsed_time = time.time() - self.last_access
        return elapsed_time > self.expire_time
    
    def update(self, data):
        ''' Function which is used to set the data in the cache. (Entirely) '''
        self.data = data
        self.last_access = time.time()

    def append(self, item):
        ''' Function which adds an item to the data cache. '''
        self.data.append(item)

    def remove(self, item):
        ''' Function which removes an item from the cache. If not present, nothing will happen. '''
        if item in self.data:
            self.data.remove(item)
    
    def make_dirty(self):
        ''' Function which can manually set the cache to be exipred. '''
        self.last_access = 0


class ReservationApi:
    def __init__(self, name, base_url: str, token: str, retries: int, delay: float, max_bookings_count: int = 2):
        """ Create a new ReservationApi to communicate with a reservation
        server.

        Args:
            base_url: The URL of the reservation API to communicate with.
            token: The user's API token obtained from the control panel.
            retries: The maximum number of attempts to make for each request.
            delay: A delay to apply to each request to prevent server overload.
        """
        self.name                   = name
        self.base_url               = base_url
        self.token                  = token
        self.retries                = retries
        self.delay                  = delay
        self.rate_limiter           = RateLimiter(1, name)
        self.booking_cache          = Cache(60)
        self.available_slot_cache   = Cache(60)
        self.max_bookings_count     = max_bookings_count

    def _reason(self, req: requests.Response) -> str:
        """Obtain the reason associated with a response"""
        reason = ''

        # Try to get the JSON content, if possible, as that may contain a
        # more useful message than the status line reason
        try:
            json = req.json()
            reason = json['message']

        # A problem occurred while parsing the body - possibly no message
        # in the body (which can happen if the API really does 500,
        # rather than generating a "fake" 500), so fall back on the HTTP
        # status line reason
        except simplejson.errors.JSONDecodeError:
            if isinstance(req.reason, bytes):
                try:
                    reason = req.reason.decode('utf-8')
                except UnicodeDecodeError:
                    reason = req.reason.decode('iso-8859-1')
            else:
                reason = req.reason

        return reason


    def _headers(self) -> dict:
        """Create the authorization token header needed for API requests"""
        # Your code goes here
        return {
            "Authorization": f"Bearer {self.token}"
        }

    def _send_request(self, method: str, endpoint: str) -> dict:
        """Send a request to the reservation API and convert errors to
           appropriate exceptions"""
        # Your code goes here

        headers = self._headers()
        
        # Allow for multiple retries if needed
        for i in range(self.retries):
            # exponential backoff delay
            iteration_delay = float(self.delay) * 2 ** i

            # Perform the request.
            match method:
                case "GET":
                    response = requests.get(endpoint, headers=headers)

                case "POST":
                    response = requests.post(endpoint, headers=headers)

                case "DELETE":
                    response = requests.delete(endpoint, headers=headers)

                case _:
                    print("EVIL IMPLEMENT THIS LATER")
            
            # Delay before processing the response to avoid swamping server.
            # time.sleep(iteration_delay) # uses exponential backoff

            # 200 response indicates all is well - send back the json data.
            if response.status_code == 200:
                return response.json()

            # 5xx responses indicate a server-side error, show a warning
            # (including the try number).
            elif str(response.status_code)[0] == "5":
                print(f"\033[33mWARNING ({self.name})\033[0m: A server-side error occured when trying to access the API (Error Code {response.status_code}). Performing retry {i+1}/{self.retries} in {iteration_delay} seconds")
                time.sleep(iteration_delay) # uses exponential backoff
                continue

            # 400 errors are client problems that are meaningful, so convert
            # them to separate exceptions that can be caught and handled by
            # the caller.
            elif response.status_code == 400:
                raise BadRequestError()

            elif response.status_code == 401:
                raise InvalidTokenError()
            
            elif response.status_code == 403:
                raise BadSlotError()
            
            elif response.status_code == 404:
                raise NotProcessedError()
            
            elif response.status_code == 409:
                # can happen if the caches becomes out of sync.
                # to avoid this, manually expire the cache
                self.booking_cache.make_dirty()
                self.available_slot_cache.make_dirty()
                raise SlotUnavailableError()
            
            elif response.status_code == 451:
                raise ReservationLimitError()

            
            # Anything else is unexpected and may need to kill the client.
            else:
                print("Critical error when calling API! Killing client")
                print(f"Endpoint: {endpoint}")
                print(f"Method: {method}")
                print(f"Reason: {self._reason(response)}")
                exit()

        # Get here and retries have been exhausted, throw an appropriate
        # exception.
        raise Exception("Max number of retries have been attempted.")

    def get_slots_available(self, bypass_cache:bool = False):
        """Obtain the list of slots currently available in the system"""
        # Your code goes here
        if not bypass_cache and not self.available_slot_cache.dirty():
            print(f"\033[96mCACHE ({self.name})\033[0m: Using cached available bookings")
            return self.available_slot_cache.data
        else:
            print(f"\033[96mCACHE ({self.name})\033[0m: Refreshing cached available bookings. Cache will expire in {self.available_slot_cache.expire_time} seconds")
            self.available_slot_cache.update(self.rate_limiter.run_task(lambda: self._send_request("GET", f"{self.base_url}/reservation/available")))
            return self.available_slot_cache.data

    def get_slots_held(self, bypass_cache:bool = False):
        """Obtain the list of slots currently held by the client"""
        # Your code goes here
        if not bypass_cache and not self.booking_cache.dirty():
            print(f"\033[96mCACHE ({self.name})\033[0m: Using cached held bookings")
            return self.booking_cache.data
        else:
            print(f"\033[96mCACHE ({self.name})\033[0m: Refreshing cached held bookings. Cache will expire in {self.booking_cache.expire_time} seconds")
            self.booking_cache.update(self.rate_limiter.run_task(lambda: self._send_request("GET", f"{self.base_url}/reservation")))
            return self.booking_cache.data

    def release_slot(self, slot_id):
        """Release a slot currently held by the client"""
        # Your code goes here
        res = self.rate_limiter.run_task(lambda: self._send_request("DELETE", f"{self.base_url}/reservation/{slot_id}"))
        self.booking_cache.remove({"id": str(slot_id)})
        self.available_slot_cache.append({"id": str(slot_id)})
        return res


    def reserve_slot(self, slot_id):
        """Attempt to reserve a slot for the client"""
        # Your code goes here
        res = self.rate_limiter.run_task(lambda: self._send_request("POST", f"{self.base_url}/reservation/{slot_id}"))
        self.booking_cache.append({"id": str(slot_id)})
        self.available_slot_cache.remove({"id": str(slot_id)})
        return res

