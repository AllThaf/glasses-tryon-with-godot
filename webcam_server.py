import cv2
import socket
import struct
import threading
import time

class WebcamServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.cap = None
        self.running = False
        
    def start_server(self):
        """Memulai server TCP"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Server dimulai di {self.host}:{self.port}")
            
            # Inisialisasi webcam
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Error: Tidak dapat mengakses webcam")
                return
                
            # Set resolusi webcam
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.running = True
            
            # Thread untuk menerima koneksi client
            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.start()
            
            # Thread untuk mengirim frame webcam
            stream_thread = threading.Thread(target=self.stream_webcam)
            stream_thread.start()
            
        except Exception as e:
            print(f"Error starting server: {e}")
    
    def accept_clients(self):
        """Menerima koneksi dari client"""
        while self.running:
            try:
                print("Menunggu koneksi client...")
                client_socket, address = self.server_socket.accept()
                print(f"✅ Client terhubung dari {address}")
                
                # Set socket options untuk mencegah error
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
                self.clients.append(client_socket)
                print(f"Total clients terhubung: {len(self.clients)}")
                
                # Beri waktu client untuk siap
                time.sleep(0.1)
                
            except Exception as e:
                if self.running:
                    print(f"❌ Error accepting client: {e}")
                break
    
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
                    print("Error: Tidak dapat membaca frame dari webcam")
                    break
                
                # Encode frame ke JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]  # Kurangi quality untuk performa
                result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
                
                if result:
                    # Kirim frame ke semua client yang terhubung
                    data = encoded_img.tobytes()
                    self.send_to_clients(data)
                
                # Tidak tampilkan preview di server (kirim ke client saja)
                # cv2.imshow('Webcam Server', frame)  # Dimatikan
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
                    
                time.sleep(0.033)  # ~30 FPS, lebih stabil
                
            except Exception as e:
                print(f"Error streaming: {e}")
                break
    
    def send_to_clients(self, data):
        """Mengirim data ke semua client"""
        if not data or len(self.clients) == 0:
            return
            
        # Header berisi ukuran data
        data_size = len(data)
        
        clients_to_remove = []
        
        for client in self.clients:
            try:
                # Check if socket is still connected
                client.settimeout(0.1)  # 100ms timeout
                
                # Kirim ukuran data terlebih dahulu (4 bytes)
                client.send(struct.pack("!I", data_size))
                
                # Kirim data frame
                bytes_sent = 0
                while bytes_sent < len(data):
                    sent = client.send(data[bytes_sent:])
                    if sent == 0:
                        raise socket.error("Socket connection broken")
                    bytes_sent += sent
                
                # Reset timeout
                client.settimeout(None)
                
                # print(f"✅ Sent {data_size} bytes to client")  # Debug
                
            except socket.timeout:
                print("⚠️  Client timeout - removing client")
                clients_to_remove.append(client)
            except socket.error as e:
                print(f"❌ Socket error with client: {e}")
                clients_to_remove.append(client)
            except Exception as e:
                print(f"❌ Error sending to client: {e}")
                clients_to_remove.append(client)
        
        # Hapus client yang terputus
        for client in clients_to_remove:
            if client in self.clients:
                self.clients.remove(client)
                try:
                    client.close()
                except:
                    pass
                print(f"Client disconnected. Remaining: {len(self.clients)}")
    
    def stop_server(self):
        """Menghentikan server"""
        self.running = False
        
        # Tutup semua koneksi client
        for client in self.clients:
            client.close()
        self.clients.clear()
        
        # Tutup server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Tutup webcam
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        print("Server dihentikan")

if __name__ == "__main__":
    server = WebcamServer()
    
    try:
        server.start_server()
        print("Tekan Ctrl+C untuk menghentikan server")
        while server.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nMenghentikan server...")
        server.stop_server()