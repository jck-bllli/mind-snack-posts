extends Node3D
# "How a Paper Boat Becomes a Cargo Ship" - full video. Godot 4, fixed 30 fps movie render.
# Every visual event is keyed to a spoken word via timing.json ("T").

var t := 0.0
var words: Array = []
var T := {}
var total := 50.0

var cam: Camera3D
var env: Environment
var sun: DirectionalLight3D
var water_mat: StandardMaterial3D
var sheet: MeshInstance3D
var ship: Node3D
var g_paper: Node3D
var g_wood: Node3D
var g_steel: Node3D
var sail: Node3D
var paper_mat: StandardMaterial3D
var keel: Node3D
var half_b: Node3D
var half_f: Node3D
var containers: Array = []
var ribs: Node3D
var radar: Node3D
var flag: Node3D
var crew: Array = []
var toast: Node3D
var toast_mat: StandardMaterial3D
var ring: MeshInstance3D
var ring_mat: StandardMaterial3D
var wave: MeshInstance3D
var dave: Node3D
var dave_hat: MeshInstance3D
var dave_hat_mat: StandardMaterial3D
var crate: MeshInstance3D
var doc: MeshInstance3D
var fisher: Node3D
var line: MeshInstance3D
var sign_node: Node3D
var booth: Node3D
var money: Label3D
var rain: Array = []
var label: Label

func mk(c: Color, rough := 0.9) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	return m

func add_box(size: Vector3, m: Material, pos: Vector3, parent: Node = null) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = m
	mi.position = pos
	if parent == null:
		parent = self
	parent.add_child(mi)
	return mi

func add_mesh(mesh: Mesh, m: Material, pos: Vector3, parent: Node = null) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = m
	mi.position = pos
	if parent == null:
		parent = self
	parent.add_child(mi)
	return mi

func add_tree(x: float, z: float, s: float) -> void:
	add_box(Vector3(0.35, 1.4, 0.35) * s, mk(Color("#6b4423")), Vector3(x, 0.7 * s, z))
	var g := mk(Color("#2f7d32"))
	for lv in [[1.7, 1.0], [2.4, 0.8], [3.0, 0.55]]:
		var c := CylinderMesh.new()
		c.top_radius = 0.0
		c.bottom_radius = lv[1] * s
		c.height = 1.2 * s
		add_mesh(c, g, Vector3(x, lv[0] * s, z))

func make_person(jacket: Color, hat: Color) -> Node3D:
	var p := Node3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.22
	cap.height = 0.85
	add_mesh(cap, mk(jacket), Vector3(0, 0.75, 0), p)
	var hd := SphereMesh.new()
	hd.radius = 0.24
	hd.height = 0.48
	add_mesh(hd, mk(Color("#f0c9a0")), Vector3(0, 1.28, 0), p)
	var hs := SphereMesh.new()
	hs.radius = 0.26
	hs.height = 0.52
	hs.is_hemisphere = true
	var hm := mk(hat)
	var hnode := add_mesh(hs, hm, Vector3(0, 1.31, 0), p)
	for sx in [-1.0, 1.0]:
		var e := SphereMesh.new()
		e.radius = 0.035
		e.height = 0.07
		add_mesh(e, mk(Color("#222222")), Vector3(sx * 0.09, 1.26, 0.22), p)
		add_box(Vector3(0.14, 0.5, 0.16), mk(Color("#34405e")), Vector3(sx * 0.11, 0.25, 0), p)
	var al := Node3D.new()
	al.position = Vector3(-0.3, 1.0, 0)
	add_box(Vector3(0.11, 0.42, 0.11), mk(jacket), Vector3(0, -0.2, 0), al)
	p.add_child(al)
	var ar := Node3D.new()
	ar.position = Vector3(0.3, 1.0, 0)
	add_box(Vector3(0.11, 0.42, 0.11), mk(jacket), Vector3(0, -0.2, 0), ar)
	p.add_child(ar)
	p.set_meta("al", al)
	p.set_meta("ar", ar)
	p.set_meta("hat", hnode)
	p.set_meta("hatmat", hm)
	add_child(p)
	return p

