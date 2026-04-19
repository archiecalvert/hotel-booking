from .menu import (Menu, MenuState, BookingType)
import reservationapi

class MenuCancelSlot(Menu):
    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)

    def load(self) -> MenuState:
        ''' Menu for removing a reserved slot '''
        Menu._print_title("Cancel a Held Slot")
        # try call api and handle any errors that might come with that
        try:
            booking_option = self.poll_individual_matching_booking()
            if booking_option == None:
                return
            
            print("Fetching booking data...")
            match booking_option:
                case BookingType.HOTEL: data = self.hotel.get_slots_held()
                case BookingType.BAND:  data = self.band.get_slots_held()
                case BookingType.MATCHING:
                    hotel_data, band_data = self.get_slots_held()
                    data = self.matchup_slots(hotel_data, band_data)
                case _:
                    return
            
            # parse the data and print to console output
            if data == None or data == []:
                print("\033[95mNo slots are being currently held by the user\033[0m")
                print()
                return

            for res in self.parse_list(data):
                print(f"\033[95m{res}\033[0m")
            print()

            # --- BOOKING LOGIC ---
            option = self.poll_yes_no("Do you wish to continue with the request? (Yes/No): ")            
            if option == "no": return

            # poll for relevant slot
            option = self.poll_slot_id("Enter Slot ID: ", data)
            
            print("Attempting to cancel slot...")
            match booking_option:
                case BookingType.HOTEL:    self.hotel.release_slot(option)
                case BookingType.BAND:     self.band.release_slot(option)
                case BookingType.MATCHING: self.cancel_matching_slot(option)

            print(f"\033[32mSUCCESS:\033[0m Slot {option} has been cancelled successfully.")

        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            return MenuState.HOME