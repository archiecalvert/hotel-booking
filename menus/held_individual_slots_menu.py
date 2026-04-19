from .menu import (Menu, MenuState)
import reservationapi

class MenuHeldHotelsAndBands(Menu):

    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)

    def load(self) -> MenuState:
        Menu._print_title("Held Slots")
        try:
            print("Fetching booking data...")
            hotel_data, band_data = self.get_slots_held()
            match_data = self.matchup_slots(hotel_data, band_data)

            if hotel_data == [] and band_data == []:
                print("\033[95mNo bookings found\033[0m")
                print()
                return
            
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