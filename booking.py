#!/usr/bin/python3
import reservationapi
import configparser
from menus.menu                                     import (Menu, MenuState)
from menus.book_slot_menu                           import MenuBookedSlots
from menus.cancel_slot_menu                         import MenuCancelSlot
from menus.cancel_unneeded_slots_menu               import MenuCancelUnneededReservations
from menus.home_menu                                import MenuHome
from menus.held_individual_slots_menu               import MenuHeldHotelsAndBands
from menus.next_20_slots_menu                       import Menu20AvailableHotelsAndBands
from menus.reserve_earliest_slot_menu               import MenuReserveEarliestSlot
from menus.upcoming_5_slots_menu                    import MenuUpcoming5Slots

class BookingSystem():
    
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("api.ini")

        # Create an API object to communicate with the hotel API
        self.hotel  = reservationapi.ReservationApi(config['hotel']['url'],
                                            config['hotel']['key'],
                                            int(config['global']['retries']),
                                            float(config['global']['delay']))

        # Create an API object to communicate with the band API
        self.band   = reservationapi.ReservationApi(config['band']['url'],
                                            config['band']['key'],
                                            int(config['global']['retries']),
                                            float(config['global']['delay']))
        
        self.data_cache = dict()
        
    
    def set_menu_state(self, state: MenuState):
        ''' Used to change what state the booking system is in. 
        
        Args:
            state(MenuState): The state in which the system should be transitioned to
        '''
        self.state = state
        # ----------------- TITLE -----------------
        Menu._reset_stdout()
        print()
    
    def start(self):
        ''' Mainloop for the Booking System. '''
        do_mainloop = True
        self.set_menu_state(MenuState.HOME)

        while do_mainloop:

            if self.state == MenuState.HOME:
                self.set_menu_state(MenuHome(self.hotel, self.band).load())
    
            # --------- MENU OPTION 1 ---------
            elif self.state == MenuState.VIEW_CURRENT_HOTEL_BAND_SLOTS:
                self.set_menu_state(MenuHeldHotelsAndBands(self.hotel, self.band).load())

            # --------- MENU OPTION 2 ---------
            elif self.state == MenuState.VIEW_20_AVAILABLE_SLOTS:
                self.set_menu_state(Menu20AvailableHotelsAndBands(self.hotel, self.band).load())

            # --------- MENU OPTION 3 ---------
            elif self.state == MenuState.BOOK_SLOT:
                self.set_menu_state(MenuBookedSlots(self.hotel, self.band).load())
                                
            # --------- MENU OPTION 4 ---------
            elif self.state == MenuState.CANCEL_HELD_SLOT:
                self.set_menu_state(MenuCancelSlot(self.hotel, self.band).load())

            # --------- MENU OPTION 5 ---------
            elif self.state == MenuState.VIEW_5_UPCOMING_SLOTS:
                self.set_menu_state(MenuUpcoming5Slots(self.hotel, self.band).load())

            # --------- MENU OPTION 6 ---------
            elif self.state == MenuState.RESERVE_EARLIEST_SLOT:
                self.set_menu_state(MenuReserveEarliestSlot(self.hotel, self.band).load())

            # --------- MENU OPTION 7 ---------
            elif self.state == MenuState.CANCEL_UNNEEDED_RESERVATION:
                self.set_menu_state(MenuCancelUnneededReservations(self.hotel, self.band).load())

            # --------- MENU OPTION 8 ---------
            elif self.state == MenuState.QUIT:
                do_mainloop = False

if __name__ == "__main__":
    booking_system = BookingSystem()
    booking_system.start()
