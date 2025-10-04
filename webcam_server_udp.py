import cv2
import socket
import struct
import threading
import time
import math

class WebcamServerUDP:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = set()  # Set untuk menyimpan alamat client
        self.cap = None
        self.running = False
        self.sequence_number = 0
        self.max_packet_size = 60000  # ~60KB per packet (aman untuk UDP)
        
    def start_server(self):
        """Memulai server UDP"""
        try:
            # Buat UDP socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            print(f"🚀 UDP Server dimulai di {self.host}:{self.port}")
            
            # Inisialisasi webcam
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ Error: Tidak dapat mengakses webcam")
                return
                
            # Set resolusi webcam
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            # Set FPS untuk performa lebih baik
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.running = True
            
            # Thread untuk menerima registrasi client
            listen_thread = threading.Thread(target=self.listen_for_clients)
            listen_thread.start()
            
            # Thread untuk mengirim frame webcam
            stream_thread = threading.Thread(target=self.stream_webcam)
            stream_thread.start()
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
    
    def listen_for_clients(self):
        """Mendengarkan pesan dari client untuk registrasi"""
        self.server_socket.settimeout(1.0)  # Timeout 1 detik
        
        while self.running:
            try:
                data, addr = self.server_socket.recvfrom(1024)
                message = data.decode('utf-8')
                
                if message == "REGISTER":
                    if addr not in self.clients:
                        self.clients.add(addr)
                        print(f"✅ Client terdaftar: {addr}")
                        print(f"📊 Total clients: {len(self.clients)}")
                        
                        # Kirim konfirmasi ke client
                        response = "REGISTERED"
                        self.server_socket.sendto(response.encode('utf-8'), addr)
                
                elif message == "UNREGISTER":
                    if addr in self.clients:
                        self.clients.remove(addr)
                        print(f"❌ Client tidak terdaftar: {addr}")
                        print(f"📊 Total clients: {len(self.clients)}")
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"⚠️  Error listening for clients: {e}")
    
    def stream_webcam(self):
        """Mengirim frame webcam ke semua client"""
        while self.running:
            try:
                # Skip jika tidak ada client
                if len(self.clients) == 0:
                    time.sleep(0.1)
                    continue
                
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Error: Tidak dapat membaca frame dari webcam")
                    break
                
                # Encode frame ke JPEG dengan quality yang optimal
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
                
                if result:
                    # Kirim frame ke semua client yang terdaftar
                    frame_data = encoded_img.tobytes()
                    self.send_frame_to_clients(frame_data)
                
                # Kontrol frame rate (~30 FPS)
                time.sleep(0.033)
                
            except Exception as e:
                print(f"❌ Error streaming: {e}")
                break
    
    def send_frame_to_clients(self, frame_data):
        """Mengirim frame data ke semua client dengan fragmentasi"""
        if not frame_data or len(self.clients) == 0:
            return
        
        self.sequence_number = (self.sequence_number + 1) % 65536
        frame_size = len(frame_data)
        
        # Hitung jumlah packet yang dibutuhkan
        header_size = 12  # 4 bytes seq + 4 bytes total_packets + 4 bytes packet_index
        payload_size = self.max_packet_size - header_size
        total_packets = math.ceil(frame_size / payload_size)
        
        clients_to_remove = set()
        
        for client_addr in self.clients.copy():
            try:
                # Kirim setiap fragment
                for packet_index in range(total_packets):
                    start_pos = packet_index * payload_size
                    end_pos = min(start_pos + payload_size, frame_size)
                    packet_data = frame_data[start_pos:end_pos]
                    
                    # Buat header packet
                    # Format: [sequence_number:4][total_packets:4][packet_index:4][data...]
                    header = struct.pack("!III", self.sequence_number, total_packets, packet_index)
                    udp_packet = header + packet_data
                    
                    # Kirim packet
                    self.server_socket.sendto(udp_packet, client_addr)
                
                # Debug info untuk frame pertama setiap detik
                if self.sequence_number % 30 == 1:
                    print(f"📤 Sent frame {self.sequence_number}: {frame_size} bytes in {total_packets} packets to {len(self.clients)} clients")
                
            except Exception as e:
                print(f"❌ Error sending to {client_addr}: {e}")
                clients_to_remove.add(client_addr)
        
        # Hapus client yang bermasalah
        for client_addr in clients_to_remove:
            if client_addr in self.clients:
                self.clients.remove(client_addr)
                print(f"❌ Removed problematic client: {client_addr}")
    
    def stop_server(self):
        """Menghentikan server"""
        print("⏹️  Stopping server...")
        self.running = False
        
        # Beri tahu semua client bahwa server akan shutdown
        for client_addr in self.clients.copy():
            try:
                shutdown_msg = "SERVER_SHUTDOWN"
                self.server_socket.sendto(shutdown_msg.encode('utf-8'), client_addr)
            except:
                pass
        
        self.clients.clear()
        
        # Tutup server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Tutup webcam
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        print("✅ Server dihentikan")

if __name__ == "__main__":
    server = WebcamServerUDP()
    
    try:
        server.start_server()
        print("📺 Server berjalan! Client dapat bergabung dengan mengirim 'REGISTER'")
        print("⌨️  Tekan Ctrl+C untuk menghentikan server")
        while server.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Menghentikan server...")
        server.stop_server()