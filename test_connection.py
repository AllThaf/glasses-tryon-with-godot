import socket
import time

def test_server_connection():
    """Test koneksi ke webcam server"""
    try:
        # Buat socket client
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)  # 5 detik timeout
        
        print("Mencoba koneksi ke localhost:8888...")
        
        # Coba connect
        result = client_socket.connect_ex(('localhost', 8888))
        
        if result == 0:
            print("✅ BERHASIL! Server dapat dijangkau")
            print("Server status: ONLINE")
            
            # Test terima data
            print("Menunggu data dari server...")
            try:
                data = client_socket.recv(1024)
                if data:
                    print(f"✅ Data diterima: {len(data)} bytes")
                else:
                    print("⚠️  Tidak ada data diterima")
            except socket.timeout:
                print("⚠️  Timeout saat menunggu data")
                
        else:
            print(f"❌ GAGAL! Error code: {result}")
            print("Kemungkinan penyebab:")
            print("- Server Python belum dijalankan")
            print("- Port 8888 sedang digunakan aplikasi lain")
            print("- Firewall memblokir koneksi")
            
        client_socket.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_port_usage():
    """Cek apakah port 8888 sedang digunakan"""
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(1)
        result = test_socket.connect_ex(('localhost', 8888))
        test_socket.close()
        
        if result == 0:
            print("🔍 Port 8888: SEDANG DIGUNAKAN")
            return True
        else:
            print("🔍 Port 8888: TERSEDIA")
            return False
    except:
        print("🔍 Port 8888: TIDAK DAPAT DICEK")
        return False

if __name__ == "__main__":
    print("=== TEST KONEKSI WEBCAM SERVER ===\n")
    
    # Cek port dulu
    port_used = check_port_usage()
    print()
    
    if port_used:
        # Test koneksi
        test_server_connection()
    else:
        print("❌ Server tidak berjalan!")
        print("Pastikan 'python webcam_server.py' sudah dijalankan")
    
    print("\n=== SELESAI ===")
    input("Tekan Enter untuk keluar...")