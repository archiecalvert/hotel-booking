from .menu import (Menu, MenuState)
import reservationapi
import math
class MenuBookedSlots(Menu):
    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)
    
    def load(self):
        ''' Menu function for booking a slot '''
        Menu._print_title("Book a Slot")
        # try call api and handle any errors that might come with that
        try:
            print("Fetching booking data...")

            # check that the maximum number of bookings haven't been made.
            hotel_bookings = self.hotel.get_slots_held()
            band_bookings = self.band.get_slots_held()

            if len(hotel_bookings) >= self.hotel.max_bookings_count and len(band_bookings) >= self.band.max_bookings_count:
                print("The maximum number of hotel and band bookings has been made. Please cancel a booking from each to continue.")
                return
            
            elif len(hotel_bookings) >= self.hotel.max_bookings_count:
                print("The maximum number of hotel bookings have been made. Please cancel one to continue")
                return
            
            elif len(band_bookings) >= self.band.max_bookings_count:
                print("The maximum number of band bookings have been made. Please cancel one to continue")
                return

            data = self.get_matching_available_slots()
            
            # parse the data and print to console output
            if data == None or data == []:
                print("No available slots are remaining")
                return


            # data menu logic
            column_count = 8
            column_length = math.ceil(float(len(data)) / column_count)
            row_data = [""] * column_length

            print("Available slots:\n")
            for i, res in enumerate(self.parse_list(data)):
                # creates a column based layout
                index = i % column_length
                row_data[index] += f"\033[95m  {res:<15}|\033[0m"
            
            for row in row_data:
                print(row)

            print()

            # --- BOOKING LOGIC ---
            option = self.poll_yes_no("Do you wish to continue with the request? (Yes/No): ")
            if option.lower() == "no": return

            option = self.poll_slot_id("Enter Slot ID: ", data)
            print("Attempting to book slot...")
    
            try:
                self.book_matching_slot(option)
                print(f"\033[32mSUCCESS:\033[0m Slot {option} has been reserved successfully.")
            except Exception as e:
                print("Failed to book the requested slot. Please return to the main menu and try again.")
                raise e

        except Exception as e:
            print(f"An error occurred while performing the request: {e}")

        finally:
            # keep on screen until user confirms theyre finished
            input("Press Enter to return to the home menu...")
            return MenuState.HOME