# "Moon Bay": one path-traced environment frame (original art).
# Electric-blue night sea, glowing bioluminescent surf, basalt sea stacks, giant moon.
# Built procedurally in Blender 4.2 LTS, rendered with Cycles on the home PC GPU.
#
# Usage (Windows, from C:\runners\environment-frame):
#   blender.exe -b -P moon_bay.py -- --preview        (540x960, 64 samples, composition check)
#   blender.exe -b -P moon_bay.py -- --final          (2160x3840, heavy samples)
# Output: renders\moon_bay_<mode>.png (16-bit) next to this script.

import bpy, math, os, sys, random
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = "final" if "--final" in argv else "preview"
SAMPLES = int(next((a.split("=")[1] for a in argv if a.startswith("--samples=")), 0)) or (4096 if MODE == "final" else 64)
HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(7)

# ---------- reset ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links

def node(nodes, kind, loc=(0, 0), **inputs):
    n = nodes.new(kind)
    n.location = loc
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n

# ---------- camera ----------
CAM_POS = Vector((0, -6, 1.4))
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 26
cam_data.sensor_fit = "VERTICAL"
cam_data.sensor_height = 36
cam_data.clip_end = 6000
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
cam.location = CAM_POS
cam.rotation_euler = (math.radians(90 + 9), 0, math.radians(-4))
scene.camera = cam

def dir_from(az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    return Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))

# ---------- moon ----------
MOON_DIR = dir_from(-2, 23)
MOON_DIST = 2400
moon_r = MOON_DIST * math.tan(math.radians(7.0))
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=moon_r,
                                     location=CAM_POS + MOON_DIR * MOON_DIST)
moon = bpy.context.object
moon.name = "moon"
bpy.ops.object.shade_smooth()
m, n, l = mat("moon")
n.clear()
out = node(n, "ShaderNodeOutputMaterial", (900, 0))
emit = node(n, "ShaderNodeEmission", (700, 0))
tc = node(n, "ShaderNodeTexCoord", (-700, 0))
maria = node(n, "ShaderNodeTexNoise", (-500, 100), Scale=1.6, Detail=8.0, Roughness=0.62)
craters = node(n, "ShaderNodeTexVoronoi", (-500, -150), Scale=9.0)
ramp = node(n, "ShaderNodeValToRGB", (-250, 100))
ramp.color_ramp.elements[0].position = 0.42
ramp.color_ramp.elements[0].color = (0.10, 0.28, 0.95, 1)
ramp.color_ramp.elements[1].position = 0.62
ramp.color_ramp.elements[1].color = (0.62, 0.85, 1.0, 1)
cr = node(n, "ShaderNodeValToRGB", (-250, -150))
cr.color_ramp.elements[0].position = 0.0
cr.color_ramp.elements[0].color = (0.55, 0.55, 0.55, 1)
cr.color_ramp.elements[1].position = 0.18
cr.color_ramp.elements[1].color = (1, 1, 1, 1)
mul = node(n, "ShaderNodeMix", (100, 0))
mul.data_type = "RGBA"
mul.blend_type = "MULTIPLY"
mul.inputs["Factor"].default_value = 1.0
# limb darkening via facing
lw = node(n, "ShaderNodeLayerWeight", (100, -250))
lw.inputs["Blend"].default_value = 0.35
limb = node(n, "ShaderNodeMath", (350, -250), )
limb.operation = "SUBTRACT"
limb.inputs[0].default_value = 1.15
strength = node(n, "ShaderNodeMath", (500, -250))
strength.operation = "MULTIPLY"
strength.inputs[1].default_value = 9.0
l.new(tc.outputs["Object"], maria.inputs["Vector"])
l.new(tc.outputs["Object"], craters.inputs["Vector"])
l.new(maria.outputs["Fac"], ramp.inputs["Fac"])
l.new(craters.outputs["Distance"], cr.inputs["Fac"])
l.new(ramp.outputs["Color"], mul.inputs[6])
l.new(cr.outputs["Color"], mul.inputs[7])
l.new(mul.outputs[2], emit.inputs["Color"])
l.new(lw.outputs["Facing"], limb.inputs[1])
l.new(limb.outputs[0], strength.inputs[0])
l.new(strength.outputs[0], emit.inputs["Strength"])
l.new(emit.outputs[0], out.inputs["Surface"])
moon.data.materials.append(m)
moon.visible_shadow = False

