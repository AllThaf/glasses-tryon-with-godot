import cv2
import socket
import struct
import threading
import time
import math
import numpy as np
import os


class WebcamServerUDP:
    def __init__(self, host="localhost", port=8888, glasses_path="glasses.png"):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = set()
        self.cap = None
        self.running = False
        self.sequence_number = 0
        self.max_packet_size = 60000  # ~60KB per packet (aman untuk UDP)

        # Inisialisasi Face Detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

        # Load gambar kacamata dari file
        self.glasses_path = glasses_path
        self.glasses_img = None
        self.load_glasses_image()

    def load_glasses_image(self):
        """Load gambar kacamata dari file"""
        if os.path.exists(self.glasses_path):
            # Load dengan alpha channel
            self.glasses_img = cv2.imread(self.glasses_path, cv2.IMREAD_UNCHANGED)

            if self.glasses_img is not None:
                # Jika gambar tidak punya alpha channel, tambahkan
                if self.glasses_img.shape[2] == 3:
                    # Konversi BGR ke BGRA
                    b, g, r = cv2.split(self.glasses_img)
                    alpha = np.ones(b.shape, dtype=b.dtype) * 255
                    self.glasses_img = cv2.merge((b, g, r, alpha))

                print(f"✅ Gambar kacamata berhasil dimuat dari: {self.glasses_path}")
                print(
                    f"   Ukuran: {self.glasses_img.shape[1]}x{self.glasses_img.shape[0]}"
                )
            else:
                print(f"❌ Error: Gagal membaca file {self.glasses_path}")
                self.create_default_glasses()

    def overlay_glasses(self, frame, face_rect, eyes):
        """Overlay kacamata pada wajah yang terdeteksi"""
        try:
            if len(eyes) < 2:
                return frame

            # Urutkan mata berdasarkan posisi x (kiri ke kanan)
            eyes = sorted(eyes, key=lambda e: e[0])

            # Ambil dua mata pertama
            eye_left = eyes[0]
            eye_right = eyes[1]

            # Hitung pusat mata
            left_eye_center = (
                eye_left[0] + eye_left[2] // 2,
                eye_left[1] + eye_left[3] // 2,
            )
            right_eye_center = (
                eye_right[0] + eye_right[2] // 2,
                eye_right[1] + eye_right[3] // 2,
            )

            # Gambar titik pusat mata untuk debugging
            cv2.circle(frame, left_eye_center, 3, (0, 255, 255), -1)
            cv2.circle(frame, right_eye_center, 3, (0, 255, 255), -1)

            # Hitung jarak antar mata
            eye_distance = np.sqrt(
                (right_eye_center[0] - left_eye_center[0]) ** 2
                + (right_eye_center[1] - left_eye_center[1]) ** 2
            )

            print(f"📏 Jarak mata: {eye_distance:.2f} pixels")

            # Skala kacamata berdasarkan jarak mata (dengan faktor 2.5 untuk ukuran yang pas)
            glasses_width = int(eye_distance * 2.5)
            glasses_height = int(
                glasses_width * self.glasses_img.shape[0] / self.glasses_img.shape[1]
            )

            print(f"🕶️  Ukuran kacamata: {glasses_width}x{glasses_height}")

            # Resize kacamata
            glasses_resized = cv2.resize(
                self.glasses_img, (glasses_width, glasses_height)
            )

            # Hitung sudut rotasi berdasarkan posisi mata
            angle = np.degrees(
                np.arctan2(
                    right_eye_center[1] - left_eye_center[1],
                    right_eye_center[0] - left_eye_center[0],
                )
            )

            # Rotasi kacamata
            center = (glasses_width // 2, glasses_height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            glasses_rotated = cv2.warpAffine(
                glasses_resized,
                rotation_matrix,
                (glasses_width, glasses_height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0, 0),
            )

            # Hitung posisi untuk menempatkan kacamata
            # Posisi x: tengah-tengah antara kedua mata
            glasses_center_x = (left_eye_center[0] + right_eye_center[0]) // 2
            # Posisi y: sedikit di atas mata
            glasses_center_y = (left_eye_center[1] + right_eye_center[1]) // 2 - int(
                glasses_height * 0.1
            )

            # Hitung koordinat top-left untuk overlay
            x1 = glasses_center_x - glasses_width // 2
            y1 = glasses_center_y - glasses_height // 2
            x2 = x1 + glasses_width
            y2 = y1 + glasses_height

            print(f"📍 Posisi kacamata: ({x1}, {y1}) -> ({x2}, {y2})")

            # Pastikan kacamata tidak keluar dari frame
            if x1 >= 0 and y1 >= 0 and x2 <= frame.shape[1] and y2 <= frame.shape[0]:
                # Overlay kacamata dengan alpha blending
                glasses_bgr = glasses_rotated[:, :, :3]
                glasses_alpha = glasses_rotated[:, :, 3] / 255.0

                # Region of Interest
                roi = frame[y1:y2, x1:x2]

                # Blend menggunakan alpha channel
                for c in range(3):
                    roi[:, :, c] = (
                        glasses_alpha * glasses_bgr[:, :, c]
                        + (1 - glasses_alpha) * roi[:, :, c]
                    )

                frame[y1:y2, x1:x2] = roi
                print("✅ Kacamata berhasil diterapkan!")
            else:
                print(f"⚠️  Kacamata di luar frame bounds!")

        except Exception as e:
            print(f"❌ Error dalam overlay_glasses: {e}")
            import traceback

            traceback.print_exc()

        return frame

    def detect_and_apply_glasses(self, frame):
        """Deteksi wajah dan terapkan kacamata"""
        try:
            # Konversi ke grayscale untuk deteksi
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Deteksi wajah dengan parameter yang lebih sensitif
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.05, minNeighbors=3, minSize=(80, 80)
            )

            # Debug: Tampilkan jumlah wajah yang terdeteksi
            if len(faces) > 0:
                print(f"🎯 Terdeteksi {len(faces)} wajah")

            # Untuk setiap wajah yang terdeteksi
            for x, y, w, h in faces:

                # ROI wajah untuk deteksi mata
                roi_gray = gray[y : y + h, x : x + w]

                # Deteksi mata dalam ROI wajah dengan parameter lebih sensitif
                eyes = self.eye_cascade.detectMultiScale(
                    roi_gray, scaleFactor=1.05, minNeighbors=5, minSize=(15, 15)
                )

                print(f"👁️  Terdeteksi {len(eyes)} mata")

                # Sesuaikan koordinat mata relatif terhadap frame penuh
                eyes_adjusted = [(x + ex, y + ey, ew, eh) for (ex, ey, ew, eh) in eyes]

                # Gambar kotak mata untuk debugging
                # for ex, ey, ew, eh in eyes_adjusted:
                #     cv2.rectangle(frame, (ex, ey), (ex + ew, ey + eh), (255, 0, 0), 2)

                # Overlay kacamata
                if len(eyes_adjusted) >= 2:
                    print("🕶️  Menerapkan kacamata...")
                    frame = self.overlay_glasses(frame, (x, y, w, h), eyes_adjusted)
                else:
                    # Tampilkan pesan jika mata tidak cukup terdeteksi
                    cv2.putText(
                        frame,
                        "Need 2 eyes detected",
                        (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        2,
                    )

        except Exception as e:
            print(f"❌ Error dalam detect_and_apply_glasses: {e}")
            import traceback

            traceback.print_exc()

        return frame

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
                message = data.decode("utf-8")

                if message == "REGISTER":
                    if self.cap is None or not self.cap.isOpened():
                        self.cap = cv2.VideoCapture(0)

                    if addr not in self.clients:
                        self.clients.add(addr)
                        print(f"✅ Client terdaftar: {addr}")
                        print(f"📊 Total clients: {len(self.clients)}")

                        # Kirim konfirmasi ke client
                        response = "REGISTERED"
                        self.server_socket.sendto(response.encode("utf-8"), addr)

                elif message == "UNREGISTER":
                    if addr in self.clients:
                        self.clients.remove(addr)
                        print(f"❌ Client tidak terdaftar: {addr}")
                        print(f"📊 Total clients: {len(self.clients)}")
                        self.cap.release()

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"⚠️  Error listening for clients: {e}")
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
                    print("❌ Error: Tidak dapat membaca frame dari webcam")
                    break

                # ========== TERAPKAN DETEKSI WAJAH DAN KACAMATA ==========
                frame = self.detect_and_apply_glasses(frame)
                # =========================================================

                # Encode frame ke JPEG dengan quality yang optimal
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                result, encoded_img = cv2.imencode(".jpg", frame, encode_param)

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
                    header = struct.pack(
                        "!III", self.sequence_number, total_packets, packet_index
                    )
                    udp_packet = header + packet_data

                    # Kirim packet
                    self.server_socket.sendto(udp_packet, client_addr)

                # Debug info untuk frame pertama setiap detik
                if self.sequence_number % 30 == 1:
                    print(
                        f"📤 Sent frame {self.sequence_number}: {frame_size} bytes in {total_packets} packets to {len(self.clients)} clients"
                    )

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
                self.server_socket.sendto(shutdown_msg.encode("utf-8"), client_addr)
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
