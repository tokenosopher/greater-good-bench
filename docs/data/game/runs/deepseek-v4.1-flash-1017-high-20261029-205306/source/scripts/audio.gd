extends Node
## Procedurally generated UI sounds. No external audio files.

const RATE := 22050

var muted := false
var _players: Array[AudioStreamPlayer] = []
var _streams: Dictionary = {}
var _next := 0


func _ready() -> void:
	for i in range(5):
		var p := AudioStreamPlayer.new()
		p.bus = "Master"
		p.volume_db = -8.0
		add_child(p)
		_players.append(p)

	_streams["click"] = _tone(620.0, 0.055, 0.12, 1.0)
	_streams["listen"] = _tone(480.0, 0.16, 0.13, 1.55)
	_streams["select"] = _tone(760.0, 0.07, 0.10, 1.08)
	_streams["success"] = _chord([523.25, 659.25, 783.99, 1046.5], 0.85, 0.10)
	_streams["fail"] = _fail_tone()
	_streams["warn"] = _tone(315.0, 0.28, 0.13, 0.86)
	_streams["settle"] = _chord([392.0, 523.25, 659.25], 1.3, 0.08)


func play(sound: String) -> void:
	if muted or not _streams.has(sound):
		return
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[sound]
	p.play()


func set_muted(value: bool) -> void:
	muted = value
	AudioServer.set_bus_mute(0, value)


func _tone(freq: float, dur: float, vol: float, slide: float = 1.0) -> AudioStreamWAV:
	var count := int(RATE * dur)
	var samples := PackedFloat32Array()
	samples.resize(count)
	for i in range(count):
		var t := float(i) / float(RATE)
		var progress := float(i) / float(max(1, count - 1))
		var f := freq * lerpf(1.0, slide, progress)
		var attack := minf(1.0, progress * 30.0)
		var release := pow(1.0 - progress, 1.8)
		var s := sin(TAU * f * t) + 0.18 * sin(TAU * f * 2.0 * t)
		samples[i] = s * attack * release * vol
	return _to_wav(samples)


func _fail_tone() -> AudioStreamWAV:
	var count := int(RATE * 0.32)
	var samples := PackedFloat32Array()
	samples.resize(count)
	for i in range(count):
		var t := float(i) / float(RATE)
		var progress := float(i) / float(max(1, count - 1))
		var f := lerpf(240.0, 170.0, progress)
		var attack := minf(1.0, progress * 25.0)
		var release := pow(1.0 - progress, 1.6)
		var s := sin(TAU * f * t) + 0.35 * sin(TAU * f * 1.015 * t)
		samples[i] = s * attack * release * 0.11
	return _to_wav(samples)


func _chord(freqs: Array, dur: float, vol: float) -> AudioStreamWAV:
	var count := int(RATE * dur)
	var samples := PackedFloat32Array()
	samples.resize(count)
	for i in range(count):
		var t := float(i) / float(RATE)
		var progress := float(i) / float(max(1, count - 1))
		var attack := minf(1.0, progress * 14.0)
		var release := pow(1.0 - progress, 1.5)
		var s := 0.0
		for f in freqs:
			s += sin(TAU * float(f) * t + 0.2) + 0.12 * sin(TAU * float(f) * 2.0 * t)
		samples[i] = s / float(freqs.size()) * attack * release * vol
	return _to_wav(samples)


func _to_wav(samples: PackedFloat32Array) -> AudioStreamWAV:
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	for i in range(samples.size()):
		var v := int(clampf(samples[i], -1.0, 1.0) * 32767.0)
		if v < 0:
			v += 65536
		data[i * 2] = v & 0xFF
		data[i * 2 + 1] = (v >> 8) & 0xFF
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = RATE
	wav.stereo = false
	wav.data = data
	return wav
