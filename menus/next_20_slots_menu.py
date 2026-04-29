from .menu import (Menu, MenuState)
import reservationapi

class Menu20AvailableHotelsAndBands(Menu):
    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)
    
    def load(self) -> MenuState:
        Menu._print_title("Earliest 20 Available Slots")
        try:
            print("Fetching booking data...")
            hotel_data, band_data = self.get_slots_available()

            hotel_held, band_held = self.get_slots_held()
            hotel_unmatched, band_unmatched = self.get_unmatched_held_bookings(hotel_held, band_held)
            match_data = self.get_matching_available_slots(None, hotel_unmatched, band_unmatched, False)

            hotel_data = hotel_data[:20]
            band_data = band_data[:20]
            match_data = match_data[:20]
            if hotel_data == [] and band_data == [] and match_data == []:
                print("\033[95mNo slots are being currently available\033[0m")
                print()
                return
            
            # creates a grid of the next 20 slots in the form
            #               |   HOTEL   |   BAND    |
            print()
            print(f"\033[95m\033[4m{" " * 9}{'HOTEL':<16}{"|":<11}{'BAND':<15}{"|":<10}{'MATCHING':<16}\033[0m")
            for i in range(max(len(hotel_data), len(band_data), len(match_data))):
                hotel_slot = f"Slot {hotel_data[i]['id']}" if i < len(hotel_data) else ""
                band_slot =  f"Slot {band_data[i]['id']}"  if i < len(band_data)  else ""
                match_slot = f"Slot {match_data[i]['id']}"  if i < len(match_data)  else ""
                print(f"\033[95m  {hotel_slot:<23}|  {band_slot:<23}|  {match_slot:<23}\033[0m")
            
            print()

        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            return MenuState.HOME