# moonlight
sun_data = bpy.data.lights.new("moonlight", "SUN")
sun_data.energy = 0.9
sun_data.color = (0.45, 0.62, 1.0)
sun_data.angle = math.radians(4)
sun = bpy.data.objects.new("moonlight", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (-MOON_DIR).to_track_quat("-Z", "Y").to_euler()

# cool violet rim fill from behind camera, very low
rim_data = bpy.data.lights.new("rim", "SUN")
rim_data.energy = 0.12
rim_data.color = (0.45, 0.3, 1.0)
rim = bpy.data.objects.new("rim", rim_data)
scene.collection.objects.link(rim)
rim.rotation_euler = (math.radians(70), 0, math.radians(200))

# ---------- ocean ----------
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
ocean = bpy.context.object
ocean.name = "ocean"
om = ocean.modifiers.new("ocean", "OCEAN")
om.geometry_mode = "GENERATE"
om.resolution = 24 if MODE == "final" else 12
om.spatial_size = 80
om.repeat_x = 5
om.repeat_y = 6
om.wave_scale = 0.55
om.choppiness = 1.25
om.wind_velocity = 14
om.wave_alignment = 0.35
om.wave_direction = math.radians(-100)
om.time = 11.0
om.random_seed = 3
om.use_normals = True
om.use_foam = True
om.foam_coverage = 0.25
om.foam_layer_name = "foam"
ocean.location = (-160, 20, 0)  # generated grid then spans x -200..200, y -20..460
bpy.ops.object.shade_smooth()

m, n, l = mat("water")
n.clear()
out = node(n, "ShaderNodeOutputMaterial", (900, 0))
bsdf = node(n, "ShaderNodeBsdfPrincipled", (500, 0))
bsdf.inputs["Base Color"].default_value = (0.002, 0.008, 0.03, 1)
bsdf.inputs["Roughness"].default_value = 0.04
bsdf.inputs["IOR"].default_value = 1.333
bsdf.inputs["Specular IOR Level"].default_value = 0.6
foam = node(n, "ShaderNodeAttribute", (-600, 0))
foam.attribute_name = "foam"
fn = node(n, "ShaderNodeTexNoise", (-600, -250), Scale=3.0, Detail=10.0, Roughness=0.7)
fmix = node(n, "ShaderNodeMath", (-350, 0))
fmix.operation = "MULTIPLY"
framp = node(n, "ShaderNodeValToRGB", (-150, 0))
framp.color_ramp.elements[0].position = 0.06
framp.color_ramp.elements[0].color = (0, 0, 0, 1)
framp.color_ramp.elements[1].position = 0.55
framp.color_ramp.elements[1].color = (0.25, 0.75, 1.0, 1)
mid = framp.color_ramp.elements.new(0.2)
mid.color = (0.03, 0.12, 0.9, 1)
l.new(foam.outputs["Fac"], fmix.inputs[0])
l.new(fn.outputs["Fac"], fmix.inputs[1])
fmix.inputs[1].default_value = 1.0
l.new(fmix.outputs[0], framp.inputs["Fac"])
l.new(framp.outputs["Color"], bsdf.inputs["Emission Color"])
bsdf.inputs["Emission Strength"].default_value = 7.0
# micro ripples
rip = node(n, "ShaderNodeTexNoise", (-150, -350), Scale=60.0, Detail=6.0)
bump = node(n, "ShaderNodeBump", (250, -300), Strength=0.08, Distance=0.02)
l.new(rip.outputs["Fac"], bump.inputs["Height"])
l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
l.new(bsdf.outputs[0], out.inputs["Surface"])
ocean.data.materials.append(m)

# far water out to the horizon (flat glossy, bump only)
bpy.ops.mesh.primitive_plane_add(size=9000, location=(0, 0, -2.5))
far = bpy.context.object
far.name = "far_water"
m2, n2, l2 = mat("far_water")
b2 = n2["Principled BSDF"]
b2.inputs["Base Color"].default_value = (0.002, 0.008, 0.03, 1)
b2.inputs["Roughness"].default_value = 0.09
b2.inputs["IOR"].default_value = 1.333
w2 = node(n2, "ShaderNodeTexWave", (-500, -300), Scale=0.08, Distortion=6.0, Detail=6.0)
bp2 = node(n2, "ShaderNodeBump", (-200, -300), Strength=0.25)
l2.new(w2.outputs["Fac"], bp2.inputs["Height"])
l2.new(bp2.outputs["Normal"], b2.inputs["Normal"])
far.data.materials.append(m2)

# ---------- rock material ----------
rm, rn, rl = mat("basalt")
rb = rn["Principled BSDF"]
rtc = node(rn, "ShaderNodeTexCoord", (-900, 0))
rnoise = node(rn, "ShaderNodeTexNoise", (-700, 100), Scale=1.5, Detail=12.0, Roughness=0.65)
rvor = node(rn, "ShaderNodeTexVoronoi", (-700, -200), Scale=5.0)
rvor.feature = "DISTANCE_TO_EDGE"
rcol = node(rn, "ShaderNodeValToRGB", (-400, 100))
rcol.color_ramp.elements[0].color = (0.006, 0.008, 0.014, 1)
rcol.color_ramp.elements[1].color = (0.05, 0.06, 0.09, 1)
rrough = node(rn, "ShaderNodeMapRange", (-400, -100))
rrough.inputs["To Min"].default_value = 0.25  # wet low parts
rrough.inputs["To Max"].default_value = 0.8
rsep = node(rn, "ShaderNodeSeparateXYZ", (-700, 300))
wet = node(rn, "ShaderNodeMapRange", (-400, 300))
wet.inputs["From Min"].default_value = 0.0
wet.inputs["From Max"].default_value = 2.5
rl.new(rtc.outputs["Object"], rnoise.inputs["Vector"])
rl.new(rtc.outputs["Object"], rvor.inputs["Vector"])
rl.new(rnoise.outputs["Fac"], rcol.inputs["Fac"])
rl.new(rcol.outputs["Color"], rb.inputs["Base Color"])
rl.new(rtc.outputs["Generated"], rsep.inputs["Vector"])
rl.new(rsep.outputs["Z"], rrough.inputs["Value"])
rl.new(rrough.outputs["Result"], rb.inputs["Roughness"])
rbump = node(rn, "ShaderNodeBump", (-150, -300), Strength=0.6, Distance=0.3)
rl.new(rvor.outputs["Distance"], rbump.inputs["Height"])
rl.new(rbump.outputs["Normal"], rb.inputs["Normal"])

clouds = bpy.data.textures.new("rock_clouds", "CLOUDS")
clouds.noise_scale = 0.9
clouds.noise_depth = 6
cells = bpy.data.textures.new("rock_cells", "VORONOI")
cells.noise_scale = 0.45
cells.distance_metric = "DISTANCE"

def rock(loc, scale, rot_z=0.0, seed=0, subdiv=5):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1, location=loc)
    o = bpy.context.object
    o.scale = scale
    o.rotation_euler = (random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), rot_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    d1 = o.modifiers.new("big", "DISPLACE")
    d1.texture = clouds
    d1.strength = max(scale) * 0.22
    d1.texture_coords = "GLOBAL"
    d2 = o.modifiers.new("cells", "DISPLACE")
    d2.texture = cells
    d2.strength = -max(scale) * 0.10
    d2.texture_coords = "GLOBAL"
    o.location.x += seed * 0.0  # keep deterministic
    bpy.ops.object.shade_smooth()
    o.data.materials.append(rm)
    return o

