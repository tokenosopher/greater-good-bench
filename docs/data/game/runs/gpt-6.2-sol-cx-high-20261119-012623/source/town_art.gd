extends Node2D

const TILE := Vector2i(40, 35)
const WIDTH := 12
const HEIGHT := 8
const ROAD := Color("#cd9c6a")
const SHADE := Color("#80946f")
const DIRT := Color("#a77f55")
const PARK := Color("#8c925a")
const POND := Color("#527f7b")

const ROOFS := [
	["#b56245", "#da8860", "#8c493c", "#e6ac7d", "#a05240"],
	["#637989", "#82969b", "#445765", "#a3afb1", "#536877"],
	["#946b65", "#b58a78", "#694c51", "#cfaa90", "#815b58"],
	["#777b58", "#989b71", "#505743", "#b4ae80", "#666c4e"],
	["#a97d4c", "#c69c65", "#7f5d43", "#dfb786", "#976e47"],
	["#617d73", "#8a9d83", "#465e56", "#a5b09a", "#526d61"],
]

var board: Array = []
var sheltered := {}
var rng := RandomNumberGenerator.new()


func update_map(new_board: Array, new_sheltered: Dictionary) -> void:
	board = new_board
	sheltered = new_sheltered
	queue_redraw()


func at(x: int, y: int) -> String:
	if y < 0 or y >= HEIGHT or x < 0 or x >= WIDTH:
		return "#"
	return board[y][x]


func blocked(t: String) -> bool:
	return t in ["#", "p", "~"]


func rect(x: float, y: float, w: float, h: float, color: Color) -> void:
	draw_rect(Rect2(x, y, w, h), color)


func shape(points: Array, color: Color) -> void:
	draw_colored_polygon(PackedVector2Array(points), color)


func rounded_square(x: int, y: int, w: int, h: int, cut: int, color: Color) -> void:
	rect(x + cut, y, w - cut * 2, h, color)
	rect(x, y + cut, cut, h - cut * 2, color)
	rect(x + w - cut, y + cut, cut, h - cut * 2, color)


func _draw() -> void:
	if board.is_empty():
		return
	for y in HEIGHT:
		for x in WIDTH:
			rng.seed = 1319 + x * 1193 + y * 811
			draw_set_transform(Vector2(x * TILE.x, y * TILE.y))
			draw_ground(x, y)
	for y in HEIGHT:
		for x in WIDTH:
			rng.seed = 6271 + x * 1193 + y * 811
			draw_set_transform(Vector2(x * TILE.x, y * TILE.y))
			draw_detail(x, y)
	draw_set_transform(Vector2.ZERO)


func draw_ground(x: int, y: int) -> void:
	var t := at(x, y)
	var cell := Vector2i(x, y)
	var width := TILE.x
	var height := TILE.y
	var is_shaded := t in ["=", "W", "S"] or sheltered.has(cell)
	var base := SHADE if is_shaded else ROAD
	match t:
		"#": base = DIRT
		"p": base = PARK
		"~": base = POND
	rect(0, 0, width, height, base)
	for n in 53:
		var px := rng.randi_range(0, width - 3)
		var py := rng.randi_range(0, height - 2)
		var fleck := base.lightened(0.12) if n % 3 == 0 else base.darkened(0.09)
		rect(px, py, rng.randi_range(1, 3), 1, fleck)
	if t == "~":
		return
	if blocked(t):
		rect(2, 2, 36, 2, base.lightened(0.09))
		rect(2, 31, 36, 2, base.darkened(0.13))
		return

	# Curbs follow the adjoining architecture.
	var curb := Color("#a08359") if is_shaded else Color("#a57b54")
	var rim := Color("#aeb08a") if is_shaded else Color("#e2b78a")
	if blocked(at(x, y - 1)):
		rect(0, 0, width, 2, curb)
		rect(0, 2, width, 1, rim)
	if blocked(at(x, y + 1)):
		rect(0, 32, width, 1, rim)
		rect(0, 33, width, 2, curb)
	if blocked(at(x - 1, y)):
		rect(0, 0, 2, height, curb)
		rect(2, 0, 1, height, rim)
	if blocked(at(x + 1, y)):
		rect(37, 0, 1, height, rim)
		rect(38, 0, 2, height, curb)

	if is_shaded:
		for n in 7:
			var px := rng.randi_range(4, 31)
			var py := rng.randi_range(4, 27)
			rect(px, py, 5, 2, Color("#778563"))
			rect(px + 2, py + 2, 5, 1, Color("#a0a480"))
	else:
		for n in 5:
			var px := rng.randi_range(5, 31)
			var py := rng.randi_range(4, 28)
			rect(px, py, 4, 1, Color("#b68b61"))
			rect(px + 1, py + 1, 3, 1, Color("#d7ae82"))


