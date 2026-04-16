#!/usr/bin/python3

from enum import Enum
import reservationapi
import configparser
import os
import time

'''
Rate Limiter for API calls.
To use:
    - Create Object
    - Execute an API request by:
        rate_limiter.run_task(lambda: function(arguments))
'''
class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = float(rate_limit)
        self.last_timestamp = 0
    
    def run_task(self, task):
        elapsed_time = time.time() - self.last_timestamp

        if elapsed_time < self.rate_limit:
            time.sleep(self.rate_limit - elapsed_time)
        
        self.last_timestamp = time.time()
        return task()


class MenuState(Enum):
    HOME = 1
    BOOK_SLOT = 2


class BookingSystem():
    TITLE_WIDTH = 50
    TITLE = "WEDDING BOOKING SYSTEM"

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("api.ini")

        # Create an API object to communicate with the hotel API
        self.hotel  = reservationapi.ReservationApi(config['hotel']['url'],
                                            config['hotel']['key'],
                                            int(config['global']['retries']),
                                            float(config['global']['delay']))

        # Create an API object to communicate with the band API
        self.band   = reservationapi.ReservationApi(config['band']['url'],
                                            config['band']['key'],
                                            int(config['global']['retries']),
                                            float(config['global']['delay']))
        
        # Create an rate limiter to manage API requests
        self.rate_limiter = RateLimiter(rate_limit=1)

        self.state = MenuState.HOME
    
    def _print_title(self, title: str):
        '''
        Function which prints a formatted title of the form: |-----| TITLE |-----|
        '''
        dash_repeat = int((BookingSystem.TITLE_WIDTH - (6 + len(title))) / 2)
        section = "|" + "-" * dash_repeat + "|"
        print(section + " " + title + " " + section)

    def _reset_stdout(self):
        '''
        Function which clears the output of the terminal and prints the menu title at the top
        '''
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * BookingSystem.TITLE_WIDTH)
        self._print_title(BookingSystem.TITLE)
        print("=" * BookingSystem.TITLE_WIDTH)

    def parse_list(self, raw_data: dict) -> list[str]:
        out = []
        for item in raw_data:
            out.append(f"Slot {item.get('id')}")
        return out

    def swap_menu(self, state):
        self.state = state
        # ----------------- TITLE -----------------
        self._reset_stdout()
        print()

    def mainloop(self):
        do_mainloop = True
        self.swap_menu(MenuState.HOME)

        while do_mainloop:

            if self.state == MenuState.HOME:
                # ------------- CURRENT SLOTS -------------
                booked_slots = self.rate_limiter.run_task(lambda: self.parse_list(self.hotel.get_slots_held()))
                # if we have slots booked, then we print them
                if len(booked_slots) > 0:
                    self._print_title("CURRENTLY HELD SLOTS")
                    for slot in booked_slots:
                        print(slot)
                    print()

                # --------------- OPERATIONS --------------
                self._print_title(" OPERATIONS ")
                print("1. View the currently held slots for the hotel")
                print("2. View the currently held slots for the band")
                print("3. Book a slot")
                print("4. Cancel a booking")
                print("5. View the first 5 matching slots")
                print("6. Reserve the earliest slot")
                print("7. Cancel a reservation")
                print("8. Quit\n")

                option = None
                while option == None:
                    try:
                        option = int(input("Enter operation number: "))
                    except:
                        print("Invalid operation selected.")
                
                match option:
                    case 1:
                        self.rate_limiter.run_task(lambda: self.hotel.get_slots_held())
                    case 2:
                        self.rate_limiter.run_task(lambda: self.band.get_slots_held())
                    case 3:
                        self.swap_menu(MenuState.BOOK_SLOT)
                    case 4:
                        pass
                    case 5:
                        pass
                    case 6:
                        pass
                    case 7:
                        pass
                    case 8:
                        do_mainloop = False

            elif self.state == MenuState.BOOK_SLOT:
                self._print_title("Book a Slot")
                



if __name__ == "__main__":
    booking_system = BookingSystem()

    booking_system.mainloop()