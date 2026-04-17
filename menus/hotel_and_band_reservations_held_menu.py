from .menu import (Menu, MenuState)
import reservationapi

class MenuHeldHotelsAndBands(Menu):

    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)

    def load(self) -> MenuState:
        Menu._print_title("Held Slots")
        try:
            hotel_data = self.hotel.get_slots_held()
            band_data = self.band.get_slots_held()

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
            return MenuState.HOME