func draw_detail(x: int, y: int) -> void:
	var t := at(x, y)
	var cell := Vector2i(x, y)
	match t:
		"#":
			var kind := posmod(x * 7 + y * 11, 6)
			if Vector2i(x, y) in [Vector2i(5, 0), Vector2i(7, 2), Vector2i(11, 4)]:
				workshop(kind)
			elif Vector2i(x, y) in [Vector2i(2, 0), Vector2i(0, 3), Vector2i(3, 6)]:
				tall_house(kind)
			elif (x * 3 + y * 7) % 11 in [3, 8]:
				courtyard(x, y)
			else:
				building(kind, posmod(x + y, 3), false)
		"p":
			courtyard(x, y)
		"~":
			pond(x, y)
		"W":
			fountain(true)
		"w":
			fountain(false)
		"S":
			home_base()
		"=":
			shade_street(x, y)
		".":
			if (x + 3 * y) % 5 == 0:
				planter(7, 27, 7)
			if (x + y) % 4 == 0:
				street_grate(30, 25)
		_:
			var kind := (t.unicode_at(0) - 65) % ROOFS.size()
			building(kind, 2, true)
			if sheltered.has(cell):
				canopy()


func building(kind: int, style: int, home: bool) -> void:
	var pal: Array = ROOFS[kind]
	var roof := Color(pal[0])
	var lip := Color(pal[1])
	var roof_shadow := Color(pal[2])
	var roof_glint := Color(pal[3])
	var roof_tiles := Color(pal[4])
	var plaster := Color("#dfbd93") if home else Color("#d3b18b")
	var dark_plaster := Color("#ac8969")
	var outline := Color("#675444")
	var left := 5 if home else 4
	var right := 32 if style == 0 else 35
	var peak := 4 if style != 1 else 2
	var eave := 20 if style != 1 else 18

	rect(left + 2, 12, right - left + 4, 18, Color("#554c3c66"))
	rect(left + 5, 30, right - left - 1, 3, Color("#54473355"))
	rect(left + 2, 12, right - left - 1, 17, outline)
	rect(left + 3, 15, right - left - 3, 13, plaster)
	rect(left + 3, eave, right - left - 3, 2, dark_plaster)
	rect(right - 7, eave + 1, 5, 7, dark_plaster)
	rect(left + 3, 27, right - left - 3, 1, Color("#b29273"))
	rect(left + 4, 29, right - left - 4, 1, Color("#e4c096"))

	if style == 0:
		shape([Vector2(left - 1, eave), Vector2(left + 1, peak + 4),
			Vector2(left + 6, peak), Vector2(right - 5, peak),
			Vector2(right, peak + 5), Vector2(right + 1, eave)], roof_shadow)
		rect(left + 2, peak + 4, right - left - 4, eave - peak - 5, roof)
	else:
		rect(left - 1, peak + 2, right - left + 3, eave - peak - 1, roof_shadow)
		rect(left + 1, peak, right - left - 1, 3, roof_shadow)
		rect(left + 1, peak + 2, right - left - 1, eave - peak - 3, roof)

	rect(left + 3, peak + 1, right - left - 6, 2, lip)
	rect(left + 5, peak + 1, right - left - 11, 1, roof_glint)
	rect(left + 2, peak + 4, 2, eave - peak - 5, lip)
	rect(right - 5, peak + 3, 4, eave - peak - 4, roof_tiles)
	for row in range(peak + 5, eave - 1, 3):
		rect(left + 4, row, right - left - 7, 1, roof_tiles)
		for col in range(left + 6 + (row % 2) * 2, right - 6, 5):
			rect(col, row - 1, 1, 1, lip)
	rect(left, eave - 1, right - left + 1, 2, roof_shadow)
	rect(left + 2, eave - 1, right - left - 3, 1, lip)

	# Small utilitarian details give the roofs distinct silhouettes.
	if style == 1:
		rect(right - 12, peak + 4, 7, 5, roof_shadow)
		rect(right - 13, peak + 3, 7, 4, Color("#b8b39a"))
		rect(right - 12, peak + 4, 5, 1, Color("#e0d1ab"))
		rect(right - 12, peak + 5, 5, 1, Color("#827e70"))
	elif kind in [0, 2, 5]:
		rect(left + 7, peak + 6, 5, 4, roof_shadow)
		rect(left + 6, peak + 3, 5, 5, Color("#af8c6e"))
		rect(left + 5, peak + 3, 7, 1, Color("#e2b791"))
	else:
		rect(left + 6, peak + 7, 7, 5, roof_shadow)
		rect(left + 7, peak + 7, 5, 3, Color("#8eaaa2"))
		rect(left + 7, peak + 7, 5, 1, Color("#c5c4a4"))

	var window_y := eave + 2
	window(left + 6, window_y)
	if style == 1:
		window(left + 15, window_y)
	var door_x := right - 11 if style == 1 else right - 15
	rect(door_x, eave + 2, 5, 7, Color("#615d4e"))
	rect(door_x + 1, eave + 3, 3, 5, Color("#8b9a82") if kind % 2 else Color("#936e55"))
	rect(door_x + 3, eave + 6, 1, 1, Color("#e6bf7a"))
	rect(door_x - 1, 28, 7, 1, Color("#edcaa1"))
	if home:
		planter(left + 3, 29, 6)
		rect(right - 7, 26, 3, 2, Color("#8e664e"))
		rect(right - 7, 24, 3, 2, Color("#687b51"))
	elif style != 1:
		planter(right - 3, 30, 5)
		if kind % 2 == 0:
			street_grate(6, 31)


