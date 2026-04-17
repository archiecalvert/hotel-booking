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
            return MenuState.HOME