# sea stacks (tall, jagged), receding into the bay
stacks = [
    ((-18, 60, 6), (5, 5, 16)),
    ((-38, 120, 10), (8, 7, 26)),
    ((26, 85, 8), (6, 5, 22)),
    ((55, 170, 14), (11, 9, 34)),
    ((-75, 220, 12), (14, 12, 30)),
    ((12, 260, 9), (7, 7, 20)),
    ((95, 300, 18), (16, 13, 44)),
    ((-130, 340, 15), (18, 15, 38)),
]
for i, (loc, sc) in enumerate(stacks):
    rock(loc, sc, rot_z=random.uniform(0, 6.28), seed=i)
# foreground shore rocks, half submerged, catching moon rim light
for loc, sc in [((-4.2, 3, -0.2), (2.4, 1.8, 1.3)), ((3.8, 6, -0.3), (1.7, 1.5, 1.0)),
                ((-1.5, 0.5, -0.6), (1.4, 1.1, 0.7)), ((6.5, 12, -0.3), (2.6, 2.0, 1.6)),
                ((-9, 16, -0.4), (3.2, 2.5, 2.2))]:
    rock(loc, sc, rot_z=random.uniform(0, 6.28), subdiv=6)

# ---------- low sea mist (volume) ----------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 300, 12))
mist = bpy.context.object
mist.name = "mist"
mist.scale = (1400, 700, 24)
vm, vn, vl = mat("mist")
vn.clear()
vout = node(vn, "ShaderNodeOutputMaterial", (600, 0))
vol = node(vn, "ShaderNodeVolumePrincipled", (300, 0))
vol.inputs["Color"].default_value = (0.35, 0.55, 1.0, 1)
vol.inputs["Anisotropy"].default_value = 0.65
vtc = node(vn, "ShaderNodeTexCoord", (-700, 0))
vsep = node(vn, "ShaderNodeSeparateXYZ", (-500, 0))
vfall = node(vn, "ShaderNodeMapRange", (-300, 0))
vfall.inputs["From Min"].default_value = 0.0
vfall.inputs["From Max"].default_value = 0.6
vfall.inputs["To Min"].default_value = 1.0
vfall.inputs["To Max"].default_value = 0.0
vnz = node(vn, "ShaderNodeTexNoise", (-300, -250), Scale=6.0, Detail=4.0)
vm1 = node(vn, "ShaderNodeMath", (-80, 0))
vm1.operation = "MULTIPLY"
vm2 = node(vn, "ShaderNodeMath", (100, 0))
vm2.operation = "MULTIPLY"
vm2.inputs[1].default_value = 0.0035
vl.new(vtc.outputs["Generated"], vsep.inputs["Vector"])
vl.new(vtc.outputs["Generated"], vnz.inputs["Vector"])
vl.new(vsep.outputs["Z"], vfall.inputs["Value"])
vl.new(vfall.outputs["Result"], vm1.inputs[0])
vl.new(vnz.outputs["Fac"], vm1.inputs[1])
vl.new(vm1.outputs[0], vm2.inputs[0])
vl.new(vm2.outputs[0], vol.inputs["Density"])
vl.new(vol.outputs[0], vout.inputs["Volume"])
mist.data.materials.append(vm)

