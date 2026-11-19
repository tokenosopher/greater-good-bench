extends Control

const Town = preload("res://scripts/neighborhood.gd")
const MAP = preload("res://art/maple_ward.png")
const INK = Color("#203246")
const MUTED = Color("#536574")
const PAPER = Color("#f8f7ef")
const WHITE = Color("#fffef7")
const BLUE = Color("#294ecc")
const GRID = Color("#a5cdd0")
const AQUA = Color("#bfdddd")
const EDGE = Color("#a8b3af")
const YELLOW = Color("#ffdb74")
const COLORS = [Color("#9ad4d1"), Color("#c1d99c"), Color("#edb69f")]
const LETTERS = ["A", "B", "C"]
const PINS = [Vector2(402,125), Vector2(294,233), Vector2(245,54)]
const HOST_PINS = [Vector2(146,178),Vector2(207,103),Vector2(229,244)]
const MAP_POS = Vector2(6,156)
const MAP_SCALE = 1.62

var normal: Font
var heavy: FontVariation
var smallcaps: FontVariation
var sound := true
var day := 0
var request := 0
var selected := -1
var count := 0
var phase := "board"
var help_open := false
var time := 0.0
var elapsed := 0.0
var hits: Array = []
var hover := ""
var focus_id := ""
var pointer := Vector2(-1000,-1000)
var keyboard := false
var muted_choices: Array = []
var sound_player: AudioStreamPlayer
var notes: Dictionary = {}
var active_delivery := false
var show_request := false

func _ready() -> void:
	normal = ThemeDB.fallback_font
	heavy = FontVariation.new()
	heavy.base_font = normal
	heavy.variation_embolden = 1.1
	smallcaps = FontVariation.new()
	smallcaps.base_font = normal
	smallcaps.variation_embolden = 0.65
	smallcaps.spacing_glyph = 2
	sound_player = AudioStreamPlayer.new()
	add_child(sound_player)
	notes["tap"] = make_tone([440.0,554.4],0.065)
	notes["connect"] = make_tone([523.3,659.3,784.0,1046.5],0.095)
	notes["try"] = make_tone([392.0,349.2],0.08)
	set_process(true)

func make_tone(freqs: Array, duration: float) -> AudioStreamWAV:
	var wave := AudioStreamWAV.new()
	wave.format = AudioStreamWAV.FORMAT_16_BITS
	wave.mix_rate = 22050
	var samples := int(duration * wave.mix_rate)
	var data := PackedByteArray()
	data.resize(samples * freqs.size() * 2)
	for i in freqs.size():
		for j in samples:
			var t := float(j)/wave.mix_rate
			var envelope := minf(t/0.009,1.0) * pow(1.0-float(j)/samples,1.6)
			data.encode_s16(2*(i*samples+j), int(sin(TAU*freqs[i]*t)*2750*envelope))
	wave.data = data
	return wave

func tone(key: String) -> void:
	if sound:
		sound_player.stream = notes[key]
		sound_player.play()

func _process(delta: float) -> void:
	time += delta
	if active_delivery:
		elapsed += delta
		if elapsed >= 1.2:
			active_delivery = false
	queue_redraw()

func task() -> Array:
	return Town.DAYS[day][request]

func box(r: Rect2, fill: Color, border: Color = Color.TRANSPARENT, w: float = 1) -> void:
	draw_rect(r,fill)
	if border.a > 0:
		draw_rect(r,border,false,w)

func txt(x: float,y: float,s: String,sz: int = 16,c: Color = INK,f: Font = null) -> void:
	draw_string(normal if f == null else f,Vector2(x,y),s,HORIZONTAL_ALIGNMENT_LEFT,-1,sz,c)

func cap(x: float,y: float,s: String,c: Color = MUTED,sz: int = 11) -> void:
	txt(x,y,s,sz,c,smallcaps)

