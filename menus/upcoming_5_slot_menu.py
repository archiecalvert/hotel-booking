from .menu import (Menu, MenuState)
import reservationapi

class MenuUpcoming5Slots(Menu):
    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)

    def load(self):
        Menu._print_title("Available Slots (Limit of 5)")
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
            return MenuState.HOME