# ---------- sky ----------
world = bpy.data.worlds.new("night")
scene.world = world
world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
wn.clear()
wout = node(wn, "ShaderNodeOutputWorld", (1200, 0))
bg = node(wn, "ShaderNodeBackground", (1000, 0))
wtc = node(wn, "ShaderNodeTexCoord", (-1000, 0))
wsep = node(wn, "ShaderNodeSeparateXYZ", (-800, 200))
# base gradient: bright electric blue at horizon, near black above
grad = node(wn, "ShaderNodeValToRGB", (-550, 250))
e = grad.color_ramp.elements
e[0].position = 0.0
e[0].color = (0.04, 0.10, 0.55, 1)
e[1].position = 0.55
e[1].color = (0.0005, 0.001, 0.008, 1)
e.new(0.12).color = (0.012, 0.03, 0.22, 1)
# nebula wisps
neb = node(wn, "ShaderNodeTexNoise", (-800, -50), Scale=2.2, Detail=12.0, Roughness=0.62, Distortion=0.8)
nramp = node(wn, "ShaderNodeValToRGB", (-550, -50))
nramp.color_ramp.elements[0].position = 0.5
nramp.color_ramp.elements[0].color = (0, 0, 0, 1)
nramp.color_ramp.elements[1].position = 0.8
nramp.color_ramp.elements[1].color = (0.06, 0.08, 0.6, 1)
nv = nramp.color_ramp.elements.new(0.66)
nv.color = (0.05, 0.015, 0.25, 1)
# stars
svor = node(wn, "ShaderNodeTexVoronoi", (-800, -350), Scale=420.0)
sthr = node(wn, "ShaderNodeMath", (-550, -300))
sthr.operation = "GREATER_THAN"
sthr.inputs[1].default_value = 0.93
ssep = node(wn, "ShaderNodeSeparateColor", (-650, -450))
sdot = node(wn, "ShaderNodeMapRange", (-550, -500))
sdot.inputs["From Min"].default_value = 0.0
sdot.inputs["From Max"].default_value = 0.09
sdot.inputs["To Min"].default_value = 1.0
sdot.inputs["To Max"].default_value = 0.0
smul = node(wn, "ShaderNodeMath", (-350, -350))
smul.operation = "MULTIPLY"
sbright = node(wn, "ShaderNodeMath", (-200, -350))
sbright.operation = "MULTIPLY"
sbright.inputs[1].default_value = 6.0
# stars only above horizon
hz = node(wn, "ShaderNodeMapRange", (-550, 450))
hz.inputs["From Min"].default_value = 0.0
hz.inputs["From Max"].default_value = 0.08
smul2 = node(wn, "ShaderNodeMath", (-50, -350))
smul2.operation = "MULTIPLY"
add1 = node(wn, "ShaderNodeMix", (300, 100))
add1.data_type = "RGBA"
add1.blend_type = "ADD"
add1.inputs["Factor"].default_value = 1.0
nmask = node(wn, "ShaderNodeMix", (100, -50))
nmask.data_type = "RGBA"
nmask.blend_type = "MULTIPLY"
nmask.inputs["Factor"].default_value = 1.0
add2 = node(wn, "ShaderNodeMix", (600, 0))
add2.data_type = "RGBA"
add2.blend_type = "ADD"
add2.inputs["Factor"].default_value = 1.0
starcol = node(wn, "ShaderNodeMix", (300, -350))
starcol.data_type = "RGBA"
starcol.blend_type = "MULTIPLY"
starcol.inputs["Factor"].default_value = 1.0
starcol.inputs[7].default_value = (0.7, 0.85, 1.0, 1)