func words(x: float,y: float,s: String,width: float,sz: int,step: int,c: Color = INK,f: Font = null) -> float:
	var font: Font = normal if f == null else f
	var row := ""
	for word in s.split(" "):
		var trial: String = word if row.is_empty() else row+" "+word
		if row != "" and font.get_string_size(trial,HORIZONTAL_ALIGNMENT_LEFT,-1,sz).x > width:
			txt(x,y,row,sz,c,font)
			y += step
			row = word
		else:
			row = trial
	txt(x,y,row,sz,c,font)
	return y

func dash(a: Vector2,b: Vector2,c: Color,len_px: float = 4) -> void:
	draw_dashed_line(a,b,c,1,len_px)

func icon(which: String,x: float,y: float,s: float,c: Color) -> void:
	draw_set_transform(Vector2(x,y),0,Vector2.ONE*s/24.0)
	match which:
		"arrow":
			draw_line(Vector2(3,12),Vector2(20,12),c,2)
			draw_polyline(PackedVector2Array([Vector2(13,5),Vector2(20,12),Vector2(13,19)]),c,2)
		"chevron":
			draw_polyline(PackedVector2Array([Vector2(9,6),Vector2(15,12),Vector2(9,18)]),c,2)
		"sun":
			draw_circle(Vector2(12,12),4,c)
			for i in 8:
				var d := Vector2.RIGHT.rotated(i*PI/4.0)
				draw_line(Vector2(12,12)+d*7,Vector2(12,12)+d*10,c,2)
		"map":
			draw_polyline(PackedVector2Array([Vector2(2,5),Vector2(9,2),Vector2(15,5),Vector2(22,2),Vector2(22,19),Vector2(15,22),Vector2(9,19),Vector2(2,22),Vector2(2,5)]),c,2)
			draw_line(Vector2(9,2),Vector2(9,19),c,1.5)
			draw_line(Vector2(15,5),Vector2(15,22),c,1.5)
		"sound","silent":
			draw_colored_polygon(PackedVector2Array([Vector2(2,9),Vector2(6,9),Vector2(12,4),Vector2(12,20),Vector2(6,15),Vector2(2,15)]),c)
			if which == "sound":
				for r in [5.0,9.0]:draw_arc(Vector2(12,12),r,-.85,.85,10,c,1.8)
			else:
				draw_line(Vector2(16,9),Vector2(22,15),c,1.8)
				draw_line(Vector2(16,15),Vector2(22,9),c,1.8)
		"link":
			draw_circle(Vector2(5,16),3,c,false,2)
			draw_circle(Vector2(19,7),3,c,false,2)
			draw_line(Vector2(8,14),Vector2(16,9),c,2)
		"pin":
			draw_circle(Vector2(12,9),6,c,false,2)
			draw_polyline(PackedVector2Array([Vector2(7,12),Vector2(12,20),Vector2(17,12)]),c,2)
			draw_circle(Vector2(12,9),1.5,c)
		"check":
			draw_polyline(PackedVector2Array([Vector2(3,12),Vector2(9,18),Vector2(21,5)]),c,3)
		"mail":
			box(Rect2(2,5,20,14),Color.TRANSPARENT,c,1.8)
			draw_polyline(PackedVector2Array([Vector2(2,5),Vector2(12,13),Vector2(22,5)]),c,1.8)
		"people":
			draw_circle(Vector2(9,7),3.5,c); draw_circle(Vector2(17,8),2.5,c)
			box(Rect2(3,13,12,7),c); box(Rect2(16,13,5,6),c)
	draw_set_transform(Vector2.ZERO,0,Vector2.ONE)

func register(id: String,r: Rect2) -> void:
	hits.append([id,r])
	if keyboard and focus_id == id:
		draw_rect(r.grow(3),BLUE,false,2)

func hot(id: String) -> bool:
	return (hover == id and not keyboard) or (keyboard and focus_id == id)

