  const day = (t >= 15 && t < 19) ? 1 : 0;   // key cinema shot: bright summer day, like Jack's photo
  U.uDay.value = day;
  U.uBreathe.value = 0.3*smooth(17, 18, t)*(1 - smooth(18.8, 19, t)) + 0.3*smooth(23.5, 25, t) + 0.1*smooth(27, 29, t);
  U.uDrip.value = 0.75*smooth(16.8, 18.3, t)*(1 - smooth(18.9, 19, t));
  U.uKal.value = 0.6*smooth(28.6, 31, t) - 0.15*smooth(31.5, 33, t) + 0.15*smooth(36, 39, t);
  U.uTrip.value = 0.08*smooth(10, 12, t) + 0.16*smooth(16.8, 18, t)*(1 - smooth(18.9, 19, t)) + 0.08*smooth(19.5, 21, t) + 0.1*smooth(27, 30, t) + 0.08*smooth(36, 39, t);
  // key shot: letters glow and drip, facade breathes
  const cg = smooth(16.6, 17.6, t)*(1 - smooth(18.9, 19, t));
  marquee.glowM.opacity = cg*(0.55 + 0.25*Math.sin(t*9));
  marquee.grp.scale.set(1 + 0.03*cg*Math.sin(t*4), 1 + 0.06*cg*Math.sin(t*4 + 0.5), 1);
  // light: golden hour everywhere except the daylight key shot
  sun.color.set(day ? '#fff4e2' : '#ffbf73'); sun.intensity = day ? 2.4 : 2.6;
  hemi.intensity = day ? 1.9 : 1.6; scene.fog.color.set(day ? '#dfe8f0' : '#f3c38f');
  // Wharf Shop breathes and glows
  const wg = smooth(20.0, 21.0, t) * (1 - smooth(22.6, 23, t));
  wsGlow.material.uniforms.uGlow.value = wg*0.9;
  WSHOP.g.scale.set(1 + 0.05*wg*Math.sin(t*4.2), 1 + 0.09*wg*Math.sin(t*4.2 + 0.6), 1 + 0.4*wg*(0.5 + 0.5*Math.sin(t*4.2)));
