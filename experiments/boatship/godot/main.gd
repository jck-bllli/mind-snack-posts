extends Node3D
# "How a Paper Boat Becomes a Cargo Ship" - first beat. Built in Godot 4, fixed 30 fps movie render.

var t := 0.0
var words: Array = []
var total := 6.0
var t_land := 1.7
var t_sag := 3.0
var t_toast := 4.0
var cam: Camera3D
var boat: Node3D
var sail: Node3D
var boat_mat: StandardMaterial3D
var toast: Node3D
var toast_mat: StandardMaterial3D
var sheet: MeshInstance3D
var dave: Node3D
var arm_l: Node3D
var arm_r: Node3D
var ring: MeshInstance3D
var ring_mat: StandardMaterial3D
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
	add_mesh(hs, mk(hat), Vector3(0, 1.31, 0), p)
	for sx in [-1.0, 1.0]:
		var e := SphereMesh.new()
		e.radius = 0.035
		e.height = 0.07
		add_mesh(e, mk(Color("#222222")), Vector3(sx * 0.09, 1.26, 0.22), p)
		add_box(Vector3(0.14, 0.5, 0.16), mk(Color("#34405e")), Vector3(sx * 0.11, 0.25, 0), p)
	arm_l = Node3D.new()
	arm_l.position = Vector3(-0.3, 1.0, 0)
	add_box(Vector3(0.11, 0.42, 0.11), mk(jacket), Vector3(0, -0.2, 0), arm_l)
	p.add_child(arm_l)
	arm_r = Node3D.new()
	arm_r.position = Vector3(0.3, 1.0, 0)
	add_box(Vector3(0.11, 0.42, 0.11), mk(jacket), Vector3(0, -0.2, 0), arm_r)
	p.add_child(arm_r)
	add_child(p)
	return p

func find_word(prefix: String, fallback: float) -> float:
	for w in words:
		if String(w["w"]).to_lower().begins_with(prefix):
			return float(w["t"])
	return fallback

func _ready() -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://timing.json"))
	words = data["words"]
	total = data["total"]
	t_land = data["t_land"]
	t_sag = data["t_sag"]
	t_toast = data["t_toast"]

	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("#bcd9ee")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 1, 1)
	env.ambient_light_energy = 0.55
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, -28, 0)
	sun.light_energy = 1.5
	sun.shadow_enabled = true
	add_child(sun)

	# banks with a canal cut through the front (dirt cross-section like a toy diorama)
	var dirt := mk(Color("#8b5a35"), 1.0)
	var grass := mk(Color("#5faa3a"))
	for side in [-1.0, 1.0]:
		var cx: float = side * 8.75
		add_box(Vector3(12.5, 3.85, 11), dirt, Vector3(cx, -2.075, -2.5))
		add_box(Vector3(12.5, 0.15, 11), grass, Vector3(cx, -0.075, -2.5))
	add_box(Vector3(5, 3.85, 5.5), dirt, Vector3(0, -2.075, -5.25))
	add_box(Vector3(5, 0.15, 5.5), grass, Vector3(0, -0.075, -5.25))
	add_box(Vector3(5, 1.0, 8.5), dirt, Vector3(0, -3.5, -1.25))
	var wmat := mk(Color("#2fa8e6"), 0.15)
	wmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	wmat.albedo_color = Color(0.18, 0.66, 0.9, 0.86)
	add_box(Vector3(5, 2.5, 8.5), wmat, Vector3(0, -1.75, -1.25))
	add_box(Vector3(160, 0.15, 90), grass, Vector3(0, -0.075, -62))
	for i in range(7):
		add_tree(-5.0 - (i % 3) * 1.6, 1.5 - i * 2.2, 0.9 + (i % 4) * 0.15)
		add_tree(5.0 + (i % 3) * 1.6, -0.5 - i * 2.2, 0.9 + ((i + 1) % 4) * 0.15)

	# paper sheet (folds, then becomes the boat)
	sheet = add_box(Vector3(1.3, 0.03, 1.3), mk(Color("#f4f1e8")), Vector3(0, 1.4, 0.5))
	boat_mat = mk(Color("#f4f1e8"))
	boat = Node3D.new()
	add_child(boat)
	add_box(Vector3(1.1, 0.24, 0.5), boat_mat, Vector3(0, 0.12, 0), boat)
	sail = Node3D.new()
	sail.position = Vector3(0, 0.24, 0)
	boat.add_child(sail)
	var pr := PrismMesh.new()
	pr.size = Vector3(0.9, 0.7, 0.06)
	add_mesh(pr, boat_mat, Vector3(0, 0.35, 0), sail)
	boat.visible = false

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

	dave = make_person(Color("#f08a24"), Color("#2a5db0"))
	dave.position = Vector3(3.3, 0, 0.9)
	dave.rotation_degrees = Vector3(0, -35, 0)

	cam = Camera3D.new()
	cam.fov = 50
	add_child(cam)

	var cl := CanvasLayer.new()
	add_child(cl)
	label = Label.new()
	label.set_anchors_preset(Control.PRESET_FULL_RECT)
	label.offset_top = 260
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