func brand() -> void:
	box(Rect2(26,17,52,50),BLUE,INK,1.5)
	# A pair of little homes on a shared green island.
	draw_colored_polygon(PackedVector2Array([Vector2(31,52),Vector2(52,43),Vector2(72,51),Vector2(51,62)]),Color("#a7c995"))
	draw_colored_polygon(PackedVector2Array([Vector2(31,52),Vector2(51,62),Vector2(51,65),Vector2(31,55)]),Color("#71a392"))
	draw_colored_polygon(PackedVector2Array([Vector2(51,62),Vector2(72,51),Vector2(72,54),Vector2(51,65)]),Color("#5d9283"))
	for v in [Vector2(35,33),Vector2(48,39)]:
		box(Rect2(v.x,v.y+6,16,12),Color("#fff0bc"),INK)
		draw_colored_polygon(PackedVector2Array([v+Vector2(-2,7),v+Vector2(7,-2),v+Vector2(18,7)]),Color("#f2a56f"))
		box(Rect2(v.x+6,v.y+11,4,7),INK)
	txt(92,45,"Common Ground",33,INK,heavy)
	cap(94,65,"NEIGHBORHOOD EXCHANGE",MUTED,10)

func _draw() -> void:
	hits.clear()
	box(Rect2(0,0,1280,800),PAPER)
	draw_line(Vector2(0,85),Vector2(1280,85),INK,2)
	brand()
	var day_r := Rect2(996,23,141,39)
	box(day_r,Color("#f6e8ac"),INK)
	icon("sun",1007,31,22,INK)
	txt(1037,49,"Day %02d / 03" % (day+1),16,INK,heavy)
	for item in [["sound",1151],["help",1206]]:
		var r := Rect2(item[1],22,48,41)
		box(r,WHITE if not hot(item[0]) else Color("#dee7ee"),INK)
		if item[0] == "sound":
			icon("sound" if sound else "silent",item[1]+12,31,24,INK)
		else:
			draw_circle(Vector2(item[1]+24,42),10,INK,false,1.8)
			txt(item[1]+20,48,"?",16,INK,heavy)
		register(item[0],r)
	map_view()
	sidebar()
	box(Rect2(0,754,1280,46),INK)
	icon("link",27,766,23,Color("#b6d9ab"))
	txt(61,783,"%d connection%s made" % [count,"" if count == 1 else "s"],15,WHITE,heavy)
	draw_line(Vector2(235,767),Vector2(235,785),Color("#64747c"))
	txt(253,783,"Maple Ward Exchange",14,Color("#c3d1d4"))
	draw_circle(Vector2(1060,777),3.8,Color("#b9d991"))
	cap(1074,781,"NETWORK ONLINE",Color("#d1dfcd"),10)
	if help_open:help_dialog()

func cloud(x: float,y: float,k: float) -> void:
	var pts := PackedVector2Array([Vector2(0,12),Vector2(8,12),Vector2(8,7),Vector2(16,7),Vector2(16,3),Vector2(25,3),Vector2(25,0),Vector2(38,0),Vector2(38,4),Vector2(45,4),Vector2(45,8),Vector2(52,8),Vector2(52,11),Vector2(60,11),Vector2(60,16),Vector2(0,16)])
	for i in pts.size():pts[i] = pts[i]*k+Vector2(x,y)
	draw_colored_polygon(pts,Color("#e9efe3"))
	draw_line(Vector2(x+6*k,y+17*k),Vector2(x+57*k,y+17*k),Color("#a9cacc"),2)

func anchor(pos: Vector2) -> Vector2:
	return MAP_POS+pos*MAP_SCALE