wl.new(wtc.outputs["Generated"], wsep.inputs["Vector"])
wl.new(wsep.outputs["Z"], grad.inputs["Fac"])
wl.new(wtc.outputs["Generated"], neb.inputs["Vector"])
wl.new(neb.outputs["Fac"], nramp.inputs["Fac"])
wl.new(wtc.outputs["Generated"], svor.inputs["Vector"])
wl.new(svor.outputs["Color"], ssep.inputs["Color"])
wl.new(ssep.outputs["Red"], sthr.inputs[0])
wl.new(svor.outputs["Distance"], sdot.inputs["Value"])
wl.new(sthr.outputs[0], smul.inputs[0])
wl.new(sdot.outputs["Result"], smul.inputs[1])
wl.new(smul.outputs[0], sbright.inputs[0])
wl.new(wsep.outputs["Z"], hz.inputs["Value"])
wl.new(sbright.outputs[0], smul2.inputs[0])
wl.new(hz.outputs["Result"], smul2.inputs[1])
wl.new(nramp.outputs["Color"], nmask.inputs[6])
wl.new(hz.outputs["Result"], nmask.inputs[7])
wl.new(grad.outputs["Color"], add1.inputs[6])
wl.new(nmask.outputs[2], add1.inputs[7])
wl.new(smul2.outputs[0], starcol.inputs[6])
wl.new(add1.outputs[2], add2.inputs[6])
wl.new(starcol.outputs[2], add2.inputs[7])
wl.new(add2.outputs[2], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0
wl.new(bg.outputs[0], wout.inputs["Surface"])

# ---------- render settings ----------
scene.render.engine = "CYCLES"
cy = scene.cycles
prefs = bpy.context.preferences.addons["cycles"].preferences
device_type = None
for t in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = t
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == t]
        if gpus:
            for d in prefs.devices:
                d.use = d.type == t
            device_type = t
            break
    except Exception:
        pass
