from .menu import (Menu, MenuState)
import reservationapi

class MenuHome(Menu):
    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)

    def load(self) -> MenuState:
        # ------------- CURRENT SLOTS -------------
        print("Fetching booking data...")
        try:
            hotel_data = self.hotel.get_slots_held()
            band_data = self.band.get_slots_held()

            if not (len(hotel_data) == 0 and len(band_data) == 0):  
                print()
                Menu._print_title("CURRENT BOOKINGS")
                print()
                print(f"\033[95m\033[4m{" " * 9}{'HOTEL':<16}{"|":<13}{'BAND':<16}\033[0m")
                for i in range(max(len(hotel_data), len(band_data))):
                    hotel_slot = f"Slot {hotel_data[i]['id']}" if i < len(hotel_data) else ""
                    band_slot = f"Slot {band_data[i]['id']}" if i < len(band_data) else ""
                    print(f"\033[95m  {hotel_slot:<23}|  {band_slot}\033[0m")
                
                print()
            else:
                print("\033[95mNo bookings found\033[0m")
                print()

        except Exception as e:
            print("Error fetching held slots. Please try again later.")

        # --------------- OPERATIONS --------------
        Menu._print_title(" OPERATIONS ")
        print("1. View the current slots held for the hotel and band")
        print("2. View the first 20 available slots for the hotel and band")
        print("3. Book a specified slot")
        print("4. Cancel a held slot")
        print("5. View the first 5 available slots")
        print("6. Reserve the earliest available slot")
        print("7. Cancel unneeded reservations")
        print("8. Quit\n")

        # This loop will run forever until the correct option has been selected
        while True:
            option = None
            while option == None:
                try:
                    option = int(input("Enter operation number: "))
                except:
                    print("Invalid operation selected.")
            
            match option:
                case 1:
                    return MenuState.VIEW_CURRENT_HOTEL_BAND_SLOTS
                case 2:
                    return MenuState.VIEW_20_AVAILABLE_SLOTS
                case 3:
                    return MenuState.BOOK_SLOT
                case 4:
                    return MenuState.CANCEL_HELD_SLOT
                case 5:
                    return MenuState.VIEW_5_UPCOMING_SLOTS
                case 6:
                    return MenuState.RESERVE_EARLIEST_SLOT
                case 7:
                    return MenuState.CANCEL_UNNEEDED_RESERVATION
                case 8:
                    return MenuState.QUIT
                case _:
                    print("Invalid operation selected.")
                