func _process(delta: float) -> void:
	t += delta
	var k: float = clamp(t / total, 0.0, 1.0)
	var e: float = k * k * (3.0 - 2.0 * k)
	cam.position = Vector3(0, 5.2, 17.0).lerp(Vector3(0.4, 3.6, 12.5), e)
	cam.look_at(Vector3(0, -0.6, 0).lerp(Vector3(0.2, -0.7, 0), e), Vector3.UP)

	# sheet folds
	var t_drop: float = t_land - 0.55
	sheet.visible = t < t_drop
	var fo: float = clamp(t / max(t_drop - 0.3, 0.1), 0.0, 1.0)
	sheet.scale = Vector3(1.0, 1.0, 1.0 - 0.55 * fo)
	sheet.rotation.y = fo * 0.7
	sheet.position.y = 1.4 + sin(t * 3.0) * 0.05

	# boat drops in, bobs, then goes soggy
	boat.visible = t >= t_drop
	var u: float = clamp((t - t_drop) / 0.55, 0.0, 1.0)
	var by: float = lerp(1.6, -0.5, u * u)
	var dt: float = t - t_land
	var squash := 1.0
	if dt > 0.0 and dt < 0.4:
		squash = 1.0 - 0.18 * sin(dt / 0.4 * PI)
	if dt > 0.0:
		by += sin(t * 2.6) * 0.03
	var sg: float = clamp((t - t_sag) / 1.6, 0.0, 1.0)
	by -= 0.3 * sg
	boat.position = Vector3(0, by, 0)
	boat.scale = Vector3(1, squash, 1)
	boat.rotation_degrees = Vector3(0, 12.0 * sin(t * 0.8), 14.0 * sg)
	sail.rotation_degrees = Vector3(0, 0, -38.0 * sg)
	boat_mat.albedo_color = Color("#f4f1e8").lerp(Color("#8d8776"), sg)

	# splash ring
	var rt: float = t - t_land
	ring.visible = rt > 0.0 and rt < 1.2
	if ring.visible:
		var rs: float = 0.3 + rt * 2.4
		ring.scale = Vector3(rs, 1, rs)
		ring_mat.albedo_color = Color(1, 1, 1, 0.7 * (1.0 - rt / 1.2))

	# soggy toast flops in beside it
	toast.visible = t >= t_toast
	var tu: float = clamp((t - t_toast) / 0.4, 0.0, 1.0)
	toast.position = Vector3(1.35, -0.5 + (1.0 - tu) * (1.0 - tu) * 1.6 + sin(t * 3.0) * 0.02, 0.6)
	toast.rotation_degrees = Vector3(0, 20, 12.0 * sin(t * 2.0) + (1.0 - tu) * 70.0)
	toast_mat.albedo_color = Color("#d9a65a").lerp(Color("#9c7a4a"), clamp((t - t_toast) / 1.0, 0.0, 1.0))

	# Dave watches, shrugs at the toast
	var sh: float = clamp((t - t_toast) / 0.3, 0.0, 1.0)
	arm_l.rotation_degrees = Vector3(0, 0, -50.0 * sh)
	arm_r.rotation_degrees = Vector3(0, 0, 50.0 * sh)
	dave.position.y = abs(sin(t * 3.0)) * 0.02

	# one-word captions
	var idx := -1
	for i in range(words.size()):
		if float(words[i]["t"]) <= t:
			idx = i
	if idx >= 0 and t < float(words[idx]["t"]) + 1.0:
		label.text = String(words[idx]["w"])
		var age: float = t - float(words[idx]["t"])
		var s: float = 1.0 + max(0.0, 0.2 - age) * 1.5
		label.pivot_offset = label.size * 0.5
		label.scale = Vector2(s, s)
	else:
		label.text = ""
