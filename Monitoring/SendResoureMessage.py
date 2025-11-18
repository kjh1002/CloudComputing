import socket
import subprocess
import time

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

def run_slave(server_ip, server_port, interval):
        print(f"Slave Start - server: {server_ip}:{server_port}, interval: {interval}s\n")

        while True:
                try:
                        cpu = get_cpu_usage()
                        memory = get_memory_usage()
                        network = get_network_usage()
                        storage = get_storage_usage()

                        save_to_file(cpu, memory, network, storage)

                        cpu, memory, network, storage = read_from_file()

                        message = f"CPU: {cpu}, Memory: {memory}, Network: {network}, Storage: {storage}"
                        send_to_server(message, server_ip, server_port)

                        time.sleep(interval)

                except Exception as e:
                        print(f"Error: {e}")
                        time.sleep(interval)


if __name__ == '__main__':
        import sys
        server_ip = '192.168.8.10'
        server_port = 9999
        interval = 10
        run_slave(server_ip, server_port, interval)