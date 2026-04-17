from enum import Enum
import reservationapi
import os

TITLE_WIDTH = 54
TITLE = "WEDDING BOOKING SYSTEM"

class MenuState(Enum):
    '''State Machine variables for the booking system'''
    HOME = 0
    VIEW_CURRENT_HOTEL_BAND_SLOTS = 1
    VIEW_20_AVAILABLE_SLOTS = 2
    BOOK_SLOT = 3
    CANCEL_HELD_SLOT = 4
    VIEW_5_UPCOMING_SLOTS = 5
    RESERVE_EARLIEST_SLOT = 6
    CANCEL_UNNEEDED_RESERVATION = 7
    QUIT = 8

class Menu():

    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        self.hotel = hotel
        self.band = band


    def load(self) -> MenuState:
        return

    def cancel_matching_slot(self, slot_id):
        ''' Function which attempts to remove a booking of the same slot. If this cant happen, then an exception is thrown '''
        try:
            self.hotel.release_slot(slot_id)
            self.band.release_slot(slot_id)
        except Exception as e:
            print(f"An error occured when cancelling slot {slot_id}. You may want to run manual clean-up from the Home Menu.")
            raise e

    def book_matching_slot(self, slot_id):
        ''' Function which attempts to book a matching slot. If this cant occur, then the system releases partial bookings. '''
        # ensure that if any errors occur, the system cleans up after itself
        try:
            self.hotel.reserve_slot(slot_id)
            self.band.reserve_slot(slot_id)
        except Exception as e:
            self.hotel.release_slot(slot_id)
            raise e

    def get_matching_available_slots(self, limit = None):
        ''' Booking which gets all matching slots for hotel and band. '''
        hotel_availability = self.hotel.get_slots_available()
        band_availability = self.band.get_slots_available()
        matches = []

        for slot in hotel_availability:
            if slot in band_availability:                
                matches.append(slot)

        if limit != None: return matches[:limit]
        else: return matches

    def cleanup_bookings(self, hotel_data: None, band_data: None):
        ''' Function which attempts to clean up bad, unmatched bookings. '''
        if hotel_data == None: hotel_data = self.hotel.get_slots_held()
        if band_data == None: band_data = self.band.get_slots_held()

        for slot in hotel_data:
            if slot not in band_data:
                id = slot.get("id")
                try:
                    self.hotel.release_slot(id)
                except Exception as e:
                    print(f"An error occured trying to cancel hotel slot {id}: {e}. Continuing...")
        
        for slot in band_data:
            if slot not in hotel_data:
                id = slot.get("id")
                try:
                    self.band.release_slot(id)
                except Exception as e:
                    print(f"An error occured trying to cancel band slot {id}: {e}. Continuing...")

    def _reset_stdout():
        ''' Function which clears the output of the terminal and prints the menu title at the top '''
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * TITLE_WIDTH)
        Menu._print_title(TITLE)
        print("=" * TITLE_WIDTH)

    def _print_title(title: str):
        '''
        Function which prints a formatted title of the form: 
        <br>|-----| TITLE |-----|
        '''
        dash_repeat = int((TITLE_WIDTH - (6 + len(title))) / 2)
        section = "|" + "-" * dash_repeat + "|"
        print(section + " " + title + " " + section)

    def parse_list(self, raw_data: dict) -> list[str]:
        ''' Function used in order to parse the slot data for a list of bookings '''
        out = []
        for item in raw_data:
            out.append(f"Slot {item.get('id')}")
        return out
    
    def poll_yes_no(self, prompt) -> str:
        option = None
        while option == None:
                option = input("Do you wish to continue with the request? (Yes/No): ")
                if option.lower() != "yes" and option.lower() != "no":
                    print("Invalid option selected.")
                    option = None
            
        return option.lower()