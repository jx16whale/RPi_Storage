import os

from commServers.multiprocessing import MultiProcessing


def init():
    multi_process = None
    os.system("sudo hciconfig hci0 piscan")
    print(f"Please enter your choice, 1: Manual, 2: Task 1, 3: Task 2")
    choice = input()
    try:
        # Manual Movement
        if choice == '1':
            multi_process = MultiProcessing(
                image_processing_server=None, 
                android_on=False, 
                stm_on=True,
                algo_on=True, 
                )
            multi_process.start()
        
        elif choice == '2':
            multi_process = MultiProcessing(
                image_processing_server="tcp://192.168.15.25:5555", 
                android_on=False, 
                stm_on=True,
                algo_on=True, 
                )
            multi_process.start()
               
        # Task 1
        elif choice == '3':
            multi_process = MultiProcessing(
                image_processing_server="", 
                android_on=True, 
                stm_on=True,
                algo_on=True, 
                )
            multi_process.start()
            
        # Task 2    
        # else:
        #     multi_process = MultiProcessing(
        #         image_processing_server="", 
        #         android_on=True, 
        #         stm_on=True,
        #         algo_on=True, 
        #         )
        #     multi_process.start()
        
    except Exception as error:
        print(f"[MAIN] Error have occurred: {error}")
        if multi_process is not None:
            multi_process.end()

if __name__ == "__main__":
    init()