func map_view() -> void:
	var map_r := Rect2(25,107,802,625)
	box(Rect2(28,111,802,625),Color("#c7cec1"))
	box(map_r,AQUA)
	for x in range(43,827,24):draw_line(Vector2(x,108),Vector2(x,685),GRID,1)
	for y in range(122,685,24):draw_line(Vector2(26,y),Vector2(826,y),GRID,1)
	for x in range(43,827,96):
		for y in range(122,685,96):
			draw_line(Vector2(x-2,y),Vector2(x+2,y),Color("#94bdc2"))
			draw_line(Vector2(x,y-2),Vector2(x,y+2),Color("#94bdc2"))
	cloud(99+sin(time*.035)*4,249,1.12)
	cloud(585+sin(time*.045)*5,226,.95)
	cloud(705+sin(time*.033)*4,288,.71)
	cloud(73,531,.65)
	cloud(657,559,.82)
	icon("map",48,129,18,INK)
	cap(76,143,"DISTRICT MAP   /   001",INK,10)
	txt(46,190,"Maple Ward",42,INK,heavy)
	box(Rect2(695,128,111,27),Color("#d8e8df"),Color("#68979a"))
	draw_circle(Vector2(710,141),3.3,Color("#4d7f67"))
	cap(720,145,"LIVE MAP",Color("#34585b"),10)
	# Drop the terrain a few pixels onto a flat ink shadow.
	var dest := Rect2(MAP_POS,Vector2(MAP.get_size())*MAP_SCALE)
	draw_texture_rect(MAP,Rect2(dest.position+Vector2(0,5),dest.size),false,Color(0.22,.38,.40,.14))
	draw_texture_rect(MAP,dest,false)
	life_on_the_block()
	if phase == "success":
		route()
	for i in 3:
		var point := anchor(PINS[i])
		if phase in ["day_done","finished"]:continue
		marker(point,LETTERS[i],COLORS[i],selected == i or hot("map%d"%i) or hot("choice%d"%i),false)
		if phase != "success":register("map%d"%i,Rect2(point.x-20,point.y-45,40,49))
	if not phase in ["day_done","finished"]:
		var host_pos := anchor(HOST_PINS[task()[0]])
		marker(host_pos,"!",YELLOW,false,true)
		if phase != "success":
			register("request_pin",Rect2(host_pos.x-19,host_pos.y-42,38,45))
			if show_request or hot("request_pin"):
				pin_label(host_pos,Town.HOSTS[task()[0]][0]+" · "+Town.HOSTS[task()[0]][1])
			else:
				for i in 3:
					if hot("map%d"%i):pin_label(anchor(PINS[i]),Town.PEOPLE[i][0]+" · "+Town.PEOPLE[i][1])
	# Map compass, distance scale, and legend are anchored to the chart frame.
	var c := Vector2(62,644)
	txt(c.x-5,c.y-15,"N",11,INK,heavy)
	draw_colored_polygon(PackedVector2Array([c+Vector2(0,-9),c+Vector2(-7,9),c+Vector2(0,5)]),INK)
	draw_colored_polygon(PackedVector2Array([c+Vector2(0,-9),c+Vector2(7,9),c+Vector2(0,5)]),Color("#72979e"))
	draw_line(Vector2(726,651),Vector2(792,651),INK,2)
	for x in [726,759,792]:draw_line(Vector2(x,645),Vector2(x,652),INK,2)
	txt(726,669,"0",10,MUTED);txt(766,669,"50 m",10,MUTED)
	box(Rect2(25,685,802,47),Color("#eaf0e5"),INK,1)
	draw_rect(Rect2(46,702,12,12),YELLOW)
	draw_rect(Rect2(46,702,12,12),INK,false,1.5)
	txt(67,714,"Request",14,INK,heavy)
	draw_circle(Vector2(167,708),6,Color("#94c5bf"));draw_circle(Vector2(167,708),6,INK,false,1.5)
	txt(182,714,"Neighbor",14,INK,heavy)
	var legend := "Select a pin to meet a neighbor"
	if phase == "success":legend = "A new connection on the block"
	elif phase in ["day_done","finished"]:legend = "All requests met for the day"
	txt(568,714,legend,14,MUTED)
	draw_rect(map_r,INK,false,2)

func pin_label(point: Vector2,label: String) -> void:
	var width := normal.get_string_size(label,HORIZONTAL_ALIGNMENT_LEFT,-1,14).x+20
	var x := clampf(point.x-width*.5,31,821-width)
	box(Rect2(x,point.y-76,width,27),WHITE,INK)
	txt(x+10,point.y-57,label,14,INK)