func window(x: int, y: int) -> void:
	rect(x - 1, y - 1, 7, 6, Color("#efd0a1"))
	rect(x, y, 5, 4, Color("#59665d"))
	rect(x + 1, y, 1, 3, Color("#9caca0"))
	rect(x + 3, y + 1, 1, 2, Color("#c4ad82"))
	rect(x - 1, y + 4, 7, 1, Color("#a98669"))


func workshop(kind: int) -> void:
	building(kind, 1, false)
	rect(4, 16, 32, 9, Color("#63554b"))
	rect(3, 16, 33, 6, Color("#ad6c52"))
	for i in 8:
		rect(3 + i * 4, 16, 2, 6, Color("#e5c9a0"))
	rect(3, 22, 33, 1, Color("#6d5750"))
	rect(8, 25, 15, 3, Color("#6b8577"))
	for i in 3:
		rect(9 + i * 5, 25, 2, 2, Color("#a1b4a0"))
	rect(14, 5, 13, 8, Color("#464e4e"))
	rect(15, 5, 11, 7, Color("#789799"))
	for i in 3:
		rect(16 + i * 4, 6, 2, 5, Color("#597478"))
	rect(15, 8, 11, 1, Color("#94aaa4"))


func tall_house(kind: int) -> void:
	building(kind, 2, false)
	rect(9, 5, 17, 16, Color("#5f5148"))
	rect(9, 4, 16, 13, Color("#d2ad7c"))
	rect(10, 4, 2, 13, Color("#e2bb85"))
	rect(22, 5, 3, 13, Color("#ab836a"))
	rect(8, 3, 19, 4, Color(ROOFS[kind][2]))
	rect(10, 3, 15, 2, Color(ROOFS[kind][1]))
	window(14, 9)
	rect(12, 15, 11, 3, Color("#776653"))
	rect(12, 15, 10, 1, Color("#b59f75"))
	rect(14, 16, 1, 2, Color("#a88b65"))
	rect(18, 16, 1, 2, Color("#a88b65"))


