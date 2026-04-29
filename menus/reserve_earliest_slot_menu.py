from .menu import (Menu, MenuState)
import reservationapi
from concurrent.futures import ThreadPoolExecutor

class MenuReserveEarliestSlot(Menu):
    def __init__(self, hotel: reservationapi.ReservationApi, band: reservationapi.ReservationApi):
        super().__init__(hotel, band)

    def load(self):
        ''' Menu function for booking a slot '''
        Menu._print_title("Book the Earliest Slot")

        # try call api and handle any errors that might come with that
        try:
            print("Fetching booking data...")
            # stores the bookings held by the user
            hotel_data, band_data = self.get_slots_held()

            # used to check if we have bookings that could be possible matches
            # stores the bookings that the user has which dont have matches
            hotels_unmatched, bands_unmatched = self.get_unmatched_held_bookings(hotel_data, band_data)
            
            # used to check if we already have the earliest slot
            # stores the matched slots held by the user
            held_matching = self.matchup_slots(hotel_data, band_data)

            # the current matches available exluding our own
            # this is used to test if we already have the best pair
            available_excluding_held = self.get_matching_available_slots(1, None, None, False)

            # includes our bookings
            # stores the most earliest booking available to the user
            data = self.get_matching_available_slots(1, hotels_unmatched, bands_unmatched, False)

            # slot id (excluding our bookings)
            slot_id_potential = int(available_excluding_held[0].get("id"))
            
            # slot id (including our bookings)
            slot_id = int(data[0].get("id"))

            # check for if the user already has the most earliest booking
            if len(held_matching) != 0 and int(held_matching[0].get("id")) < slot_id_potential:
                print(f"\n\033[92mYou already have the lowest available matching slot (Slot {held_matching[0].get("id")}).\033[0m")
                input("Press Enter to return to the home menu...")
                return MenuState.HOME
            
            # if we have:  2 | 2  bookings
            if len(hotel_data) >= self.hotel.max_bookings_count and len(band_data) >= self.band.max_bookings_count:
                print("\033[95mThe maximum number of hotel and band bookings has been made.")
                option = self.poll_yes_no("Would you like to cancel a booking? (Yes/No): \033[0m")
                if option == "no":
                    input("Press Enter to return to the home menu...")
                    return MenuState.HOME
                else:
                    Menu.callback = MenuState.RESERVE_EARLIEST_SLOT
                    return MenuState.CANCEL_HELD_SLOT
    
             # if we have 2 hotel bookings
            elif len(hotel_data) >= self.hotel.max_bookings_count:
                print("\033[95mThe maximum number of hotel bookings have been made.")
                option = self.poll_yes_no("Would you like to cancel a booking? (Yes/No): \033[0m")
                if option == "no":
                    input("Press Enter to return to the home menu...")
                    return MenuState.HOME
                else:
                    Menu.callback = MenuState.RESERVE_EARLIEST_SLOT
                    return MenuState.CANCEL_HELD_SLOT
            
            # if we have 2 band bookings
            elif len(band_data) >= self.band.max_bookings_count:
                print("\033[95mThe maximum number of band bookings have been made.")
                option = self.poll_yes_no("Would you like to cancel a booking? (Yes/No): \033[0m")
                if option == "no":
                    input("Press Enter to return to the home menu...")
                    return MenuState.HOME
                else:
                    Menu.callback = MenuState.RESERVE_EARLIEST_SLOT
                    return MenuState.CANCEL_HELD_SLOT
            
            # data null check
            if data == None or data == []:
                print("\033[95mNo available slots are remaining\033[0m")
                print()
                input("Press Enter to return to the home menu...")
                return MenuState.HOME

            print()
            print(f"The earliest available slot is \033[95mSlot {slot_id}\033[0m")
    
            # --- BOOKING LOGIC ---
            option = self.poll_yes_no("Would you like to book this slot (Yes/No): ")            
            if option == "no":
                input("Press Enter to return to the home menu...")
                return MenuState.HOME
            
            print()
            print("Attempting to book slot...")
            
            try:
                # send a booking request for the earliest booking
                # this includes our currently held bookings
                self.book_matching_slot(slot_id, hotel_data, band_data)
                print(f"\033[32mSUCCESS:\033[0m Slot {slot_id} has been reserved successfully.")
                print()
                print("Checking for earlier booking...")

                # try once to book an earlier slot
                try:
                    def cancel(id, data, api):
                        '''Helper function to cancel unneeded slots'''
                        for x in data:
                            if int(x.get("id")) != id:
                                api.release_slot(x.get("id"))

                        return data

                    # check to see if an earlier slot is open on the api (bypass cache)
                    attempt = self.get_matching_available_slots(1, None, None, True)

                    # if the above is true, then we need to attempt to book it
                    if len(attempt) > 0 and int(attempt[0].get("id")) < slot_id:
                        
                        # the id of the most early booking
                        new_id = int(attempt[0].get("id"))
                        print()
                        print(f"An earlier booking has been found (Slot {new_id}).")

                        # if we're at capacity, then need to remove the later bookings (safety for the most up-to-date booking)   
                        # eliminate the bookings in parallel
                        with ThreadPoolExecutor() as executor:
                            t1 = executor.submit(cancel, slot_id, hotel_data, self.hotel)
                            t2 = executor.submit(cancel, slot_id, band_data, self.band)
                            hotel_data = t1.result()
                            band_data = t2.result()    
                        
                        print(f"Attempting to book Slot {new_id}...")
                        self.book_matching_slot(new_id)    # book earlier slot
                        self.cancel_matching_slot(slot_id) # remove earlier slot 
                        slot_id = new_id                   # runs if the newer booking was successful
                        print(f"\033[32mSUCCESS:\033[0m Slot {slot_id} has been reserved successfully.")
                    else:
                        print(f"No earlier booking was found.")

                    print()
                    print("Running Cleanup...")
                    # clean up every booking EXCEPT the one we've just made
                    with ThreadPoolExecutor() as executor:
                        t1 = executor.submit(cancel, slot_id, hotel_data, self.hotel)
                        t2 = executor.submit(cancel, slot_id, band_data, self.band)
                        t1.result()
                        t2.result()

                    print("Cleanup successfully ran.")

                except Exception as e:
                    raise e
            except Exception as e:
                print("Failed to book the requested slot. Please return to the main menu and try again.")
                raise e
            
            print()
            input("Press Enter to return to the home menu...")
            return MenuState.HOME
        except Exception as e:
            print(f"An error occurred while performing the request: {e}")
            input("Press Enter to return to the home menu...")
            return MenuState.HOME