func life_on_the_block() -> void:
	# Pedestrians walk the paved paths and turn at each end.
	var a := (1-cos(time*.19))*.5
	var b := (1-cos(time*.25+2.1))*.5
	walker(anchor(Vector2(186,144).lerp(Vector2(265,183),a)),Color("#bd6b4f"),Color("#bd8e68"),time*4)
	walker(anchor(Vector2(355,159).lerp(Vector2(306,184),b)),Color("#6387a8"),Color("#a47151"),time*4.5)
	for i in 3:
		var bx := 536+i*11+sin(time*.12)*11
		var by := 197-i%2*7+sin(time*.22+i)*2
		var flap := 2+sin(time*2+i)
		draw_polyline(PackedVector2Array([Vector2(bx-4,by-flap),Vector2(bx,by),Vector2(bx+4,by-flap)]),Color("#567d84"),1.6)
	if count >= 2:
		for i in 4:
			var pot := anchor(Vector2(278+i*6,117-i*3))
			box(Rect2(pot.x,pot.y,6,6),Color("#ab7054"),INK,1)
			draw_circle(pot+Vector2(3,-2),4,Color("#67875b"))
			draw_circle(pot+Vector2(1,-4),2,Color("#92ae72"))

func walker(feet: Vector2,shirt: Color,skin: Color,step: float) -> void:
	var x := roundf(feet.x)
	var y := roundf(feet.y)
	var stride := roundf(sin(step)*1.4)
	draw_set_transform(Vector2(x,y),0,Vector2.ONE*1.5)
	box(Rect2(-3,0,7,2),Color(.26,.32,.30,.28))
	box(Rect2(-2+stride,-3,2,4),INK)
	box(Rect2(1-stride,-3,2,4),INK)
	box(Rect2(-2.5,-8,5,6),shirt)
	box(Rect2(-2,-12,4,4),skin)
	box(Rect2(-2,-13,4,2),Color("#55483e"))
	draw_set_transform(Vector2.ZERO,0,Vector2.ONE)

func marker(p: Vector2,letter: String,color: Color,on: bool,is_request: bool) -> void:
	var k := -3 if on else 0
	var center := Vector2(round(p.x),round(p.y)+k)
	var top := center+Vector2(-16,-42)
	box(Rect2(top+Vector2(3,3),Vector2(33,31)),Color("#394c53"))
	draw_colored_polygon(PackedVector2Array([center+Vector2(-7,-12),center+Vector2(7,-12),center+Vector2(0,0)]),INK)
	draw_colored_polygon(PackedVector2Array([center+Vector2(-4,-13),center+Vector2(4,-13),center+Vector2(0,-5)]),color)
	box(Rect2(top,Vector2(32,30)),color if not on else WHITE,INK,2)
	if is_request:txt(top.x+12,top.y+23,letter,21,INK,heavy)
	else:txt(top.x+8,top.y+23,letter,20,INK,heavy)

func route() -> void:
	var start := anchor(PINS[selected])
	var end := anchor(HOST_PINS[task()[0]])
	var mid := anchor(Vector2(259,176))
	draw_dashed_line(start,mid,BLUE,3,7)
	draw_dashed_line(mid,end,BLUE,3,7)
	var t := clampf(elapsed/1.2,0,1)
	var pos := start.lerp(mid,t*2) if t < .5 else mid.lerp(end,(t-.5)*2)
	box(Rect2(pos.x-13,pos.y-10,26,20),WHITE,BLUE,2)
	icon("mail",pos.x-10,pos.y-10,20,BLUE)

