from .menu import (Menu, MenuState)
import reservationapi

class MenuHome(Menu):
    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)

    def load(self) -> MenuState:
        # ------------- CURRENT SLOTS -------------
        booked_slots = self.parse_list(self.hotel.get_slots_held())
        # if we have slots booked, then we print them
        if len(booked_slots) > 0:
            Menu._print_title("CURRENTLY HELD SLOTS")
            for slot in booked_slots:
                print(slot)
            print()

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
