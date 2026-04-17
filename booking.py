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
    
    # --------- WRAPPER METHODS ---------
    def get_slots_available(self, object: reservationapi.ReservationApi):
        return self.run_task(lambda: object.get_slots_available())
    
    def get_slots_held(self, object: reservationapi.ReservationApi):
        return self.run_task(lambda: object.get_slots_held())
    
    def release_slot(self, object: reservationapi.ReservationApi,  slot_id):
        return self.run_task(lambda: object.release_slot(slot_id))
    
    def reserve_slot(self, object: reservationapi.ReservationApi,  slot_id):
        return self.run_task(lambda: object.reserve_slot(slot_id))

class MenuState(Enum):
    '''State Machine variables for the booking system'''
    HOME = 0
    VIEW_CURRENT_HOTEL_BAND_SLOTS = 1
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

    def cancel_matching_slot(self, slot_id):
        try:
            self.rate_limiter.release_slot(self.hotel, slot_id)
            self.rate_limiter.release_slot(self.band, slot_id)
        except Exception as e:
            print(f"An error occured when cancelling slot {slot_id}. You may want to run manual clean-up from the Home Menu.")
            raise e

    def book_matching_slot(self, slot_id):
        # ensure that if any errors occur, the system cleans up after itself
        try:
            self.rate_limiter.reserve_slot(self.hotel, slot_id)
            self.rate_limiter.reserve_slot(self.band, slot_id)
        except Exception as e:
            self.rate_limiter.release_slot(self.hotel, slot_id)
            raise e

    def get_matching_available_slots(self, limit = None):

        hotel_availability = self.rate_limiter.get_slots_available(self.hotel)
        band_availability = self.rate_limiter.get_slots_available(self.band)
        matches = []

        for slot in hotel_availability:
            if slot in band_availability:                
                matches.append(slot)

        if limit != None: return matches[:limit]
        else: return matches

    def cleanup_bookings(self, hotel_data: None, band_data: None):
        if hotel_data == None: hotel_data = self.rate_limiter.get_slots_held(self.hotel)
        if band_data == None: hotel_data = self.rate_limiter.get_slots_held(self.band)

        for slot in hotel_data:
            if slot not in band_data:
                id = slot.get("id")
                try:
                    self.rate_limiter.release_slot(self.hotel, id)
                except Exception as e:
                    print(f"An error occured trying to cancel hotel slot {id}: {e}. Continuing...")
        
        for slot in band_data:
            if slot not in hotel_data:
                id = slot.get("id")
                try:
                    self.rate_limiter.release_slot(self.band, id)
                except Exception as e:
                    print(f"An error occured trying to cancel band slot {id}: {e}. Continuing...")


    def load_held_hotel_band_slots_menu(self):
        self._print_title("Held Slots")
        try:
            hotel_data = self.rate_limiter.get_slots_held(self.hotel)
            band_data = self.rate_limiter.get_slots_held(self.band)

            if hotel_data == [] and band_data == []:
                print("No slots are being currently held")
                return
            
            print(f"{" " * 9}{'HOTEL':<16}{"|":<12}BAND")

            for i in range(max(len(hotel_data), len(band_data))):
                hotel_slot = f"Slot {hotel_data[i]['id']}" if i < len(hotel_data) else ""
                band_slot = f"Slot {band_data[i]['id']}" if i < len(band_data) else ""
                print(f"  {hotel_slot:<23}|  {band_slot}")

            print()

        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            self.set_menu_state(MenuState.HOME)

    
    def load_held_band_slots_menu():
        pass

    def load_book_slot_menu(self):
        ''' Menu function for booking a slot '''
        self._print_title("Book a Slot")
        # try call api and handle any errors that might come with that
        try:
            data = self.get_matching_available_slots()
            
            # parse the data and print to console output
            if data == None or data == []:
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
    
            try:
                self.book_matching_slot(option)
                print(f"SUCCESS! Slot {option} has been reserved successfully.")
            except Exception as e:
                print("Failed to book the requested slot. Please return to the main menu and try again.")
                raise e

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
            data = self.rate_limiter.get_slots_held(self.hotel)
            
            # parse the data and print to console output
            if data == None or data == []:
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
            self.cancel_matching_slot(option)
            print(f"SUCCESS! Slot {option} has been cancelled successfully.")

        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            self.set_menu_state(MenuState.HOME)

    def load_first_5_slots_menu(self):
        self._print_title("Available Slots (Limit of 5)")
        try:
            print("Fetching data...")
            slot_data = self.get_matching_available_slots(5)
            if slot_data != None:
                for slot in self.parse_list(slot_data):
                    print(slot)
            else:
                print("No current matching slots are available.")
    
        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            self.set_menu_state(MenuState.HOME)
        
    def load_book_earliest_slot_menu(self):
        ''' Menu function for booking a slot '''
        self._print_title("Book a Slot")
        # try call api and handle any errors that might come with that
        try:
            data = self.get_matching_available_slots(1)
            
            # parse the data and print to console output
            if data == None or data == []:
                print("No available slots are remaining")
                return

            slot_id = data[0].get("id")
            print(f"The earliest available slot is Slot {slot_id}")

            # --- BOOKING LOGIC ---
            option = None
            # poll to see if user wants to continue
            while option == None:
                option = input("Would you like to book this slot (Yes/No): ")
                if option.lower() != "yes" and option.lower() != "no":
                    print("Invalid option selected.")
                    option = None
            
            if option.lower() == "no": return
                
            print("Attempting to book slot...")
            
            try:
                self.book_matching_slot(slot_id)
                print(f"SUCCESS! Slot {option} has been reserved successfully.")
            except Exception as e:
                print("Failed to book the requested slot. Please return to the main menu and try again.")
                raise e
    
        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            self.set_menu_state(MenuState.HOME)

    def load_unneeded_reservations_menu(self):
        self._print_title("Cancel Unneeded Reservation")
        try:
            print("Fetching reservation data...")
            hotel_data = self.rate_limiter.get_slots_held(self.hotel)
            band_data = self.rate_limiter.get_slots_held(self.band)

            unmatched_hotels = []
            unmatched_bands = []

            found = False
            out = []
            for slot in hotel_data:
                if slot not in band_data:
                    out.append(f"Hotel Slot {slot.get("id")}")
                    unmatched_hotels.append(slot)
                    found = True

            for slot in band_data:
                if slot not in hotel_data:
                    out.append(f"Band Slot {slot.get("id")}")
                    unmatched_bands.append(slot)
                    found = True
            
            if found:
                print("Found unmatched bookings:")
                for x in out:
                    print(x)
            else:
                print("No unnmatched bookings found.")
                return
            
            option = None
            while option == None:
                option = input("Would you like to remove these bookings? (Yes/No): ")
                if option.lower() != "yes" and option.lower() != "no":
                    print("Invalid option selected.")
                    option = None
            
            if option.lower() == "no": return

            print("Cleaning up bookings...")
            self.cleanup_bookings(unmatched_hotels, unmatched_bands)


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
                booked_slots = self.parse_list(self.rate_limiter.get_slots_held(self.hotel))
                # if we have slots booked, then we print them
                if len(booked_slots) > 0:
                    self._print_title("CURRENTLY HELD SLOTS")
                    for slot in booked_slots:
                        print(slot)
                    print()

                # --------------- OPERATIONS --------------
                self._print_title(" OPERATIONS ")
                print("1. View the current slots held for the hotel and band")
                print("2. View the first 20 available slots for the hotel and band")
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
                        self.set_menu_state(MenuState.VIEW_CURRENT_HOTEL_BAND_SLOTS)
                    case 2:
                        pass
                    case 3:
                        self.set_menu_state(MenuState.BOOK_SLOT)
                    case 4:
                        self.set_menu_state(MenuState.CANCEL_HELD_SLOT)
                    case 5:
                        self.set_menu_state(MenuState.VIEW_5_UPCOMING_SLOTS)
                    case 6:
                        self.set_menu_state(MenuState.RESERVE_EARLIEST_SLOT)
                    case 7:
                        self.set_menu_state(MenuState.CANCEL_UNNEEDED_RESERVATION)
                    case 8:
                        do_mainloop = False
                    case _:
                        print("Invalid operation selected.")

            # --------- MENU OPTION 1 ---------
            elif self.state == MenuState.VIEW_CURRENT_HOTEL_BAND_SLOTS:
                self.load_held_hotel_band_slots_menu()

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
                self.load_first_5_slots_menu()

            # --------- MENU OPTION 6 ---------
            elif self.state == MenuState.RESERVE_EARLIEST_SLOT:
                self.load_book_earliest_slot_menu()

            # --------- MENU OPTION 7 ---------
            elif self.state == MenuState.CANCEL_UNNEEDED_RESERVATION:
                self.load_unneeded_reservations_menu()


if __name__ == "__main__":
    booking_system = BookingSystem()
    booking_system.start()
