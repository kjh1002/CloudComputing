import socket
import subprocess
import time
import threading
import webbrowser
from datetime import datetime

def get_cpu_usage():
	try:
		# mpstat 사용 (더 안정적)
		cmd = "mpstat 1 1 | awk 'NR==4{print 100-$NF}'"
		result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
		cpu_value = result.stdout.strip()
		if cpu_value:
			return f"{float(cpu_value):.1f}%"
	except:
		pass
	
	try:
		# top 명령어 개선
		cmd = "top -bn2 -d 0.5 | grep '^%Cpu' | tail -1 | awk '{print $2}' | cut -d'%' -f1"
		result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
		cpu_value = result.stdout.strip()
		if cpu_value:
			return cpu_value + "%"
	except:
		pass
	
	# 모두 실패하면 0% 반환
	return "0%"

def get_memory_usage():
        cmd = "free -m | awk 'NR==2{print $3}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip() + "MB"

def get_network_usage():
        cmd = "cat /proc/net/dev | grep 'eth0\\|ens' | awk '{print ($2+$10)/1024}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
        if output:
                return f"{float(output):.2f} KB"
        return "0 KB"

def get_storage_usage():
        cmd = "df -BG | awk 'NR==2{print $3}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()

def save_to_file(cpu, memory, network, storage):
        with open('system_resources.txt', 'w') as f:
                f.write(f"CPU : {cpu}\n")
                f.write(f"Memory : {memory}\n")
                f.write(f"Network : {network}\n")
                f.write(f"Storage : {storage}\n")

def read_from_file():
        with open('system_resources.txt', 'r') as f:
                lines = f.readlines()

        cpu = lines[0].split(' : ')[1].strip()
        memory = lines[1].split(' : ')[1].strip()
        network = lines[2].split(' : ')[1].strip()
        storage = lines[3].split(' : ')[1].strip()

        return cpu, memory, network, storage

def send_to_server(message, server_ip, server_port):
        try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((server_ip, server_port))
                client_socket.send(message.encode('utf-8'))
                response = client_socket.recv(1024).decode('utf-8')
                client_socket.close()
                print(f"Send Complete : {message}")
        except Exception as e:
                print(f"Send Fail : {e}")

def execute_task(task_command):
        """작업 명령을 실행"""
        try:
                if task_command == "OPEN_YOUTUBE":
                        print("\n★ 작업 수신: YouTube 웹페이지 열기")
                        
                        # Linux 환경에서 브라우저 열기
                        import platform
                        import os
                        
                        url = 'https://www.youtube.com'
                        system = platform.system()
                        
                        try:
                                if system == "Linux":
                                        # Linux에서는 여러 방법 시도
                                        # 1. xdg-open 시도 (가장 범용적)
                                        result = subprocess.run(['xdg-open', url], 
                                                              capture_output=True, 
                                                              timeout=5)
                                        if result.returncode == 0:
                                                print(f"✓ xdg-open으로 YouTube 페이지를 열었습니다.\n")
                                                return "SUCCESS"
                                        
                                        # 2. 직접 브라우저 실행 시도
                                        browsers = ['firefox', 'google-chrome', 'chromium-browser', 'chromium']
                                        for browser in browsers:
                                                try:
                                                        subprocess.Popen([browser, url], 
                                                                       stdout=subprocess.DEVNULL, 
                                                                       stderr=subprocess.DEVNULL)
                                                        print(f"✓ {browser}로 YouTube 페이지를 열었습니다.\n")
                                                        return "SUCCESS"
                                                except FileNotFoundError:
                                                        continue
                                        
                                        print("⚠ 사용 가능한 브라우저를 찾을 수 없습니다.")
                                        print("  firefox, google-chrome, chromium-browser 중 하나를 설치해주세요.\n")
                                        return "NO_BROWSER"
                                
                                else:
                                        # Windows/Mac은 webbrowser 사용
                                        webbrowser.open(url)
                                        print("✓ YouTube 페이지를 열었습니다.\n")
                                        return "SUCCESS"
                        
                        except subprocess.TimeoutExpired:
                                print("⚠ 브라우저 실행 시간 초과\n")
                                return "TIMEOUT"
                        except Exception as e:
                                print(f"⚠ 브라우저 열기 실패: {e}\n")
                                return "ERROR"
                
                else:
                        print(f"알 수 없는 작업: {task_command}")
                        return "UNKNOWN_TASK"
        
        except Exception as e:
                print(f"작업 실행 오류: {e}")
                return "ERROR"

def task_listener(port=9998):
        """서버로부터 작업 명령을 받는 리스너"""
        try:
                task_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                task_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                task_socket.bind(('0.0.0.0', port))
                task_socket.listen(1)
                
                print(f"Task Listener Start... Port : {port}\n")
                
                while True:
                        try:
                                client_socket, addr = task_socket.accept()
                                task_command = client_socket.recv(1024).decode('utf-8')
                                
                                # 작업 실행
                                result = execute_task(task_command)
                                
                                # 결과 전송
                                client_socket.send(result.encode('utf-8'))
                                client_socket.close()
                                
                        except Exception as e:
                                print(f"Task Listener Error: {e}")
        except Exception as e:
                print(f"Task Listener 시작 실패: {e}")

def run_slave(server_ip, server_port, interval, task_port=9998):
        print(f"Slave Start - server: {server_ip}:{server_port}, interval: {interval}s")
        
        # 작업 리스너를 백그라운드 스레드로 시작
        listener_thread = threading.Thread(target=task_listener, args=(task_port,), daemon=True)
        listener_thread.start()
        
        print("리소스 모니터링 시작...\n")

        while True:
                try:
                        cpu = get_cpu_usage()
                        memory = get_memory_usage()
                        network = get_network_usage()
                        storage = get_storage_usage()

                        save_to_file(cpu, memory, network, storage)

                        cpu, memory, network, storage = read_from_file()

                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        message = f"[{current_time}] CPU: {cpu}, Memory: {memory}, Network: {network}, Storage: {storage}"
                        send_to_server(message, server_ip, server_port)

                        time.sleep(interval)

                except KeyboardInterrupt:
                        print("\n클라이언트 종료...")
                        break
                except Exception as e:
                        print(f"Error: {e}")
                        time.sleep(interval)


if __name__ == '__main__':
        import sys
        server_ip = '192.168.8.10'
        server_port = 9999
        interval = 10
        run_slave(server_ip, server_port, interval)