cy.device = "GPU" if device_type else "CPU"
print(f"[moon_bay] device: {device_type or 'CPU'}  mode: {MODE}  samples: {SAMPLES}")

cy.samples = SAMPLES
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.004 if MODE == "final" else 0.05
cy.use_denoising = True
cy.denoiser = "OPENIMAGEDENOISE"
cy.max_bounces = 16
cy.glossy_bounces = 8
cy.transmission_bounces = 12
cy.volume_bounces = 2
cy.caustics_reflective = True
cy.blur_glossy = 0.6
cy.volume_step_rate = 1.0 if MODE == "final" else 4.0
cy.tile_size = 1024

r = scene.render
if MODE == "final":
    r.resolution_x, r.resolution_y = 2160, 3840
else:
    r.resolution_x, r.resolution_y = 540, 960
r.resolution_percentage = 100
r.image_settings.file_format = "PNG"
r.image_settings.color_depth = "16"
vs = scene.view_settings
vs.view_transform = "AgX"
for look in ("AgX - Punchy", "Punchy"):
    try:
        vs.look = look
        break
    except Exception:
        pass
vs.exposure = 0.3

# ---------- compositor: bloom + soft vignette ----------
scene.use_nodes = True
ct = scene.node_tree
ct.nodes.clear()
rl_ = ct.nodes.new("CompositorNodeRLayers")
glare = ct.nodes.new("CompositorNodeGlare")
glare.glare_type = "FOG_GLOW"
glare.quality = "HIGH"
glare.threshold = 0.7
glare.size = 9
glare.mix = -0.55
glare2 = ct.nodes.new("CompositorNodeGlare")
glare2.glare_type = "FOG_GLOW"
glare2.quality = "HIGH"
glare2.threshold = 3.0
glare2.size = 7
glare2.mix = -0.7
ell = ct.nodes.new("CompositorNodeEllipseMask")
ell.width, ell.height = 0.95, 0.9
blur = ct.nodes.new("CompositorNodeBlur")
blur.size_x = blur.size_y = 400 if MODE == "final" else 100
vig = ct.nodes.new("CompositorNodeMixRGB")
vig.blend_type = "MULTIPLY"
vigr = ct.nodes.new("CompositorNodeMapRange")
vigr.inputs["To Min"].default_value = 0.55
vigr.inputs["To Max"].default_value = 1.0
comp = ct.nodes.new("CompositorNodeComposite")
ct.links.new(rl_.outputs["Image"], glare.inputs["Image"])
ct.links.new(glare.outputs["Image"], glare2.inputs["Image"])
ct.links.new(ell.outputs["Mask"], blur.inputs["Image"])
ct.links.new(blur.outputs["Image"], vigr.inputs["Value"])
ct.links.new(glare2.outputs["Image"], vig.inputs[1])
ct.links.new(vigr.outputs["Value"], vig.inputs[2])
ct.links.new(vig.outputs["Image"], comp.inputs["Image"])

os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
r.filepath = os.path.join(HERE, "renders", f"moon_bay_{MODE}.png")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "renders", "moon_bay.blend"))
if "--build-only" in argv:
    print("[moon_bay] build ok"); sys.exit(0)
bpy.ops.render.render(write_still=True)
print("[moon_bay] wrote", r.filepath)