func planter(x: int, y: int, width: int) -> void:
	rect(x + 1, y + 2, width, 2, Color("#5f4d3b55"))
	rect(x, y + 1, width, 2, Color("#966751"))
	rect(x, y, width, 1, Color("#c9956d"))
	rect(x + 1, y - 2, width - 2, 2, Color("#5f774f"))
	for n in range(1, width - 1, 2):
		rect(x + n, y - 2, 1, 1, Color("#e6ad70") if n % 4 == 1 else Color("#a9af71"))


func street_grate(x: int, y: int) -> void:
	rect(x, y, 6, 4, Color("#9e805e"))
	for n in range(1, 6, 2):
		rect(x + n, y + 1, 1, 2, Color("#695c4c"))


func courtyard(x: int, y: int) -> void:
	rounded_square(2, 3, 36, 29, 3, Color("#626f4f"))
	rounded_square(3, 3, 34, 27, 3, Color("#8d9a61"))
	for n in 15:
		var px := rng.randi_range(5, 33)
		var py := rng.randi_range(5, 27)
		rect(px, py, 2, 1, Color("#b2ac70") if n % 3 else Color("#758455"))
	if (x + y) % 3 == 0:
		tree(7, 3, 19, 22, true)
		tree(21, 10, 13, 15, false)
		bench(7, 26)
	elif (x + y) % 3 == 1:
		tree(16, 3, 19, 22, false)
		rect(6, 7, 8, 16, Color("#877253"))
		for row in range(8, 24, 3):
			rect(7, row, 6, 1, Color("#57704d"))
			rect(8 + row % 3, row, 1, 1, Color("#d6af69"))
		planter(19, 27, 9)
	else:
		tree(7, 5, 18, 21, false)
		tree(22, 3, 14, 16, true)
		bench(21, 24)


func tree(x: int, y: int, w: int, h: int, golden: bool) -> void:
	var deep := Color("#3b583e")
	var side := Color("#526848")
	var leaf := Color("#657d50") if not golden else Color("#8b8e52")
	var light := Color("#82935d") if not golden else Color("#a8a15c")
	rounded_square(x + 3, y + h - 6, w, 7, 2, Color("#43543f69"))
	rect(x + w / 2 - 1, y + h - 8, 3, 7, Color("#776043"))
	rect(x + w / 2 - 1, y + h - 7, 1, 5, Color("#a27b50"))
	rounded_square(x, y + 3, w, maxi(h - 8, 6), 3, deep)
	rounded_square(x + 1, y + 1, w - 3, maxi(h - 9, 4), 2, side)
	rounded_square(x + 2, y, w - 5, maxi(h - 11, 4), 2, leaf)
	rect(x + 5, y + 2, maxi(w - 12, 1), 2, light)
	rect(x + 3, y + 4, 3, 2, light)
	rect(x + w - 7, y + 5, 2, 2, leaf)
	rect(x + 7, y + 6, 2, 1, light)
	rect(x + 3, y + h - 12, 4, 1, side)
	rect(x + w - 6, y + h - 11, 3, 1, leaf)


func bench(x: int, y: int) -> void:
	rect(x + 2, y + 4, 12, 2, Color("#52564055"))
	rect(x + 1, y + 1, 2, 5, Color("#6c6049"))
	rect(x + 10, y + 1, 2, 5, Color("#6c6049"))
	rect(x, y, 13, 2, Color("#ad8055"))
	rect(x, y + 2, 13, 1, Color("#dab278"))
	rect(x, y + 3, 13, 1, Color("#986e4d"))


func shade_street(x: int, y: int) -> void:
	if Vector2i(x, y) == Vector2i(8, 3):
		public_shade()
		return
	if blocked(at(x, y - 1)):
		tree(3, 1, 14, 13, (x + y) % 3 == 1)
		if (x + y) % 3 == 0:
			bench(19, 7)
	if blocked(at(x, y + 1)):
		if (x + y) % 2 == 0:
			tree(26, 21, 13, 12, false)
		else:
			planter(6, 29, 10)


func public_shade() -> void:
	rect(6, 9, 29, 18, Color("#46564268"))
	rect(7, 8, 2, 18, Color("#635a48"))
	rect(31, 8, 2, 18, Color("#635a48"))
	rect(8, 8, 23, 13, Color("#3a685d"))
	rect(6, 7, 27, 11, Color("#77a08c"))
	for i in 6:
		rect(7 + i * 4, 7, 2, 11, Color("#d3d8ab"))
	rect(6, 18, 27, 2, Color("#456b56"))
	bench(13, 23)
	planter(4, 28, 7)
	planter(29, 28, 7)


