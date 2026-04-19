from .menu import (Menu, MenuState)
import reservationapi

class MenuCancelUnneededReservations(Menu):
    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)

    def load(self) -> MenuState:
        Menu._print_title("Cancel Unneeded Reservation")
        try:
            print("Fetching reservation data...")
            hotel_data, band_data = self.get_slots_held()

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
            
            option = self.poll_yes_no("Would you like to remove these bookings? (Yes/No): ")
            if option.lower() == "no": return

            print("Cleaning up bookings...")
            self.cleanup_bookings()


        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            return MenuState.HOME