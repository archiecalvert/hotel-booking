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
    def __init__(self, rate_limit):
        self.rate_limit = float(rate_limit)
        self.last_timestamp = 0

    
    def run_task(self, task):
        elapsed_time = time.time() - self.last_timestamp

        if elapsed_time < self.rate_limit:
            time.sleep(self.rate_limit - elapsed_time)
        
        self.last_timestamp = time.time()
        return task()


class ReservationApi:
    def __init__(self, base_url: str, token: str, retries: int, delay: float, max_bookings_count: int = 2):
        """ Create a new ReservationApi to communicate with a reservation
        server.

        Args:
            base_url: The URL of the reservation API to communicate with.
            token: The user's API token obtained from the control panel.
            retries: The maximum number of attempts to make for each request.
            delay: A delay to apply to each request to prevent server overload.
        """
        self.base_url       = base_url
        self.token          = token
        self.retries        = retries
        self.delay          = delay
        self.rate_limiter   = RateLimiter(1)
        self.dirty_cache    = True # if this is ever true, then the data in the cache needs refreshing
        self.booking_cache  = []
        self.max_bookings_count = max_bookings_count

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
                print(f"\033[33mWARNING\033[0m: A server-side error occured when trying to access the API (Error Code {response.status_code}). Performing retry {i+1}/{self.retries} in {iteration_delay} seconds")
                time.sleep(iteration_delay) # uses exponential backoff
                continue

            # 400 errors are client problems that are meaningful, so convert
            # them to separate exceptions that can be caught and handled by
            # the caller.
            elif response.status_code == 401:
                raise InvalidTokenError()
            
            elif response.status_code == 403:
                raise BadSlotError()
            
            elif response.status_code == 404:
                raise NotProcessedError()
            
            elif response.status_code == 409:
                raise SlotUnavailableError()
            
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

    def get_slots_available(self):
        """Obtain the list of slots currently available in the system"""
        # Your code goes here
        return self.rate_limiter.run_task(lambda: self._send_request("GET", f"{self.base_url}/reservation/available"))

    def get_slots_held(self):
        """Obtain the list of slots currently held by the client"""
        # Your code goes here
        if not self.dirty_cache:
            return self.booking_cache
        else:
            self.booking_cache = self.rate_limiter.run_task(lambda: self._send_request("GET", f"{self.base_url}/reservation"))
            self.dirty_cache = False
            return self.booking_cache


    def release_slot(self, slot_id):
        """Release a slot currently held by the client"""
        # Your code goes here
        res = self.rate_limiter.run_task(lambda: self._send_request("DELETE", f"{self.base_url}/reservation/{slot_id}"))
        self.booking_cache.remove({"id": str(slot_id)})
        return res


    def reserve_slot(self, slot_id):
        """Attempt to reserve a slot for the client"""
        # Your code goes here
        res = self.rate_limiter.run_task(lambda: self._send_request("POST", f"{self.base_url}/reservation/{slot_id}"))
        self.booking_cache.append({"id": str(slot_id)})
        return res