func portrait(x: float,y: float,who: int,k: float = 2.25) -> void:
	var skins = [Color("#ba7d5b"),Color("#dba381"),Color("#965e48"),Color("#bf825d"),Color("#ba825b"),Color("#9a654e")]
	var hairs = [Color("#4a3f42"),Color("#493e3b"),Color("#46464b"),Color("#3a4146"),Color("#6c4d41"),Color("#58545b")]
	var shirts = [Color("#699794"),Color("#c28750"),Color("#6e81ad"),Color("#5779a0"),Color("#7b9b67"),Color("#c58964")]
	var bgs = [Color("#f7d9a1"),Color("#d4dec6"),Color("#d9d5e8"),COLORS[0],COLORS[1],COLORS[2]]
	var skin: Color = skins[who]
	var hair: Color = hairs[who]
	var shirt: Color = shirts[who]
	draw_set_transform(Vector2(x,y),0,Vector2.ONE*k)
	box(Rect2(0,0,20,20),bgs[who],INK,0.55)
	box(Rect2(4,17,12,3),shirt);box(Rect2(6,15,8,3),shirt)
	box(Rect2(8,13,4,4),skin.darkened(.1))
	box(Rect2(5,4,10,7),hair)
	box(Rect2(6,7,8,6),skin)
	box(Rect2(7,12,6,2),skin)
	box(Rect2(5,9,1,2),skin);box(Rect2(14,9,1,2),skin)
	box(Rect2(7,4,7,4),skin)
	box(Rect2(6,3,7,3),hair)
	box(Rect2(5,5,3,4),hair)
	box(Rect2(8,8,1,1),INK);box(Rect2(12,8,1,1),INK)
	box(Rect2(10,11,2,1),skin.darkened(.25))
	match who:
		0:
			box(Rect2(3,3,4,4),hair);box(Rect2(7,3,7,2),Color("#b75b46"))
			box(Rect2(7,16,2,4),Color("#eee3c2"));box(Rect2(13,16,1,4),Color("#eee3c2"))
		1:
			box(Rect2(5,7,5,3),Color.TRANSPARENT,INK,.65);box(Rect2(10,7,5,3),Color.TRANSPARENT,INK,.65)
		2,4:
			box(Rect2(3,5,14,2),Color("#997644"))
			box(Rect2(6,2,8,4),Color("#e7b868"));box(Rect2(6,4,8,1),Color("#b5874e"))
		3:
			box(Rect2(5,4,10,2),Color("#e7a16d"));box(Rect2(7,2,6,3),Color("#f5b879"))
			box(Rect2(10,5,6,1),INK)
		5:
			box(Rect2(5,3,10,3),Color("#586a81"));box(Rect2(4,5,12,2),Color("#8191a0"))
			box(Rect2(7,12,6,2),hair);box(Rect2(8,11,4,1),hair)
	draw_set_transform(Vector2.ZERO,0,Vector2.ONE)

func sidebar() -> void:
	var x := 855
	cap(x,123,"MUTUAL AID NETWORK",MUTED,10)
	txt(x-1,165,"Community desk",32,INK,heavy)
	box(Rect2(1180,137,73,28),Color("#e5e9de"),Color("#a8b2a4"))
	txt(1194,157,"%02d / 03" % (request+1),14,INK,heavy)
	if phase in ["day_done","finished"]:
		summary_panel()
		return
	request_card()
	match phase:
		"board": offer_list()
		"offer","retry": offer_detail()
		"success": outcome()

func request_card() -> void:
	var r := Rect2(855,189,398,234)
	box(Rect2(859,194,398,234),Color("#cecbb8"),INK)
	box(r,Color("#fff0bb"),INK,1.5)
	box(Rect2(855,189,7,234),YELLOW)
	icon("mail",877,205,20,INK)
	cap(908,220,"REQUEST  %03d" % (day*3+request+1),INK,11)
	# A small postage stamp with a sun, ruled like the corner of a postcard.
	box(Rect2(1198,199,35,28),Color("#f6df98"),Color("#a6945e"))
	draw_rect(Rect2(1201,202,29,22),Color("#b6a164"),false)
	icon("sun",1206,203,19,Color("#95814c"))
	dash(Vector2(877,237),Vector2(1231,237),Color("#ae9f70"),4)
	words(877,272,"“"+task()[1]+"”",350,19,26,INK)
	var host: int = task()[0]
	portrait(877,358,host,2.28)
	txt(934,378,Town.HOSTS[host][0],17,INK,heavy)
	icon("pin",933,385,14,MUTED)
	txt(952,397,Town.HOSTS[host][1],14,MUTED)

