# Environment frame: Moon Bay

New format test: pure environment, no story. One path-traced still (original art).
Electric-blue night sea with glowing bioluminescent surf, basalt sea stacks, low mist, huge blue moon.

Rendered on the home PC only (Blender 4.2 LTS portable, Cycles on the GTX 1660 Ti).

    blender.exe -b -P moon_bay.py -- --preview    # 540x960, 64 samples
    blender.exe -b -P moon_bay.py -- --final      # 2160x3840, 4096 samples adaptive

Output lands in renders/ next to the script.
