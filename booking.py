#!/usr/bin/python3

from enum import Enum
import reservationapi
import configparser
import os
import time
from exceptions import (
    BadRequestError, InvalidTokenError, BadSlotError, NotProcessedError,
    SlotUnavailableError,ReservationLimitError)

class RateLimiter:
    '''
    Rate Limiter for API calls.
    To use:
        - Create Object
        - Execute an API request by:
            rate_limiter.run_task(lambda: function(arguments))
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


class MenuState(Enum):
    '''State Machine variables for the booking system'''
    HOME = 0
    VIEW_CURRENT_HOTEL_SLOTS = 1
    VIEW_CURRENT_BAND_SLOTS = 2
    BOOK_SLOT = 3
    CANCEL_HELD_SLOT = 4
    VIEW_5_UPCOMING_SLOTS = 5
    RESERVE_EARLIEST_SLOT = 6
    CANCEL_UNNEEDED_RESERVATION = 7


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

        self.data_cache = dict()
    
    def _print_title(self, title: str):
        '''
        Function which prints a formatted title of the form: 
        <br>|-----| TITLE |-----|
        '''
        dash_repeat = int((BookingSystem.TITLE_WIDTH - (6 + len(title))) / 2)
        section = "|" + "-" * dash_repeat + "|"
        print(section + " " + title + " " + section)

    def _reset_stdout(self):
        ''' Function which clears the output of the terminal and prints the menu title at the top '''
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * BookingSystem.TITLE_WIDTH)
        self._print_title(BookingSystem.TITLE)
        print("=" * BookingSystem.TITLE_WIDTH)

    def parse_list(self, raw_data: dict) -> list[str]:
        ''' Function used in order to parse the slot data for a list of bookings '''
        out = []
        for item in raw_data:
            out.append(f"Slot {item.get('id')}")
        return out

    def set_menu_state(self, state):
        ''' Used to change what state the booking system is in. '''
        self.state = state
        # ----------------- TITLE -----------------
        self._reset_stdout()
        print()

    def get_matching_available_slots(self, limit = None):
        hotel_availability = self.hotel.get_slots_available()
        band_availability = self.band.get_slots_available()
        matches = []

        for slot in hotel_availability:
            if slot in band_availability:                
                matches.append(slot)

        if limit != None: return matches[:limit]
        else: return matches

    def load_held_hotel_slots_menu():
        pass
    
    def load_held_band_slots_menu():
        pass

    def load_book_slot_menu(self):
        ''' Menu function for booking a slot '''
        self._print_title("Book a Slot")
        # try call api and handle any errors that might come with that
        try:
            data = self.get_matching_available_slots()
            
            # parse the data and print to console output
            if data == None:
                print("No available slots are remaining")
                return

            self._print_title("Avaialable Slots")
            for res in self.parse_list(data):
                print(res)
            print()

            # --- BOOKING LOGIC ---
            option = None
            # poll to see if user wants to continue
            while option == None:
                option = input("Do you wish to continue with the request? (Yes/No): ")
                if option.lower() != "yes" and option.lower() != "no":
                    print("Invalid option selected.")
                    option = None
            
            if option.lower() == "no": return

            # poll for relevant slot
            option = None
            while option == None:
                try:
                    option = int(input("Enter Slot ID: "))
                except:
                    print("Invalid slot ID.")
            
            print("Attempting to book slot...")
            # ensure that if any errors occur, the system cleans up after itself
            try: self.hotel.reserve_slot(option)
            except: return
            
            try: self.band.reserve_slot(option)
            except:
                self.hotel.release_slot(option)
                return
            
            print(f"SUCCESS! Slot {option} has been reserved successfully.")

        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            self.set_menu_state(MenuState.HOME)

    def load_cancel_slot_menu(self):
        ''' Menu for removing a reserved slot '''
        self._print_title("Cancel a Held Slot")
        # try call api and handle any errors that might come with that
        try:
            data = self.hotel.get_slots_held()
            
            # parse the data and print to console output
            if data == None:
                print("No slots are being currently held by the user")
                return

            for res in self.parse_list(data):
                print(res)
            print()

            # --- BOOKING LOGIC ---
            option = None
            # poll to see if user wants to continue
            while option == None:
                option = input("Do you wish to continue with the request? (Yes/No): ")
                if option.lower() != "yes" and option.lower() != "no":
                    print("Invalid option selected.")
                    option = None
            
            if option.lower() == "no": return

            # poll for relevant slot
            option = None
            while option == None:
                try:
                    option = int(input("Enter Slot ID: "))
                except:
                    print("Invalid slot ID.")
            
            print("Attempting to cancel slot...")
            self.hotel.release_slot(option)
            self.band.release_slot(option)

            print(f"SUCCESS! Slot {option} has been cancelled successfully.")

        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            self.set_menu_state(MenuState.HOME)

    def start(self):
        do_mainloop = True
        self.set_menu_state(MenuState.HOME)

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
                print("1. View the current slots held for the hotel")
                print("2. View the current slots held for the band")
                print("3. Book a specified slot")
                print("4. Cancel a held slot")
                print("5. View the first 5 available slots")
                print("6. Reserve the earliest available slot")
                print("7. Cancel unneeded reservations")
                print("8. Quit\n")

                option = None
                while option == None:
                    try:
                        option = int(input("Enter operation number: "))
                    except:
                        print("Invalid operation selected.")
                
                match option:
                    case 1:
                        slot_data = self.rate_limiter.run_task(lambda: self.hotel.get_slots_held())
                        self.parse_list(slot_data)
                    case 2:
                        slot_data = self.rate_limiter.run_task(lambda: self.band.get_slots_held())
                        self.parse_list(slot_data)
                    case 3:
                        self.set_menu_state(MenuState.BOOK_SLOT)
                    case 4:
                        self.set_menu_state(MenuState.CANCEL_HELD_SLOT)
                    case 5:
                        pass
                    case 6:
                        pass
                    case 7:
                        pass
                    case 8:
                        do_mainloop = False
                    case _:
                        print("Invalid operation selected.")

            # --------- MENU OPTION 1 ---------
            elif self.state == MenuState.VIEW_CURRENT_HOTEL_SLOTS:
                self.load_held_hotel_slots_menu()

            # --------- MENU OPTION 2 ---------
            elif self.state == MenuState.VIEW_CURRENT_BAND_SLOTS:
                self.load_held_band_slots_menu()

            # --------- MENU OPTION 3 ---------
            elif self.state == MenuState.BOOK_SLOT:
                self.load_book_slot_menu()
                                
            # --------- MENU OPTION 4 ---------
            elif self.state == MenuState.CANCEL_HELD_SLOT:
                self.load_cancel_slot_menu()

            # --------- MENU OPTION 5 ---------
            elif self.state == MenuState.VIEW_5_UPCOMING_SLOTS:
                print("Fetching data...")
                slot_data = self.get_matching_available_slots(5)
                try:
                    if slot_data != None:
                        self.parse_list(slot_data)
                    else:
                        print("No current matching slots are available.")
                except Exception as e:
                    print(f"An error occurred when fecthing data: {e}")

                input("Press Enter to continue...")
                self.set_menu_state(MenuState.HOME)

            # --------- MENU OPTION 6 ---------
            elif self.state == MenuState.RESERVE_EARLIEST_SLOT:
                pass

            # --------- MENU OPTION 7 ---------
            elif self.state == MenuState.CANCEL_UNNEEDED_RESERVATION:
                pass


if __name__ == "__main__":
    booking_system = BookingSystem()
    booking_system.start()