func offer_list() -> void:
	cap(855,463,"AVAILABLE NEIGHBORS",INK,11)
	draw_line(Vector2(1044,459),Vector2(1253,459),EDGE)
	for i in 3:
		var y := 481+i*73
		var id := "choice%d"%i
		var hover_row := hot(id) or hot("map%d"%i)
		var r := Rect2(855,y,398,61)
		box(Rect2(857,y+3,398,61),Color("#ced1c8"))
		box(r,Color("#edf2ee") if hover_row else WHITE,BLUE if hover_row else INK,2 if hover_row else 1)
		box(Rect2(868,y+10,41,41),COLORS[i],INK)
		txt(880,y+38,LETTERS[i],20,INK,heavy)
		txt(925,y+26,Town.PEOPLE[i][0],18,INK,heavy)
		txt(925,y+47,Town.PEOPLE[i][1],14,MUTED)
		if i in muted_choices:
			txt(1158,y+37,"Reviewed",12,MUTED)
		icon("chevron",1216,y+21,19,INK)
		register(id,r)
	icon("people",856,706,19,MUTED)
	txt(883,721,"Choose a neighbor to read their offer.",14,MUTED)

func button(id: String,r: Rect2,label: String,primary: bool = true) -> void:
	var fill := BLUE if primary else WHITE
	if hot(id):fill = Color("#193caf") if primary else Color("#e3e9df")
	box(Rect2(r.position+Vector2(2,3),r.size),INK)
	box(r,fill,INK,1)
	txt(r.position.x+16,r.position.y+r.size.y*.5+6,label,16,WHITE if primary else INK,heavy)
	if primary:icon("arrow",r.end.x-37,r.position.y+r.size.y*.5-10,21,WHITE)
	register(id,r)

func offer_detail() -> void:
	var p = Town.PEOPLE[selected]
	cap(855,459,"NEIGHBOR %s  /  OFFER" % LETTERS[selected],INK,10)
	draw_line(Vector2(1068,455),Vector2(1253,455),EDGE)
	portrait(857,475,selected+3,2)
	txt(910,494,p[0],20,INK,heavy)
	txt(911,514,p[1],14,MUTED)
	words(856,547,"“"+task()[3][selected]+"”",389,17,23)
	if phase == "retry":
		words(857,616,Town.FEEDBACK[day][request][selected],393,15,20,Color("#914c38"))
		button("back",Rect2(856,684,395,44),"Review other offers")
	else:
		button("back",Rect2(856,682,110,45),"Go back",false)
		button("connect",Rect2(981,682,270,45),"Make connection")

func outcome() -> void:
	box(Rect2(856,452,395,193),Color("#e6eedb"),Color("#a2b39c"))
	icon("check",873,469,23,Color("#4c785c"))
	cap(904,485,"CONNECTION MADE",Color("#375c47"),10)
	txt(875,524,Town.PEOPLE[selected][0]+" + "+Town.HOSTS[task()[0]][0],25,INK,heavy)
	words(875,557,task()[4],352,16,23)
	button("next",Rect2(856,677,395,50),"Next request" if request < 2 else "Finish the day")

func summary_panel() -> void:
	var done := phase == "finished"
	box(Rect2(859,195,398,435),Color("#c6d1bb"),INK)
	box(Rect2(855,190,398,435),Color("#e7eedb"),INK)
	icon("sun",875,214,31,INK)
	cap(920,235,"EXCHANGE COMPLETE" if done else "DAILY ROUNDUP",INK)
	txt(876,294,"A connected block" if done else "Day %02d complete" % (day+1),30,INK,heavy)
	var message := "Nine requests met in three days. Try asking someone on your own block, “What would make your day easier?” Give them time to answer." if done else "Three requests met. Here's who lent a hand in Maple Ward today."
	words(876,331,message,350,18,26)
	var y := 442
	for entry in Town.DAYS[day]:
		var neighbor: int = entry[2]
		box(Rect2(875,y-20,28,28),COLORS[neighbor],INK)
		icon("check",880,y-16,18,INK)
		txt(916,y,Town.PEOPLE[neighbor][0]+" helped "+Town.HOSTS[entry[0]][0],17,INK,heavy)
		y += 48
	button("advance",Rect2(856,677,395,50),"Play again" if done else "Start day %02d" % (day+2))

