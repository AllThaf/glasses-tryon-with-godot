extends Control

@onready var kacamata1_button: Button = $BoxContainer/TextureRect/ButtonContainer/ButtonKacamata1
@onready var kacamata2_button: Button = $BoxContainer/TextureRect/ButtonContainer/ButtonKacamata2
@onready var kacamata3_button: Button = $BoxContainer/TextureRect/ButtonContainer/ButtonKacamata3
@onready var kacamata4_button: Button = $BoxContainer/TextureRect/ButtonContainer/ButtonKacamata4
@onready var tentangKami_button: Button = $BoxContainer/TextureRect/ButtonContainer/ButtonTentangKami
@onready var quit_button: Button = $BoxContainer/TextureRect/ButtonContainer/ButtonQuit


func _on_button_quit_pressed() -> void:
	get_tree().quit()


func _on_button_tentang_kami_pressed() -> void:
	get_tree().change_scene_to_file("res://Scenes/tentang_kami.tscn")


func _on_button_kacamata_1_pressed() -> void:
	send_glasses_choice("godot_project/Glasses/glasses1.png")
	get_tree().change_scene_to_file("res://Scenes/webcam_client_udp.tscn")


func _on_button_kacamata_2_pressed() -> void:
	send_glasses_choice("godot_project/Glasses/glasses2.png")
	get_tree().change_scene_to_file("res://Scenes/webcam_client_udp.tscn")


func _on_button_kacamata_3_pressed() -> void:
	send_glasses_choice("godot_project/Glasses/glasses3.png")
	get_tree().change_scene_to_file("res://Scenes/webcam_client_udp.tscn")


func _on_button_kacamata_4_pressed() -> void:
	send_glasses_choice("godot_project/Glasses/glasses4.png")
	get_tree().change_scene_to_file("res://Scenes/webcam_client_udp.tscn")

func send_glasses_choice(path: String) -> void:
	# Mengirim pesan UDP singkat ke server lokal pada port 8888
	var peer := PacketPeerUDP.new()
	var err = peer.set_dest_address("127.0.0.1", 8888)
	if err != OK:
		print("Gagal set dest address: ", err)
		return
	var msg = ("SET_GLASSES:" + path).to_utf8_buffer()
	var res = peer.put_packet(msg)
	if res != OK:
		print("Gagal mengirim paket: ", res)
	peer.close()
