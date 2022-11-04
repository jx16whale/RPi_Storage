import os

from commServers.multiprocessing import MultiProcessing
from commServers.multiprocessing2 import MultiProcessing2
from commServers.multiprocessing3 import MultiProcessing3
from commServers.multiprocessing4 import MultiProcessing4
from commServers.multiprocessing5 import MultiProcessing5

from commServers.config import BASE_IP, IMAGE_PORT

def init():
    multi_process = None
    os.system("sudo chmod o+rw /var/run/sdp")
    os.system("sudo hciconfig hci0 piscan")

    while True:
        try:
            print(f"Please enter your choice, \n1: Task 1, \n2: Task 2 (Safe), \n3: Task 2 (Take & Process Continuous), \n4: Task 2 (Take immediately & repeat if fail), \n5: Task 2 (Take Immediately)")
            choice = input()
            if choice == '1':
                multi_process = MultiProcessing(
                    image_processing_server= f'{BASE_IP[0]}{IMAGE_PORT}', 
                    android_on=True, 
                    stm_on=True,
                    algo_on=True, 
                    )
                multi_process.start()
                       
            # Task 1
            elif choice == '2':
                multi_process = MultiProcessing2(
                    image_processing_server=f'{BASE_IP[0]}{IMAGE_PORT}', 
                    android_on = True,
                    stm_on=True
                    )
                multi_process.start()

            
            elif choice == '3':
                multi_process = MultiProcessing3(
                    image_processing_server=f'{BASE_IP[0]}{IMAGE_PORT}', 
                    android_on = True,
                    stm_on=True
                    )
                multi_process.start()
            elif choice == '4':
                multi_process = MultiProcessing4(
                    image_processing_server=f'{BASE_IP[0]}{IMAGE_PORT}', 
                    android_on = True,
                    stm_on=True
                    )
                multi_process.start()
            elif choice == '5':
                multi_process = MultiProcessing5(
                    image_processing_server=f'{BASE_IP[0]}{IMAGE_PORT}', 
                    android_on = True,
                    stm_on=True
                    )
                multi_process.start()

            else:
                print(f"Wrong Choice. Try again!")
                continue
        
        except Exception as error:
            print(f"[MAIN] Error have occurred:")
            if multi_process is not None:
                multi_process.end()
            raise error


if __name__ == "__main__":
    init()