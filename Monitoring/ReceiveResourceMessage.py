import socket
import threading
import re
from datetime import datetime

# 클라이언트 리소스 정보를 저장하는 딕셔너리
client_resources = {}

def parse_resource_message(message):
        """리소스 메시지를 파싱하여 딕셔너리로 반환"""
        try:
                # [2025-01-01 12:00:00] CPU: 25.5%, Memory: 1500MB, Network: 100.50 KB, Storage: 50G
                cpu_match = re.search(r'CPU:\s*([0-9.]+)%', message)
                memory_match = re.search(r'Memory:\s*([0-9]+)MB', message)
                network_match = re.search(r'Network:\s*([0-9.]+)\s*KB', message)
                storage_match = re.search(r'Storage:\s*([0-9]+)G', message)
                
                cpu = float(cpu_match.group(1)) if cpu_match else 0
                memory = int(memory_match.group(1)) if memory_match else 0
                network = float(network_match.group(1)) if network_match else 0
                storage = int(storage_match.group(1)) if storage_match else 0
                
                return {
                        'cpu': cpu,
                        'memory': memory,
                        'network': network,
                        'storage': storage,
                        'timestamp': datetime.now()
                }
        except Exception as e:
                print(f"파싱 에러: {e}")
                return None

def calculate_available_resources(resource_info):
        """남은 리소스량 계산 (점수가 높을수록 여유가 많음)"""
        # CPU: 사용률이 낮을수록 좋음 (100 - 사용률)
        # Memory: 사용량이 적을수록 좋음 (가정: 전체 메모리 대비)
        cpu_score = 100 - resource_info['cpu']
        
        # 간단한 점수 계산: CPU가 가장 중요한 요소
        # 메모리 사용량은 상대적으로 덜 중요하게 가중치 적용
        total_score = cpu_score * 0.7 + (10000 - resource_info['memory']) / 100 * 0.3
        
        return total_score

def get_best_client():
        """가장 여유있는 클라이언트를 선택"""
        if not client_resources:
                return None
        
        best_client = None
        best_score = -1
        
        for client_ip, info in client_resources.items():
                score = calculate_available_resources(info)
                if score > best_score:
                        best_score = score
                        best_client = client_ip
        
        return best_client, best_score

def send_task_to_client(client_ip, task_command, task_port=9998):
        """선택된 클라이언트에게 작업 전송"""
        try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(5)
                client_socket.connect((client_ip, task_port))
                client_socket.send(task_command.encode('utf-8'))
                response = client_socket.recv(1024).decode('utf-8')
                client_socket.close()
                print(f"✓ 작업 전송 완료: {client_ip} - 응답: {response}")
                return True
        except Exception as e:
                print(f"✗ 작업 전송 실패 ({client_ip}): {e}")
                return False

def show_client_status():
        """현재 클라이언트 상태 출력"""
        print("\n" + "="*80)
        print("현재 연결된 클라이언트 리소스 현황")
        print("="*80)
        
        if not client_resources:
                print("연결된 클라이언트가 없습니다.")
        else:
                for client_ip, info in sorted(client_resources.items()):
                        score = calculate_available_resources(info)
                        time_str = info['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{client_ip}] (점수: {score:.1f})")
                        print(f"  CPU: {info['cpu']}%, Memory: {info['memory']}MB, "
                              f"Network: {info['network']}KB, Storage: {info['storage']}G")
                        print(f"  최종 업데이트: {time_str}")
                        print()
        print("="*80 + "\n")

def command_handler():
        """사용자 명령어를 처리하는 스레드"""
        print("\n명령어:")
        print("  'task' - 가장 여유있는 클라이언트에게 YouTube 열기 작업 할당")
        print("  'status' - 클라이언트 상태 확인")
        print("  'quit' - 서버 종료\n")
        
        while True:
                try:
                        cmd = input("명령어 입력> ").strip().lower()
                        
                        if cmd == 'task':
                                result = get_best_client()
                                if result:
                                        best_client, score = result
                                        print(f"\n가장 여유있는 클라이언트: {best_client} (점수: {score:.1f})")
                                        print(f"작업 전송 중: YouTube 웹페이지 열기...")
                                        send_task_to_client(best_client, "OPEN_YOUTUBE")
                                else:
                                        print("\n사용 가능한 클라이언트가 없습니다.")
                        
                        elif cmd == 'status':
                                show_client_status()
                        
                        elif cmd == 'quit':
                                print("\n서버를 종료합니다...")
                                import os
                                os._exit(0)
                        
                        else:
                                print("알 수 없는 명령어입니다. (task, status, quit)")
                
                except EOFError:
                        break
                except Exception as e:
                        print(f"명령 처리 오류: {e}")

def start_server(port=9999):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)

        print(f"Server Start... Port : {port}")
        print("Waiting Messages...\n")
        
        # 명령어 처리 스레드 시작
        cmd_thread = threading.Thread(target=command_handler, daemon=True)
        cmd_thread.start()

        while True:
                try:
                        client_socket, addr = server_socket.accept()
                        message = client_socket.recv(1024).decode('utf-8')
                        print(f"[{addr[0]}] {message}")
                        
                        # 리소스 정보 파싱 및 저장
                        resource_info = parse_resource_message(message)
                        if resource_info:
                                client_resources[addr[0]] = resource_info

                        client_socket.send("OK".encode('utf-8'))
                        client_socket.close()

                except KeyboardInterrupt:
                        print("\nServer stop...")
                        break
                except Exception as e:
                        print(f"Error : {e}")

        server_socket.close()

if __name__ == '__main__':
        import sys
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 9999
        start_server(port)