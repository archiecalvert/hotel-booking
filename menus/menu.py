from enum import Enum
import reservationapi
import os
from concurrent.futures import ThreadPoolExecutor

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

class BookingType(Enum):
    HOTEL = 0
    BAND = 1
    MATCHING = 2

class Menu():

    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        self.hotel = hotel
        self.band = band


    def load(self) -> MenuState:
        return
    
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

        Args:
            title(str): The title to be inserted into the output
        '''
        dash_repeat = int((TITLE_WIDTH - (6 + len(title))) / 2)
        section = "|" + "-" * dash_repeat + "|"
        print(section + " " + title + " " + section)

    def parse_list(self, raw_data: list[dict]) -> list[str]:
        ''' Function used in order to parse the slot data for a list of bookings
        
        Args:
            raw_data(list[dict]): data dictionary returned from ReservationApi

        Returns:
            list[str]: A list of strings, each formatted as 'Slot \<slot_id\>'
        '''
        out = []
        for item in raw_data:
            out.append(f"Slot {item.get('id')}")
        return out

    def poll_yes_no(self, prompt: str = "") -> str:
        ''' Function which prompts the user in the terminal for a yes/no answer.
        
        Args:
            prompt(str): A prompt to the user displayed next to the input.
        Returns:
            str: Either 'yes' or 'no' (matching these cases)
        '''
        option = None
        while option == None:
                option = input(prompt)
                if option.lower() != "yes" and option.lower() != "no":
                    print("Invalid option selected.")
                    option = None
            
        return option.lower()
    
    def poll_slot_id(self, prompt: str, slot_data: list[dict]) -> int:
        ''' Function which polls for a slot ID for the user. 
        
        Args:
            prompt(str): The prompt to the user to be displayed in the terminal.
            slot_data(list[dict]): The slot data returned from the ReservationApi

        Returns:
            int: The selected slot by the user
        '''
        if slot_data == None or len(slot_data) == 0: raise Exception("No slot data was provided.")

        valid_ids = [int(x.get("id")) for x in slot_data]
        # poll for relevant slot
        option = None
        while option == None:
            try:
                option = int(input(prompt))
                if option not in valid_ids:
                    option = None
                    print("Slot entered is not available. Please try a listed slot.")
            except:
                print("Invalid slot ID.")

        return option
    
    def poll_individual_matching_booking(self) -> str:
        ''' Function which polls for a whether they want to make an individual booking or a 
        matching booking.
        
        Returns:
            BookingType | None: what kind of booking the user selected, or none if the operation was cancelled
        '''
        option = None
        while option == None:
            try:
                print("What kind of booking would you like to make:")
                print("\033[95m1. Hotel")
                print("2. Band")
                print("3. Matching slot")
                print("4. Cancel Operation\033[0m")
                print()
                option = int(input("Please enter your corresponding option number (1, 2, 3, 4): "))

                if option == 1:
                    return BookingType.HOTEL
                elif option == 2:
                    return BookingType.BAND
                elif option == 3:
                    return BookingType.MATCHING
                elif option == 4:
                    return None
                else:
                    print("Invalid option selected.")
                    option = None
            except:
                print("Invalid option selected.")


    def matchup_slots(self, hotel_data: list[dict], band_data: list[dict]) -> list[dict]:
        ''' Function which takes in two booking lists from the API, and returns the slots which match up
        
        Args:
            hotel_data(list[dict]): The hotel slot data from the ReservationApi
            band_data(list[dict]): The band slot data from the ReservationApi

        Returns:
            list[dict]: An array of matched slots.

        '''
        matches = []

        for slot in hotel_data:
            if slot in band_data:                
                matches.append(slot)

        return matches

    def get_slots_held(self) -> tuple:
        ''' Function which gets the held slots from the APIs asynchronously.
        
        Returns:
            (list[dict], list[dict]): A tuple of (hotel_data, band_data)
        '''
        with ThreadPoolExecutor() as executor:
            t1 = executor.submit(self.hotel.get_slots_held)
            t2 = executor.submit(self.band.get_slots_held)

            return (t1.result(), t2.result())
    
    def cancel_matching_slot(self, slot_id: int):
        ''' Function which attempts to remove a booking of the same slot. If this cant happen, then an exception is thrown
        
        Args:
            slot_id(int): The id of the target slot from the ReservationApi
        '''
        try:
            with ThreadPoolExecutor() as executor:
                t1 = executor.submit(lambda:self.hotel.release_slot(slot_id))
                t2 = executor.submit(lambda:self.band.release_slot(slot_id))

                #  raise exepctions if they occur
                t1.result()
                t2.result()
        except Exception as e:
            print(f"An error occured when cancelling slot {slot_id}. You may want to run manual clean-up from the Home Menu.")
            raise e

    def book_matching_slot(self, slot_id: int):
        ''' Function which attempts to book a matching slot. If this cant occur, then the system releases partial bookings.
        
        Args:
            slot_id(int): The id of the target slot from the ReservationApi
        '''
        # ensure that if any errors occur, the system cleans up after itself
        try:
            with ThreadPoolExecutor() as executor:
                t1 = executor.submit(lambda:self.hotel.reserve_slot(slot_id))
                t2 = executor.submit(lambda:self.band.reserve_slot(slot_id))

                #  raise exepctions if they occur
                t1.result()
                t2.result()
        except Exception as e:
            self.hotel.release_slot(slot_id)
            raise e


    def get_slots_available(self, bypass_cache:bool = False):
        with ThreadPoolExecutor() as executor:
            t1 = executor.submit(lambda: self.hotel.get_slots_available(bypass_cache))
            t2 = executor.submit(lambda: self.band.get_slots_available(bypass_cache))

            return (t1.result(), t2.result())
    

    def get_matching_available_slots(self, limit:int = None, bypass_cache:bool = False) -> list[dict]:
        ''' Function which gets all matching slots for hotel and band.
        
        Args:
            limit(int): (optional) The number of returned items
        
        '''
        hotel_availability, band_availability = self.get_slots_available(bypass_cache)
        
        matches = self.matchup_slots(hotel_availability, band_availability)

        if limit != None: return matches[:limit]
        else: return matches

    def cleanup_bookings(self):
        ''' Function which attempts to clean up bad, unmatched bookings.
        
        Args:
            hotel_data(list[dict]): Hotel slot data returned from the ReservationApi
            band_data(list[dict]): Band slot data returned from the ReservationApi
        '''
        hotel_data, band_data = self.get_slots_held()

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
