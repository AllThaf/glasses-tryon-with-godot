#!/usr/bin/env python3
"""
Comparison test untuk TCP vs UDP webcam streaming
"""

import time
import os

def show_comparison():
    """Tampilkan perbandingan TCP vs UDP"""
    print("🎥 WEBCAM STREAMING: TCP vs UDP COMPARISON")
    print("=" * 70)
    
    comparison_data = [
        ["Aspect", "TCP", "UDP"],
        ["-" * 20, "-" * 25, "-" * 25],
        ["Connection", "Connection-oriented", "Connectionless"],
        ["Handshake", "3-way handshake required", "No handshake"],
        ["Reliability", "Guaranteed delivery", "Best effort"],
        ["Speed", "Slower (overhead)", "Faster (minimal overhead)"],
        ["Latency", "Higher", "Lower"],
        ["Packet Loss", "Automatic retransmission", "No retransmission"],
        ["Buffer", "Large buffers", "Small buffers"],
        ["Real-time", "Not ideal", "Excellent"],
        ["Use Case", "File transfer, HTTP", "Video/Audio streaming"],
    ]
    
    for row in comparison_data:
        print(f"{row[0]:<20} | {row[1]:<25} | {row[2]:<25}")
    
    print("\n🎯 RECOMMENDATION for Video Streaming:")
    print("   ✅ UDP is BETTER for:")
    print("      - Real-time video streaming")
    print("      - Lower latency requirements")
    print("      - Can tolerate some packet loss")
    print("      - Live webcam feeds")
    
    print("\n   ❌ TCP might cause:")
    print("      - Higher latency due to acknowledgments")
    print("      - Buffering delays")
    print("      - Connection overhead")
    print("      - Not suitable for real-time streaming")

def main():
    # Check if both server files exist
    tcp_exists = os.path.exists("webcam_server.py")
    udp_exists = os.path.exists("webcam_server_udp.py")
    
    print("📁 File Check:")
    print(f"   TCP Server: {'✅ Found' if tcp_exists else '❌ Missing'}")
    print(f"   UDP Server: {'✅ Found' if udp_exists else '❌ Missing'}")
    
    show_comparison()
    
    print("\n📋 NEXT STEPS:")
    print("1. Run 'python webcam_server_udp.py' for UDP server")
    print("2. Open Godot and run 'webcam_client_udp.tscn'")
    print("3. Compare with TCP version for latency and smoothness")
    
    print("\n💡 EXPECTED IMPROVEMENTS with UDP:")
    print("   - Faster connection establishment")
    print("   - Lower video latency")
    print("   - Smoother playback")
    print("   - Better real-time performance")

if __name__ == "__main__":
    main()