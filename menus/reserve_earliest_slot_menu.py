from .menu import (Menu, MenuState)
import reservationapi

class MenuReserveEarliestSlot(Menu):
    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)

    def load(self):
        ''' Menu function for booking a slot '''
        Menu._print_title("Book a Slot")
        # try call api and handle any errors that might come with that
        try:
            print("Fetching booking data...")
            hotel_data, band_data = self.get_slots_held()

            if len(hotel_data) >= self.hotel.max_bookings_count and len(band_data) >= self.band.max_bookings_count:
                print("\033[95mThe maximum number of hotel and band bookings has been made.")
                option = self.poll_yes_no("Would you like to cancel a booking? (Yes/No) \033[0m")
                if option == "no":
                    input("Press Enter to return to the home menu...")
                    return MenuState.HOME
                else:
                    Menu.callback = MenuState.RESERVE_EARLIEST_SLOT
                    return MenuState.CANCEL_HELD_SLOT
            
            elif len(hotel_data) >= self.hotel.max_bookings_count:
                print("\033[95mThe maximum number of hotel bookings have been made.")
                option = self.poll_yes_no("Would you like to cancel a booking? (Yes/No) \033[0m")
                if option == "no":
                    input("Press Enter to return to the home menu...")
                    return MenuState.HOME
                else:
                    Menu.callback = MenuState.RESERVE_EARLIEST_SLOT
                    return MenuState.CANCEL_HELD_SLOT
            
            elif len(band_data) >= self.band.max_bookings_count:
                print("\033[95mThe maximum number of band bookings have been made.")
                option = self.poll_yes_no("Would you like to cancel a booking? (Yes/No) \033[0m")
                if option == "no":
                    input("Press Enter to return to the home menu...")
                    return MenuState.HOME
                else:
                    Menu.callback = MenuState.RESERVE_EARLIEST_SLOT
                    return MenuState.CANCEL_HELD_SLOT
        
            data = self.get_matching_available_slots(1)
            
            # parse the data and print to console output
            if data == None or data == []:
                print("\033[95mNo available slots are remaining\033[0m")
                print()
                input("Press Enter to return to the home menu...")
                return MenuState.HOME

            slot_id = int(data[0].get("id"))
            print(f"The earliest available slot is \033[95mSlot {slot_id}\033[0m")
            print()
            # --- BOOKING LOGIC ---
            option = self.poll_yes_no("Would you like to book this slot (Yes/No): ")            
            if option == "no":
                input("Press Enter to return to the home menu...")
                return MenuState.HOME
            
            print("Attempting to book slot...")
            
            try:
                self.book_matching_slot(slot_id)
                # try book an earlier slot
                try:
                    attempt = self.get_matching_available_slots(limit=1, bypass_cache=True)
                    if len(attempt) > 0 and int(attempt[0].get("id")) < slot_id:
                        new_id = int(attempt[0].get("id"))
                        print(f"INFO: Earlier booking has been found (Slot {new_id}). Attempting to book...")
                        self.cancel_matching_slot(slot_id) # remove earliest slot 
                        self.book_matching_slot(new_id)    # book earlier slot
                        slot_id = new_id                   # runs if the newer booking was successful

                    print(f"\033[32mSUCCESS:\033[0m Slot {slot_id} has been reserved successfully.")
                except Exception as e:
                    raise e
            except Exception as e:
                print("Failed to book the requested slot. Please return to the main menu and try again.")
                raise e

            input("Press Enter to return to the home menu...")
            return MenuState.HOME
        except Exception as e:
            print(f"An error occurred while performing the request: {e}")
            input("Press Enter to return to the home menu...")
            return MenuState.HOME