func label3d(txt: String, size: int, col: Color) -> Label3D:
	var l := Label3D.new()
	l.text = txt
	l.font_size = size
	l.pixel_size = 0.006
	l.modulate = col
	l.outline_size = 10
	l.outline_modulate = Color(0, 0, 0, 0.9)
	var f := SystemFont.new()
	f.font_names = PackedStringArray(["Arial Black", "Impact", "Arial"])
	l.font = f
	return l

func popv(t0: float) -> float:
	var x: float = (t - t0) / 0.35
	if x < 0.0:
		return 0.0
	if x >= 1.0:
		return 1.0
	return 1.0 + sin(x * PI) * 0.18 - (1.0 - x) * (1.0 - x)

func ev(n: String) -> float:
	return float(T[n])

func _ready() -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://timing.json"))
	words = data["words"]
	total = data["total"]
	T = data["T"]

	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("#bcd9ee")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 1, 1)
	env.ambient_light_energy = 0.55
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, -28, 0)
	sun.light_energy = 1.5
	sun.shadow_enabled = true
	add_child(sun)

	var dirt := mk(Color("#8b5a35"), 1.0)
	var grass := mk(Color("#5faa3a"))
	for side in [-1.0, 1.0]:
		var cx: float = side * 8.75
		add_box(Vector3(12.5, 3.85, 11), dirt, Vector3(cx, -2.075, -2.5))
		add_box(Vector3(12.5, 0.15, 11), grass, Vector3(cx, -0.075, -2.5))
	add_box(Vector3(5, 3.85, 5.5), dirt, Vector3(0, -2.075, -5.25))
	add_box(Vector3(5, 0.15, 5.5), grass, Vector3(0, -0.075, -5.25))
	add_box(Vector3(5, 1.0, 8.5), dirt, Vector3(0, -3.5, -1.25))
	water_mat = mk(Color("#2fa8e6"), 0.15)
	water_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	water_mat.albedo_color = Color(0.18, 0.66, 0.9, 0.86)
	add_box(Vector3(5, 2.5, 8.5), water_mat, Vector3(0, -1.75, -1.25))
	add_box(Vector3(160, 0.15, 90), grass, Vector3(0, -0.075, -62))
	for i in range(7):
		add_tree(-5.0 - (i % 3) * 1.6, 1.5 - i * 2.2, 0.9 + (i % 4) * 0.15)
		add_tree(5.0 + (i % 3) * 1.6, -0.5 - i * 2.2, 0.9 + ((i + 1) % 4) * 0.15)

	sheet = add_box(Vector3(1.3, 0.03, 1.3), mk(Color("#f4f1e8")), Vector3(0, 1.4, 0.5))

	# ---- ship: paper -> wood -> steel ----
	ship = Node3D.new()
	add_child(ship)
	paper_mat = mk(Color("#f4f1e8"))
	g_paper = Node3D.new()
	ship.add_child(g_paper)
	add_box(Vector3(1.1, 0.24, 0.5), paper_mat, Vector3(0, 0.12, 0), g_paper)
	sail = Node3D.new()
	sail.position = Vector3(0, 0.24, 0)
	g_paper.add_child(sail)
	var pr := PrismMesh.new()
	pr.size = Vector3(0.9, 0.7, 0.06)
	add_mesh(pr, paper_mat, Vector3(0, 0.35, 0), sail)

	g_wood = Node3D.new()
	ship.add_child(g_wood)
	add_box(Vector3(1.9, 0.38, 0.85), mk(Color("#a9703a")), Vector3(0, 0.19, 0), g_wood)
	add_box(Vector3(1.92, 0.06, 0.87), mk(Color("#6b4423")), Vector3(0, 0.3, 0), g_wood)
	add_box(Vector3(1.92, 0.06, 0.87), mk(Color("#6b4423")), Vector3(0, 0.08, 0), g_wood)
	add_box(Vector3(0.08, 0.9, 0.08), mk(Color("#6b4423")), Vector3(-0.5, 0.8, 0), g_wood)

	g_steel = Node3D.new()
	ship.add_child(g_steel)
	half_b = Node3D.new()
	half_b.position = Vector3(0, 0.3, 0)
	g_steel.add_child(half_b)
	half_f = Node3D.new()
	half_f.position = Vector3(0, 0.3, 0)
	g_steel.add_child(half_f)
	var steel := mk(Color("#5b6b7d"), 0.5)
	var red := mk(Color("#b53a2f"))
	add_box(Vector3(1.9, 0.6, 1.5), steel, Vector3(-0.95, 0, 0), half_b)
	add_box(Vector3(1.92, 0.14, 1.52), red, Vector3(-0.95, -0.2, 0), half_b)
	add_box(Vector3(1.9, 0.6, 1.5), steel, Vector3(0.95, 0, 0), half_f)
	add_box(Vector3(1.92, 0.14, 1.52), red, Vector3(0.95, -0.2, 0), half_f)
	var bow := PrismMesh.new()
	bow.size = Vector3(0.9, 0.6, 1.5)
	var bn := add_mesh(bow, steel, Vector3(2.1, 0, 0), half_f)
	bn.rotation_degrees = Vector3(0, 0, -90)
	add_box(Vector3(0.6, 0.7, 1.0), mk(Color("#f1f1ee")), Vector3(-1.5, 0.65, 0), half_b)
	var fun := CylinderMesh.new()
	fun.top_radius = 0.2
	fun.bottom_radius = 0.22
	fun.height = 0.55
	add_mesh(fun, mk(Color("#c0392b")), Vector3(-1.5, 1.25, 0), half_b)
	radar = Node3D.new()
	radar.position = Vector3(-1.5, 1.7, 0)
	half_b.add_child(radar)
	add_box(Vector3(0.9, 0.06, 0.1), mk(Color("#dddddd")), Vector3(0, 0, 0), radar)
	add_box(Vector3(0.05, 0.3, 0.05), mk(Color("#888888")), Vector3(0, -0.15, 0), half_b)
	radar.visible = false
	flag = Node3D.new()
	flag.position = Vector3(1.8, 0.3, 0)
	half_f.add_child(flag)
	add_box(Vector3(0.05, 1.0, 0.05), mk(Color("#dddddd")), Vector3(0, 0.5, 0), flag)
	add_box(Vector3(0.5, 0.3, 0.03), mk(Color("#e63946")), Vector3(0.27, 0.9, 0), flag)
	var ccols := ["#e63946", "#2a9d8f", "#f4a261", "#457b9d", "#e9c46a", "#8e44ad"]
	var xs := [-0.95, -0.1, 0.75, 1.6]
	for lv in range(3):
		for ci in range(4):
			var par: Node3D = half_b if ci < 2 else half_f
			var cm := mk(Color(ccols[(lv * 2 + ci) % 6]), 0.7)
			var cb := add_box(Vector3(0.75, 0.4, 0.9), cm, Vector3(xs[ci], 0.5 + lv * 0.42, -0.25), par)
			cb.visible = false
			containers.append(cb)
	ribs = Node3D.new()
	g_steel.add_child(ribs)
	for rx in [-1.6, -0.8, 0.0, 0.8, 1.6]:
		add_box(Vector3(0.1, 0.7, 1.56), mk(Color("#f2c200")), Vector3(rx, 0.3, 0), ribs)
	ribs.visible = false
	keel = Node3D.new()
	ship.add_child(keel)
	add_box(Vector3(0.2, 0.6, 0.9), mk(Color("#444c56")), Vector3(0, -0.25, 0), keel)
	keel.visible = false
	for i in range(3):
		var cp := make_person([Color("#2a9d8f"), Color("#e9c46a"), Color("#e63946")][i], Color("#ffffff"))
		cp.scale = Vector3(0.4, 0.4, 0.4)
		cp.visible = false
		crew.append(cp)

	toast_mat = mk(Color("#d9a65a"))
	toast = Node3D.new()
	add_child(toast)
	add_box(Vector3(0.9, 0.12, 0.9), toast_mat, Vector3(0, 0.06, 0), toast)
	add_box(Vector3(0.78, 0.125, 0.78), mk(Color("#f1d9a8")), Vector3(0, 0.065, 0), toast)
	toast.visible = false

	ring_mat = mk(Color(1, 1, 1, 0.7))
	ring_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	var tm := TorusMesh.new()
	tm.inner_radius = 0.9
	tm.outer_radius = 1.0
	ring = add_mesh(tm, ring_mat, Vector3(0, -0.47, 0))
	ring.visible = false
	var wmat := mk(Color(0.55, 0.85, 1.0, 0.75), 0.1)
	wmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	wave = add_box(Vector3(5, 1.1, 0.7), wmat, Vector3(0, -0.1, -3))
	wave.visible = false

	dave = make_person(Color("#f08a24"), Color("#2a5db0"))
	dave.position = Vector3(3.3, 0, 0.9)
	dave.rotation_degrees = Vector3(0, -35, 0)
	dave_hat = dave.get_meta("hat")
	dave_hat_mat = dave.get_meta("hatmat")
	crate = add_box(Vector3(0.6, 0.6, 0.6), mk(Color("#f4a261"), 0.7), Vector3(0, 0, 0))
	crate.visible = false
	doc = add_box(Vector3(0.35, 0.45, 0.03), mk(Color("#ffffff")), Vector3(0, 0, 0))
	doc.visible = false

	fisher = make_person(Color("#2e7d32"), Color("#caa24a"))
	fisher.position = Vector3(-3.4, 0, 0.8)
	fisher.rotation_degrees = Vector3(0, 35, 0)
	fisher.visible = false
	line = add_box(Vector3(0.02, 1.0, 0.02), mk(Color("#222222")), Vector3(0, 0, 0))
	line.visible = false

	sign_node = Node3D.new()
	sign_node.position = Vector3(3.2, 1.4, 2.0)
	add_child(sign_node)
	add_box(Vector3(0.1, 1.4, 0.1), mk(Color("#6b4423")), Vector3(0, -0.7, 0), sign_node)
	add_box(Vector3(1.6, 0.9, 0.08), mk(Color("#ffd23f")), Vector3(0, 0.2, 0), sign_node)
	var sl := label3d("MAX WEIGHT\n5 TONS", 52, Color("#111111"))
	sl.position = Vector3(0, 0.2, 0.06)
	sign_node.add_child(sl)
	sign_node.visible = false

	booth = Node3D.new()
	booth.position = Vector3(4.6, 0, -1.2)
	add_child(booth)
	add_box(Vector3(1.4, 1.5, 1.4), mk(Color("#f4f1e8")), Vector3(0, 0.75, 0), booth)
	add_box(Vector3(1.8, 0.18, 1.8), mk(Color("#c0392b")), Vector3(0, 1.6, 0), booth)
	var bl := label3d("PORT FEE", 52, Color("#c0392b"))
	bl.position = Vector3(0, 1.0, 0.72)
	booth.add_child(bl)
	booth.visible = false

	money = label3d("$6,000,000", 90, Color("#7CFC6B"))
	money.position = Vector3(0, 2.8, 0.6)
	money.visible = false
	add_child(money)

	for i in range(40):
		var rb := add_box(Vector3(0.02, 0.5, 0.02), mk(Color(0.8, 0.9, 1.0, 1.0)), Vector3(0, 0, 0))
		rb.visible = false
		rain.append(rb)

	cam = Camera3D.new()
	cam.fov = 50
	add_child(cam)

	var cl := CanvasLayer.new()
	add_child(cl)
	label = Label.new()
	label.set_anchors_preset(Control.PRESET_FULL_RECT)
	label.offset_top = 300
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 120)
	label.add_theme_color_override("font_color", Color(1, 1, 1))
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	label.add_theme_constant_override("outline_size", 28)
	var f := SystemFont.new()
	f.font_names = PackedStringArray(["Arial Black", "Impact", "Arial"])
	label.add_theme_font_override("font", f)
	cl.add_child(label)