func fountain(flowing: bool) -> void:
	rounded_square(3, 4, 34, 27, 5, Color("#5a6c5c"))
	rounded_square(4, 3, 31, 26, 5, Color("#cfb891"))
	rounded_square(6, 5, 27, 22, 5, Color("#48958f") if flowing else Color("#a28e72"))
	rounded_square(8, 6, 23, 18, 4, Color("#73ada3") if flowing else Color("#b3a181"))
	rect(16, 11, 8, 9, Color("#637f75"))
	rect(17, 10, 6, 7, Color("#b8c3a5"))
	if flowing:
		rect(10, 13, 6, 1, Color("#bcddc5"))
		rect(23, 17, 6, 1, Color("#a1c9b7"))
		rect(11, 20, 5, 1, Color("#5f9996"))
		rect(19, 4, 2, 9, Color("#e1edcf"))
		rect(15, 7, 2, 5, Color("#bce1cc"))
		rect(23, 8, 2, 4, Color("#d7ebcf"))
		rect(13, 11, 1, 2, Color("#e1edcf"))
		rect(26, 13, 1, 1, Color("#d7ebcf"))
	else:
		rect(14, 20, 12, 4, Color("#70483d"))
		rect(16, 21, 8, 1, Color("#ead1a8"))
	rect(8, 26, 22, 1, Color("#ead1a8"))
	tree(1, 0, 11, 11, false)
	planter(29, 28, 7)


func home_base() -> void:
	building(5, 0, false)
	rect(4, 17, 32, 3, Color("#3e6758"))
	for i in 8:
		rect(4 + i * 4, 17, 2, 2, Color("#c7d0a4"))
	rect(17, 8, 7, 6, Color("#537365"))
	rect(20, 9, 1, 4, Color("#e9dcb5"))
	rect(18, 10, 5, 2, Color("#e9dcb5"))


func canopy() -> void:
	rect(8, 20, 25, 10, Color("#3f594b70"))
	rect(9, 22, 2, 9, Color("#44675a"))
	rect(29, 22, 2, 9, Color("#44675a"))
	rect(7, 19, 26, 6, Color("#497b6c"))
	for i in 6:
		rect(8 + i * 4, 19, 2, 6, Color("#bad0a0"))
	rect(7, 25, 26, 1, Color("#315d52"))


func pond(x: int, y: int) -> void:
	if at(x - 1, y) != "~":
		rect(0, 0, 5, 35, Color("#a5a06f"))
		rect(4, 0, 2, 35, Color("#6e8d71"))
		for row in range(4, 34, 7):
			rect(2, row, 2, 4, Color("#6f8052"))
			rect(4, row + 2, 3, 1, Color("#91a682"))
	if at(x, y - 1) != "~":
		rect(0, 0, 40, 6, Color("#a5a06f"))
		rect(0, 5, 40, 2, Color("#6e8d71"))
		for col in range(5, 40, 9):
			rect(col, 2, 2, 4, Color("#6f8052"))
			rect(col + 3, 4, 1, 3, Color("#687c50"))
	for i in 8:
		var px := rng.randi_range(8, 33)
		var py := rng.randi_range(9, 33)
		rect(px, py, rng.randi_range(2, 6), 1, Color("#83a799"))
	rounded_square(20, 14, 6, 3, 1, Color("#8c9e70"))
	rect(23, 14, 2, 1, Color("#c8b580"))
	if Vector2i(x, y) == Vector2i(10, 7):
		rect(2, 16, 23, 11, Color("#3f68676e"))
		rect(0, 14, 23, 10, Color("#806851"))
		for i in 7:
			rect(i * 3, 14, 2, 8, Color("#c29b6d"))
			rect(i * 3, 14, 2, 1, Color("#d5b082"))
		rect(2, 13, 2, 12, Color("#84644b"))
		rect(20, 13, 2, 12, Color("#84644b"))
		rect(2, 13, 2, 2, Color("#d6b080"))
		rect(20, 13, 2, 2, Color("#d6b080"))