func help_dialog() -> void:
	hits.clear()
	box(Rect2(0,0,1280,800),Color(.08,.15,.21,.52))
	box(Rect2(384,193,523,422),INK)
	box(Rect2(378,186,523,422),PAPER,INK,2)
	icon("map",405,212,21,BLUE)
	cap(438,228,"FIELD GUIDE",BLUE,11)
	txt(404,279,"How to play",35,INK,heavy)
	for i in 3:
		var y := 321+i*64
		box(Rect2(406,y-19,29,29),[YELLOW,COLORS[0],COLORS[1]][i],INK)
		txt(415,y+2,str(i+1),16,INK,heavy)
		words(451,y,["Read the request. Notice what the person needs and any limits they mention.","Select a letter on the map or a neighbor in the list to hear their offer.","Connect the two people whose plans fit. Complete three requests each day."][i],412,16,22)
	txt(406,523,"Keyboard: A / B / C to read offers, Tab and Enter to select.",14,MUTED)
	button("close_help",Rect2(406,546,467,40),"Back to the neighborhood")

func activate(id: String) -> void:
	if help_open:
		if id == "close_help":
			help_open = false
			tone("tap")
	elif id == "help":
		help_open = true
		tone("tap")
	elif id == "sound":
		sound = not sound
		if sound:tone("tap")
		else:sound_player.stop()
	elif id.begins_with("choice") or id.begins_with("map"):
		if phase in ["board","offer","retry"]:
			show_request = false
			selected = int(id.right(1))
			phase = "offer"
			tone("tap")
	elif id == "request_pin" and phase != "success":
		show_request = not show_request
		tone("tap")
	elif id == "back":
		if phase in ["offer","retry"]:
			selected = -1
			phase = "board"
			tone("tap")
	elif id == "connect" and phase == "offer":
		if selected == task()[2]:
			phase = "success"
			count += 1
			elapsed = 0
			active_delivery = true
			tone("connect")
		else:
			phase = "retry"
			if not selected in muted_choices:muted_choices.append(selected)
			tone("try")
	elif id == "next" and phase == "success":
		if request < 2:
			request += 1
			reset_board()
		else:
			phase = "finished" if day == 2 else "day_done"
		tone("tap")
	elif id == "advance":
		if phase == "finished":
			day = 0
			count = 0
		elif phase == "day_done":
			day += 1
		request = 0
		reset_board()
		tone("tap")
	else:
		return
	focus_id = ""
	hover = ""
	queue_redraw()

func reset_board() -> void:
	show_request = false
	phase = "board"
	selected = -1
	muted_choices.clear()
	active_delivery = false

func hit_at(point: Vector2) -> String:
	for i in range(hits.size()-1,-1,-1):
		if hits[i][1].has_point(point):return hits[i][0]
	return ""

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		pointer = get_local_mouse_position()
		keyboard = false
		hover = hit_at(pointer)
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if hover != "" else Control.CURSOR_ARROW
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		keyboard = false
		activate(hit_at(get_local_mouse_position()))
	elif event is InputEventKey and event.pressed and not event.echo:
		keyboard = true
		match event.keycode:
			KEY_TAB:
				var ids: Array = []
				for h in hits:
					if h[0].begins_with("map") and phase != "board":continue
					ids.append(h[0])
				if ids.size() > 0:
					var next := ids.find(focus_id)
					next = posmod(next+(-1 if event.shift_pressed else 1),ids.size())
					focus_id = ids[next]
				get_viewport().set_input_as_handled()
			KEY_ENTER,KEY_SPACE:
				if focus_id != "":activate(focus_id)
				elif help_open:activate("close_help")
				elif phase == "offer":activate("connect")
				elif phase == "success":activate("next")
				elif phase == "retry":activate("back")
				elif phase in ["day_done","finished"]:activate("advance")
			KEY_ESCAPE:
				if help_open:activate("close_help")
				else:activate("back")
			KEY_A,KEY_B,KEY_C:
				if not help_open:activate("choice%d" % (event.keycode-KEY_A))
			KEY_F1:activate("close_help" if help_open else "help")