func set_arms(p: Node3D, l: float, r: float) -> void:
	(p.get_meta("al") as Node3D).rotation_degrees = Vector3(0, 0, l)
	(p.get_meta("ar") as Node3D).rotation_degrees = Vector3(0, 0, r)

func _process(delta: float) -> void:
	t += delta
	var fin: bool = t >= ev("final")

	# ---- camera: slow pull back, aimed so the diorama sits lower in the frame ----
	var k: float = clamp(t / total, 0.0, 1.0)
	var e: float = k * k * (3.0 - 2.0 * k)
	cam.position = Vector3(0, 4.4, 14.8).lerp(Vector3(0.2, 4.0, 14.2), e)
	cam.look_at(Vector3(0, 1.3, 0).lerp(Vector3(0, 1.1, 0), e), Vector3.UP)

	# ---- sky / storm ----
	var storm: float = 0.0
	if t > ev("storm") and t < ev("radar") + 1.0:
		storm = smoothstep(ev("storm"), ev("storm") + 0.6, t) * (1.0 - smoothstep(ev("bulk") + 0.5, ev("radar"), t))
	env.background_color = Color("#bcd9ee").lerp(Color("#58687a"), storm)
	sun.light_energy = 1.5 - 0.9 * storm
	var flash: float = 0.0
	if t > ev("storm") + 0.3 and t < ev("storm") + 0.45:
		flash = 1.0
	env.ambient_light_energy = 0.55 + flash * 2.5 - 0.15 * storm
	for i in range(rain.size()):
		var rb: MeshInstance3D = rain[i]
		rb.visible = storm > 0.2
		if rb.visible:
			var px: float = -3.5 + fmod(float(i) * 1.7, 7.0)
			var pz: float = -2.0 + fmod(float(i) * 2.3, 5.0)
			var py: float = 5.0 - fmod(t * 11.0 + float(i) * 0.9, 6.0)
			rb.position = Vector3(px, py, pz)

	# ---- paper sheet: folds at the start and again at the very end ----
	var t_drop: float = ev("land") - 0.55
	var t_fold_end: float = t_drop
	var fo: float = clamp(t / max(t_drop - 0.3, 0.1), 0.0, 1.0)
	sheet.visible = t < t_drop
	if fin:
		sheet.visible = true
		fo = clamp((t - ev("final")) / 0.7, 0.0, 1.0)
	sheet.scale = Vector3(1.0, 1.0, 1.0 - 0.55 * fo)
	sheet.rotation.y = fo * 0.7
	sheet.position.y = 1.4 + sin(t * 3.0) * 0.05

	# ---- which ship stage is showing ----
	var paper_on: bool = t >= t_drop and t < ev("hull")
	var wood_on: bool = t >= ev("hull") and t < ev("steel")
	var steel_on: bool = t >= ev("steel")
	g_paper.visible = paper_on
	g_wood.visible = wood_on
	g_steel.visible = steel_on
	g_wood.scale = Vector3.ONE * max(popv(ev("hull")), 0.001)
	g_steel.scale = Vector3.ONE * max(popv(ev("steel")), 0.001)
	keel.visible = t >= ev("keel")
	keel.scale = Vector3.ONE * max(popv(ev("keel")), 0.001)
	ribs.visible = t >= ev("bulk")
	ribs.scale = Vector3.ONE * max(popv(ev("bulk")), 0.001)
	radar.visible = t >= ev("radar")
	radar.rotation.y = t * 4.0
	flag.visible = t >= ev("flag")
	flag.scale = Vector3.ONE * max(popv(ev("flag")), 0.001)

	# ---- ship motion ----
	var u: float = clamp((t - t_drop) / 0.55, 0.0, 1.0)
	var base: float = -0.5
	if steel_on:
		base = -0.6
	var by: float = base
	if paper_on or t < t_drop + 0.55:
		by = lerp(1.6, base, u * u)
	var dt: float = t - ev("land")
	var squash: float = 1.0
	if dt > 0.0 and dt < 0.4:
		squash = 1.0 - 0.18 * sin(dt / 0.4 * PI)
	if dt > 0.0:
		by += sin(t * 2.6) * 0.03
	var sg: float = clamp((t - ev("sag")) / 1.6, 0.0, 1.0)
	if paper_on:
		by -= 0.3 * sg
		g_paper.rotation_degrees = Vector3(0, 12.0 * sin(t * 0.8), 14.0 * sg)
		sail.rotation_degrees = Vector3(0, 0, -38.0 * sg)
		paper_mat.albedo_color = Color("#f4f1e8").lerp(Color("#8d8776"), sg)
	var n_cont: int = 0
	for i in range(containers.size()):
		var cb: MeshInstance3D = containers[i]
		var tc: float = ev("cont") + float(i) * 0.09
		cb.visible = t >= tc and steel_on
		cb.scale = Vector3.ONE * max(popv(tc), 0.001)
		if cb.visible:
			n_cont += 1
	by -= 0.03 * float(n_cont)

	var sx: float = 0.0
	var rot_z: float = 0.0
	# the wave flips the boat, the fisherman catches it, the keel rights it
	var t_w: float = ev("wave")
	var t_k: float = ev("keel")
	if t >= t_w and t < t_k:
		rot_z = 180.0 * smoothstep(t_w, t_w + 0.8, t)
		var lu: float = smoothstep(ev("fisher"), ev("fisher") + 0.9, t)
		sx = -1.8 * lu
		by += 2.3 * lu
	elif t >= t_k and t < t_k + 0.8:
		var ru: float = smoothstep(t_k, t_k + 0.8, t)
		rot_z = 180.0 * (1.0 - ru)
		sx = -1.8 * (1.0 - ru)
		by += 2.3 * (1.0 - ru)
	# storm rocking and bend
	var bend: float = 0.0
	if t > ev("storm") + 0.5:
		bend = smoothstep(ev("storm") + 0.5, ev("storm") + 1.4, t) * (1.0 - smoothstep(ev("bulk"), ev("bulk") + 0.5, t))
	if t > ev("storm") and t < ev("bulk") + 0.5:
		rot_z += 5.0 * sin(t * 4.0)
	half_b.rotation_degrees = Vector3(0, 0, 13.0 * bend)
	half_f.rotation_degrees = Vector3(0, 0, -13.0 * bend)
	var ship_vis: bool = (paper_on or wood_on or steel_on) and not fin
	if fin:
		ship_vis = t < ev("final") + 0.3
	ship.visible = ship_vis
	ship.position = Vector3(sx, by, 0)
	ship.rotation_degrees = Vector3(0, 0, rot_z)
	ship.scale = Vector3(1, squash, 1)
	if fin:
		ship.scale = Vector3.ONE * max(1.0 - (t - ev("final")) / 0.3, 0.001)

	# crew on deck
	for i in range(crew.size()):
		var cp: Node3D = crew[i]
		cp.visible = t >= ev("crew") and not fin
		cp.scale = Vector3.ONE * 0.4 * max(popv(ev("crew") + float(i) * 0.12), 0.001)
		cp.position = ship.position + Vector3(-0.4 + float(i) * 0.5, 1.95 + 0.0, 0.0)
		cp.rotation_degrees = Vector3(0, -20, 0)

	# ---- splash ring on every big splash ----
	ring.visible = false
	for name in ["land", "swim"]:
		var rt: float = t - ev(name)
		if rt > 0.0 and rt < 1.2:
			ring.visible = true
			var rs: float = 0.3 + rt * 2.4
			ring.scale = Vector3(rs, 1, rs)
			ring_mat.albedo_color = Color(1, 1, 1, 0.7 * (1.0 - rt / 1.2))
			ring.position = Vector3(0.0 if name == "land" else 1.0, -0.47, 0.0 if name == "land" else 0.6)

	# ---- wave ----
	var wt: float = t - (t_w - 0.5)
	wave.visible = wt > 0.0 and wt < 2.0
	if wave.visible:
		wave.position = Vector3(0, -0.1 + sin(wt / 2.0 * PI) * 0.5, -3.0 + wt * 2.4)

	# ---- soggy toast ----
	toast.visible = t >= ev("toast") and not fin
	var tu: float = clamp((t - ev("toast")) / 0.4, 0.0, 1.0)
	toast.position = Vector3(1.35, -0.5 + (1.0 - tu) * (1.0 - tu) * 1.6 + sin(t * 3.0) * 0.02, 0.6)
	toast.rotation_degrees = Vector3(0, 20, 12.0 * sin(t * 2.0) + (1.0 - tu) * 70.0)
	toast_mat.albedo_color = Color("#d9a65a").lerp(Color("#9c7a4a"), clamp((t - ev("toast")) / 1.0, 0.0, 1.0))
	if t > ev("hull"):
		toast.visible = toast.visible and t < ev("hull") + 0.01 and false

	# ---- fisherman and line ----
	fisher.visible = t >= ev("fisher") - 0.3 and t < ev("keel") + 1.5
	line.visible = t >= ev("fisher") and t < ev("keel") + 0.2
	if line.visible:
		var p0 := Vector3(-2.7, 2.3, 0.7)
		var p1: Vector3 = ship.position + Vector3(0, 0.3, 0)
		var d: Vector3 = p0 - p1
		line.position = (p0 + p1) * 0.5
		line.scale = Vector3(1, d.length(), 1)
		line.rotation.z = -atan2(d.x, d.y)
	set_arms(fisher, 0.0, 150.0 if line.visible else 0.0)

	# ---- sign, booth, money ----
	sign_node.visible = t >= ev("sign") and not fin
	sign_node.scale = Vector3.ONE * max(popv(ev("sign")), 0.001)
	var flipu: float = smoothstep(ev("upside"), ev("upside") + 0.5, t)
	sign_node.rotation_degrees = Vector3(0, -15, 180.0 * flipu)
	booth.visible = t >= ev("fee")
	booth.scale = Vector3.ONE * max(popv(ev("fee")), 0.001)
	money.visible = t >= ev("million") and t < ev("sue") + 1.5 and not fin
	money.position = Vector3(0, 3.2 + sin(t * 3.0) * 0.08, 0.6)

	# ---- Dave ----
	var hat_up: bool = t >= ev("captain")
	dave_hat_mat.albedo_color = Color("#ffffff") if hat_up else Color("#2a5db0")
	dave_hat.scale = Vector3(1.5, 1.2, 1.5) if hat_up else Vector3.ONE
	crate.visible = false
	doc.visible = false
	var dp := Vector3(3.3, 0, 0.9)
	var dsc: float = 1.0
	var ay: float = -35.0
	var arms_l: float = 0.0
	var arms_r: float = 0.0
	var tsw: float = ev("swim")
	if t < tsw:
		var sh: float = clamp((t - ev("toast")) / 0.3, 0.0, 1.0)
		if t >= ev("toast"):
			arms_l = -50.0 * sh
			arms_r = 50.0 * sh
		dp.y = abs(sin(t * 3.0)) * 0.02
	elif t < tsw + 0.6:
		var ju: float = (t - tsw) / 0.6
		dp = Vector3(3.3, 0, 0.9).lerp(Vector3(1.0, -0.55, 0.6), ju)
		dp.y += sin(ju * PI) * 1.3
		arms_l = -100.0
		arms_r = 100.0
	elif t < ev("hull"):
		dp = Vector3(1.0, -0.55 + sin(t * 3.0) * 0.05, 0.6)
		arms_l = -80.0 - 30.0 * sin(t * 14.0)
		arms_r = 80.0 + 30.0 * sin(t * 14.0 + 1.0)
	elif t < t_w:
		dp = ship.position + Vector3(0.1, 0.38, 0.0)
		dp.y += 0.0
		if t >= ev("captain"):
			arms_l = -20.0
			arms_r = 20.0
	elif t < ev("steer") - 0.6:
		dp = Vector3(1.8, -0.55 + sin(t * 3.0) * 0.05, 0.9)
		arms_l = -80.0 - 30.0 * sin(t * 14.0)
		arms_r = 80.0 + 30.0 * sin(t * 14.0 + 1.0)
	elif t < ev("steer"):
		var bu: float = (t - (ev("steer") - 0.6)) / 0.6
		var deck: Vector3 = ship.position + Vector3(0.9, 0.6, 0.5)
		dp = Vector3(1.8, -0.55, 0.9).lerp(deck, bu)
		dp.y += sin(bu * PI) * 1.0
	elif t < ev("sue"):
		var deck2: Vector3 = ship.position + Vector3(0.9, 0.6, 0.5)
		dp = deck2
		if t >= ev("cargo"):
			dsc = 0.5
			dp.y += 0.3
			crate.visible = true
			crate.position = ship.position + Vector3(0.9, 0.9, 0.5)
			crate.scale = Vector3.ONE * max(popv(ev("cargo")), 0.001)
		else:
			arms_l = -30.0
			arms_r = 30.0
	elif t < ev("sue") + 0.6:
		var su: float = (t - ev("sue")) / 0.6
		var deck3: Vector3 = ship.position + Vector3(0.9, 1.2, 0.5)
		dp = deck3.lerp(Vector3(3.0, 0, 1.4), su)
		dp.y += sin(su * PI) * 1.3
	else:
		dp = Vector3(3.0, 0, 1.4)
		ay = -40.0
		arms_l = 0.0
		arms_r = 150.0 + 25.0 * sin(t * 16.0)
		doc.visible = true
		doc.position = dp + Vector3(0.3, 1.9, 0.1)
		doc.scale = Vector3.ONE * max(popv(ev("sue") + 0.6), 0.001)
	if fin:
		dp = Vector3(3.3, 0, 0.9)
		dsc = 1.0
		ay = -35.0
		arms_l = 0.0
		arms_r = 0.0
		doc.visible = false
		crate.visible = false
		dave_hat_mat.albedo_color = Color("#2a5db0")
		dave_hat.scale = Vector3.ONE
	dave.position = dp
	dave.scale = Vector3.ONE * dsc
	dave.rotation_degrees = Vector3(0, ay, 0)
	set_arms(dave, arms_l, arms_r)

	# ---- one-word captions ----
	var idx := -1
	for i in range(words.size()):
		if float(words[i]["t"]) <= t:
			idx = i
	if idx >= 0 and t < float(words[idx]["t"]) + 1.0:
		label.text = String(words[idx]["w"])
		label.add_theme_font_size_override("font_size", int(min(120.0, 120.0 * 6.0 / float(max(label.text.length(), 1)))))
		var age: float = t - float(words[idx]["t"])
		var s: float = 1.0 + max(0.0, 0.2 - age) * 1.5
		label.pivot_offset = label.size * 0.5
		label.scale = Vector2(s, s)
	else:
		label.text = ""
