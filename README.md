# Proyek Uji Coba Kacamata (*Glasses Try-On*): Implementasi Streaming Webcam Real-Time (UDP)

Proyek ini menghadirkan aplikasi uji coba kacamata virtual *real-time* dengan memanfaatkan protokol **UDP (User Datagram Protocol)** untuk transmisi video berkecepatan tinggi, diimplementasikan menggunakan **Python (OpenCV)** sebagai *server* dan **Godot Engine** sebagai *client*.

## 📁 Struktur File

```
├── webcam_server_udp.py    # Server Python: Streaming webcam + deteksi wajah & try-on kacamata.
├── godot_project/
│   ├── Scenes/
│   │   ├── main_menu.tscn      # Menu utama untuk memilih kacamata.
│   │   └── webcam_client_udp.tscn # Scene klien UDP utama untuk menampilkan video.
│   ├── Scripts/
│   │   ├── main_menu.gd        # Logika Godot: Mengirim pilihan kacamata ke server via UDP.
│   │   └── webcam_client_udp.gd # Logika Godot: Menerima, menyusun ulang paket, dan menampilkan video.
│   └── Glasses/
│       ├── glasses1.png, glasses2.png, ... # Aset gambar kacamata.
└── README.md
```

-----

## 🚀 Panduan Memulai Cepat

### 1\. Memulai Server (Python)

*Server* ini menggunakan Python dan *library* **OpenCV** untuk mengakses *webcam*, mendeteksi wajah, dan memproses *overlay* kacamata.

```bash
python webcam_server_udp.py
```

Setelah dijalankan, *server* akan beroperasi pada `127.0.0.1:8888` dan siap menerima koneksi *client* UDP.

### 2\. Menjalankan Klien (Godot Engine)

1.  Buka proyek `godot_project/` di Godot Engine.
2.  Jalankan *scene* utama (`main_menu.tscn`).
3.  Pilih salah satu tombol **"Kacamata X"**.
      * Pemilihan kacamata akan mengirimkan pesan `SET_GLASSES:` melalui UDP ke *server* untuk mengubah kacamata yang di-*overlay* secara *real-time*.
4.  Di *scene* klien UDP, tekan **"Connect to Server"**.
      * *Client* akan mengirim pesan `REGISTER` ke *server* dan mulai menerima *stream* video.

-----

## ⚙️ Fitur dan Implementasi Teknis UDP

Proyek ini mengimplementasikan *real-time streaming* video menggunakan UDP karena protokol ini menawarkan **latensi rendah** dan sangat cocok untuk transmisi data yang memprioritaskan kecepatan dibandingkan keandalan mutlak.

### Server UDP (`webcam_server_udp.py`)

  * **Deteksi Wajah dan Mata:** Menggunakan model **Haar Cascades** dari OpenCV (`haarcascade_frontalface_default.xml` dan `haarcascade_eye.xml`) untuk mengidentifikasi area wajah dan mata.
  * **Overlay Kacamata *Real-time*:** Menghitung skala dan rotasi kacamata berdasarkan posisi mata untuk menghasilkan *overlay* yang akurat.
  * **Fragmentasi Paket (Packet Fragmentation):** Frame video di-*encode* ke JPEG (kualitas 50) dan dipecah menjadi fragmen-fragmen dengan ukuran maksimum `60000 bytes` untuk mematuhi batas paket UDP, memungkinkan transmisi *frame* berukuran besar.
  * **Pengiriman Fragmen Serial:** Setiap paket dikirim dengan *header* **12 *byte*** yang berisi **nomor urut *frame***, **jumlah total paket**, dan **indeks paket** (`!III`), yang penting untuk rekonstruksi *frame* yang benar di sisi *client*.

### Klien UDP (`webcam_client_udp.gd`)

  * ***Frame Reassembly***: Menerima fragmen-fragmen UDP, menyimpannya dalam *buffer* (`frame_buffers`), dan menyusunnya kembali menjadi satu *frame* video lengkap berdasarkan nomor urut.
  * **Penanganan *Frame Timeout***: *Frame* yang tidak lengkap (*missing packets*) akan dihapus dari *buffer* setelah *timeout* **1,0 detik** untuk menjaga *client* tetap sinkron dengan *stream* *real-time*.
  * **Pemantauan Performa:** Menampilkan metrik utama *real-time*, termasuk **FPS (Frame per Second)**, **Data Rate (KB/s)**, dan **Drop Rate (persentase *frame* yang hilang)**.
  * **Proses *Client***: Proses penerimaan paket, penyusunan *frame*  , dan pembersihan *frame* lama dilakukan di dalam fungsi `_process(delta)` Godot.
