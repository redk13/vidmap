// ============================================================================
// ROME PHOTOREALISTIC AI-DEPTH 3D ENGINE (WebGL 2.0 + Custom GLSL Normal/Depth Shader)
// Converts Photorealistic Renders + Depth-Anything-V2 Maps into True 3D Scenes
// ============================================================================

window.initRomeAI3D = async function() {
  const W = 1920, H = 1080;
  const glCanvas = document.getElementById('glCanvas');
  const hudCanvas = document.getElementById('hudCanvas');
  const outCanvas = document.getElementById('outCanvas');
  const hudCtx = hudCanvas.getContext('2d');
  const outCtx = outCanvas.getContext('2d');

  const renderer = new THREE.WebGLRenderer({
    canvas: glCanvas,
    antialias: true,
    preserveDrawingBuffer: true,
    powerPreference: 'high-performance'
  });
  renderer.setSize(W, H, false);

  const loader = new THREE.TextureLoader();
  function loadTex(url) {
    return new Promise((resolve, reject) => {
      loader.load(url, tex => {
        tex.minFilter = THREE.LinearFilter;
        tex.magFilter = THREE.LinearFilter;
        tex.wrapS = THREE.ClampToEdgeWrapping;
        tex.wrapT = THREE.ClampToEdgeWrapping;
        resolve(tex);
      }, undefined, reject);
    });
  }

  // Load all 5 photorealistic RGB textures + 5 Depth-Anything-V2 3D depth maps
  const rgbTex = [], depthTex = [], depthCpu = [];
  for (let i = 1; i <= 5; i++) {
    const rt = await loadTex(`/ai3d/rgb${i}.jpg`);
    const dt = await loadTex(`/ai3d/depth${i}.png`);
    rgbTex.push(rt);
    depthTex.push(dt);

    const c = document.createElement('canvas');
    c.width = 240; c.height = 135;
    const cx = c.getContext('2d');
    cx.drawImage(dt.image, 0, 0, 240, 135);
    const imgData = cx.getImageData(0, 0, 240, 135).data;
    const fArr = new Float32Array(240 * 135);
    for (let k = 0; k < 240 * 135; k++) {
      fArr[k] = imgData[k * 4] / 255.0;
    }
    depthCpu.push(fArr);
  }

  const PLANE_W = 16.0, PLANE_H = 9.0;
  function sampleDepth(shotIdx, u, v) {
    const arr = depthCpu[shotIdx];
    const ix = Math.max(0, Math.min(239, Math.floor(u * 239)));
    const iy = Math.max(0, Math.min(134, Math.floor((1.0 - v) * 134))); // v in image space (0=top, 1=bottom)
    return arr[iy * 240 + ix];
  }
  // Convert image normalized coordinates (u: 0=left..1=right, v_img: 0=top..1=bottom) to 3D World Space
  function imgUVToWorld3D(shotIdx, u, v_img, depthScale, zOffset = 0.08) {
    const arr = depthCpu[shotIdx];
    const ix = Math.max(0, Math.min(239, Math.floor(u * 239)));
    const iy = Math.max(0, Math.min(134, Math.floor(v_img * 134)));
    const d = arr[iy * 240 + ix];
    const wx = (u - 0.5) * PLANE_W;
    const wy = (0.5 - v_img) * PLANE_H;
    const wz = (d - 0.45) * depthScale + zOffset;
    return new THREE.Vector3(wx, wy, wz);
  }

  const vertexShader = `
    uniform sampler2D uDepthTex;
    uniform float uDepthScale;
    varying vec2 vUv;
    varying vec3 vWorldPos;
    varying float vDepth;

    void main() {
      vUv = uv;
      vec2 texel = vec2(1.0 / 480.0, 1.0 / 270.0);
      float dC = texture2D(uDepthTex, uv).r;
      float dL = texture2D(uDepthTex, uv - vec2(texel.x * 2.0, 0.0)).r;
      float dR = texture2D(uDepthTex, uv + vec2(texel.x * 2.0, 0.0)).r;
      float dU = texture2D(uDepthTex, uv - vec2(0.0, texel.y * 2.0)).r;
      float dD = texture2D(uDepthTex, uv + vec2(0.0, texel.y * 2.0)).r;
      float d = (dC * 4.0 + dL + dR + dU + dD) / 8.0;

      float edgeX = smoothstep(0.0, 0.04, uv.x) * smoothstep(1.0, 0.96, uv.x);
      float edgeY = smoothstep(0.0, 0.04, uv.y) * smoothstep(1.0, 0.96, uv.y);
      float edgeMask = edgeX * edgeY;

      vDepth = d;
      vec3 pos = position;
      pos.z += (d - 0.45) * uDepthScale * edgeMask;
      vWorldPos = pos;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `;

  const fragmentShader = `
    uniform sampler2D uRgbTex;
    uniform sampler2D uDepthTex;
    uniform int uShotIdx;
    uniform float uTime;
    uniform float uProgress;
    uniform vec3 uLightPos;
    uniform vec3 uLightColor;
    uniform float uLightIntensity;

    varying vec2 vUv;
    varying vec3 vWorldPos;
    varying float vDepth;

    void main() {
      vec3 baseCol = texture2D(uRgbTex, vUv).rgb;

      // Compute 3D surface normal from Depth-Anything-V2 map for real 3D relighting!
      vec2 eps = vec2(1.0 / 960.0, 1.0 / 540.0);
      float dzdx = (texture2D(uDepthTex, vUv + vec2(eps.x, 0.0)).r - texture2D(uDepthTex, vUv - vec2(eps.x, 0.0)).r) * 18.0;
      float dzdy = (texture2D(uDepthTex, vUv + vec2(0.0, eps.y)).r - texture2D(uDepthTex, vUv - vec2(0.0, eps.y)).r) * 18.0;
      vec3 normal = normalize(vec3(-dzdx, -dzdy, 1.0));

      vec3 lDir = uLightPos - vWorldPos;
      float dist = length(lDir);
      vec3 L = normalize(lDir);
      float ndotl = max(0.0, dot(normal, L));
      float atten = 1.0 / (1.0 + 0.16 * dist + 0.05 * dist * dist);
      vec3 dynLight = uLightColor * (ndotl * atten * uLightIntensity);

      vec3 finalCol = baseCol + dynLight;

      // Shot 1 Special 3D Effect: Depth-Contoured Cyan Holographic Laser Scan Wave
      if (uShotIdx == 0) {
        float scanU = 0.02 + uProgress * 0.92;
        float aqueductCoord = vUv.x + (vUv.y - 0.5) * 0.28;
        float distScan = abs(aqueductCoord - scanU);
        float structureMask = smoothstep(0.30, 0.45, vDepth);
        if (distScan < 0.09 && structureMask > 0.01) {
          float core = exp(-distScan * distScan / 0.00016);
          float halo = exp(-distScan * distScan / 0.0024);
          float contour = 0.5 + 0.5 * sin(vDepth * 150.0 + vWorldPos.x * 14.0);
          vec3 scanCol = vec3(0.05, 0.92, 1.0) * (core * 1.45 + halo * 0.52 * contour * (0.45 + 0.85 * abs(normal.x)));
          finalCol += scanCol * structureMask;
        }
      }

      gl_FragColor = vec4(finalCol, 1.0);
    }
  `;

  const scenes = [], cameras = [], uniformsList = [];
  for (let i = 0; i < 5; i++) {
    const sc = new THREE.Scene();
    sc.background = new THREE.Color(i === 1 || i === 2 ? 0x0E1014 : 0xD8D5CE);
    const cam = new THREE.PerspectiveCamera(34, W / H, 0.1, 100);

    const uniforms = {
      uRgbTex: { value: rgbTex[i] },
      uDepthTex: { value: depthTex[i] },
      uDepthScale: { value: i === 2 || i === 4 ? 2.25 : 1.85 },
      uShotIdx: { value: i },
      uTime: { value: 0.0 },
      uProgress: { value: 0.0 },
      uLightPos: { value: new THREE.Vector3(0, 0, 2) },
      uLightColor: { value: new THREE.Color(0x00F0FF) },
      uLightIntensity: { value: 0.85 }
    };

    const geo = new THREE.PlaneGeometry(PLANE_W, PLANE_H, 480, 270);
    const mat = new THREE.ShaderMaterial({ vertexShader, fragmentShader, uniforms });
    const mesh = new THREE.Mesh(geo, mat);
    // Scale mesh slightly (1.14x) so 3D camera movement & orbital parallax never expose outer border
    mesh.scale.set(1.14, 1.14, 1.0);
    sc.add(mesh);

    scenes.push(sc);
    cameras.push(cam);
    uniformsList.push(uniforms);
  }

  function mapPt3D(shotIdx, u, v_img, depthScale, zOff = 0.08) {
    const p = imgUVToWorld3D(shotIdx, u, v_img, depthScale, zOff);
    p.x *= 1.14;
    p.y *= 1.14;
    return p;
  }

  function create3DGlowSpline(shotIdx, uvPoints, depthScale, radiusCore, radiusHalo, colorCore, colorHalo) {
    const pts3d = uvPoints.map(([u, v_img]) => mapPt3D(shotIdx, u, v_img, depthScale, 0.08));
    const curve = new THREE.CatmullRomCurve3(pts3d);
    const coreGeo = new THREE.TubeGeometry(curve, 180, radiusCore, 10, false);
    const haloGeo = new THREE.TubeGeometry(curve, 180, radiusHalo, 10, false);

    const coreMesh = new THREE.Mesh(coreGeo, new THREE.MeshBasicMaterial({ color: colorCore }));
    const haloMesh = new THREE.Mesh(haloGeo, new THREE.MeshBasicMaterial({
      color: colorHalo,
      transparent: true,
      opacity: 0.45,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    }));
    scenes[shotIdx].add(coreMesh, haloMesh);
    return { curve, coreGeo, haloGeo, fullPts: curve.getPoints(200) };
  }

  // 1. Shot 1: Shimmering 3D Cyan Water Stream inside the top Aqueduct Channel (Specus)
  const s1Water = create3DGlowSpline(
    0,
    [[0.00, 0.595], [0.18, 0.530], [0.36, 0.468], [0.54, 0.405], [0.72, 0.342], [0.87, 0.285]],
    1.85, 0.024, 0.070, 0x88F8FF, 0x00C8FF
  );

  // 2. Shot 2: Animated 3D Glowing Golden-Amber Spline for AQUA MARCIA (from Rome Colosseum into the Apennines)
  const s2Marcia = create3DGlowSpline(
    1,
    [
      [0.485, 0.482], [0.545, 0.505], [0.615, 0.518], [0.685, 0.492],
      [0.745, 0.435], [0.805, 0.368], [0.865, 0.295], [0.915, 0.235]
    ],
    1.85, 0.040, 0.130, 0xFFE46B, 0xFF8800
  );

  // 3. Shot 3: Animated 3D Glowing Cyan Water Flow (from Right Mountain Lake Basin -> Bridge -> Left Roman Temple)
  const s3Flow = create3DGlowSpline(
    2,
    [
      [0.775, 0.490], [0.715, 0.480], [0.655, 0.465], [0.540, 0.438],
      [0.410, 0.408], [0.280, 0.376], [0.160, 0.346], [0.085, 0.328]
    ],
    2.25, 0.042, 0.135, 0x98FFFF, 0x00D8FF
  );

  // 4. Shot 4: Animated 3D Glowing Golden-Yellow Laser Slope Line along the Studio Aqueduct
  const s4Laser = create3DGlowSpline(
    3,
    [[0.10, 0.432], [0.30, 0.372], [0.52, 0.305], [0.75, 0.235], [0.98, 0.162]],
    1.85, 0.035, 0.120, 0xFFF066, 0xFFB800
  );

  // 5. Shot 5: Animated 3D Glowing Cyan Pressurized U-Shaped Inverted Siphon (from Header Tank down 50m Valley & Uphill!)
  const s5Siphon = create3DGlowSpline(
    4,
    [
      [0.245, 0.408], [0.295, 0.425], [0.335, 0.565], [0.380, 0.725],
      [0.430, 0.835], [0.478, 0.862], [0.528, 0.835], [0.580, 0.725],
      [0.640, 0.575], [0.705, 0.440], [0.785, 0.435]
    ],
    2.25, 0.050, 0.155, 0x90FFFF, 0x00D8FF
  );

  function projectTo2D(vec3, camera) {
    const v = vec3.clone().project(camera);
    return {
      x: (v.x * 0.5 + 0.5) * W,
      y: (-v.y * 0.5 + 0.5) * H
    };
  }

  function drawSubtitle(ctx, beforeText, goldKeyword, afterText) {
    ctx.save();
    const fontBase = "500 32px 'DejaVu Sans', Arial, sans-serif";
    const fontGold = "italic bold 33px 'DejaVu Sans', Arial, sans-serif";
    ctx.font = fontBase;
    const w1 = ctx.measureText(beforeText).width;
    ctx.font = fontGold;
    const w2 = ctx.measureText(goldKeyword).width;
    ctx.font = fontBase;
    const w3 = ctx.measureText(afterText).width;
    const totalW = w1 + w2 + w3;
    let startX = (W - totalW) / 2;
    const baseY = H - 56;

    ctx.fillStyle = 'rgba(10, 12, 16, 0.72)';
    ctx.beginPath();
    ctx.roundRect(startX - 24, baseY - 34, totalW + 48, 48, 10);
    ctx.fill();

    ctx.shadowColor = 'rgba(0,0,0,0.9)';
    ctx.shadowBlur = 6;
    ctx.shadowOffsetY = 2;

    ctx.font = fontBase;
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(beforeText, startX, baseY);
    startX += w1;

    ctx.font = fontGold;
    ctx.fillStyle = '#F6D34E';
    ctx.fillText(goldKeyword, startX, baseY);
    startX += w2;

    ctx.font = fontBase;
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(afterText, startX, baseY);
    ctx.restore();
  }

  window.renderFrameAt = function(t, frameIdx) {
    hudCtx.clearRect(0, 0, W, H);
    const shotIdx = Math.min(4, Math.floor(t / 4.0));
    const u = (t - shotIdx * 4.0) / 4.0;
    const su = u * u * (3.0 - 2.0 * u);

    const sc = scenes[shotIdx];
    const cam = cameras[shotIdx];
    const uni = uniformsList[shotIdx];
    uni.uTime.value = t;
    uni.uProgress.value = u;

    if (shotIdx === 0) {
      cam.position.set(-0.65 + su * 1.30, -0.32 + su * 0.58, 13.8 - su * 1.65);
      cam.lookAt(0.15 * su, 0.08 * su, 0.0);

      const scanIdx = Math.min(199, Math.floor(u * 199));
      const scanPt = s1Water.fullPts[scanIdx];
      uni.uLightPos.value.set(scanPt.x, scanPt.y, scanPt.z + 0.6);
      uni.uLightColor.value.setHex(0x00F0FF);
      uni.uLightIntensity.value = 0.68;

      const totalW1 = s1Water.coreGeo.index ? s1Water.coreGeo.index.count : s1Water.coreGeo.attributes.position.count;
      const cnt1 = Math.floor(totalW1 * Math.min(1.0, u * 1.15));
      s1Water.coreGeo.setDrawRange(0, cnt1);
      s1Water.haloGeo.setDrawRange(0, cnt1);

      renderer.render(sc, cam);

      if (u < 0.5) {
        drawSubtitle(hudCtx, 'From the innovative ', 'aqueducts', ' engineered across Roman valleys');
      } else {
        drawSubtitle(hudCtx, 'that brought fresh water nearly ', '100 km', ' straight into the city');
      }
    } else if (shotIdx === 1) {
      cam.position.set(-0.55 + su * 1.15, -0.45 + su * 0.65, 13.8 - su * 1.55);
      cam.lookAt(0.25 * su, 0.05 * su, 0.0);

      const drawFrac = Math.min(1.0, Math.max(0.10, (u - 0.03) / 0.80));
      const totalM = s2Marcia.coreGeo.index ? s2Marcia.coreGeo.index.count : s2Marcia.coreGeo.attributes.position.count;
      const cnt2 = Math.floor(totalM * drawFrac);
      s2Marcia.coreGeo.setDrawRange(0, cnt2);
      s2Marcia.haloGeo.setDrawRange(0, cnt2);

      const tipIdx = Math.min(199, Math.floor(drawFrac * 199));
      const tipPt = s2Marcia.fullPts[tipIdx];
      uni.uLightPos.value.set(tipPt.x, tipPt.y, tipPt.z + 0.8);
      uni.uLightColor.value.setHex(0xFF9900);
      uni.uLightIntensity.value = 0.78;

      renderer.render(sc, cam);

      const pRome  = projectTo2D(mapPt3D(1, 0.482, 0.482, 1.85, 0.1), cam);
      const pPop   = projectTo2D(mapPt3D(1, 0.240, 0.460, 1.85, 0.1), cam);
      const pTitle = projectTo2D(mapPt3D(1, 0.635, 0.435, 1.85, 0.2), cam);
      const pTip   = projectTo2D(tipPt, cam);

      hudCtx.save();
      hudCtx.fillStyle = 'rgba(255,255,255,0.22)';
      hudCtx.beginPath(); hudCtx.roundRect(42, 28, 360, 12, 6); hudCtx.fill();
      hudCtx.fillStyle = '#FFFFFF';
      hudCtx.beginPath(); hudCtx.roundRect(42, 28, 125 + u * 95, 12, 6); hudCtx.fill();

      const popVal = Math.floor(750000 + Math.min(1.0, u * 1.35) * 250000).toLocaleString('en-US');
      hudCtx.strokeStyle = 'rgba(255,255,255,0.88)';
      hudCtx.lineWidth = 2.4;
      hudCtx.beginPath();
      hudCtx.moveTo(pPop.x + 85, pPop.y + 6);
      hudCtx.lineTo(pRome.x, pRome.y);
      hudCtx.stroke();

      hudCtx.font = "italic bold 38px 'DejaVu Serif', Georgia, serif";
      hudCtx.fillStyle = '#FFFFFF';
      hudCtx.textAlign = 'center';
      hudCtx.shadowColor = 'rgba(0,0,0,0.9)';
      hudCtx.shadowBlur = 12;
      hudCtx.fillText(popVal, pPop.x, pPop.y);

      hudCtx.save();
      hudCtx.translate(pTitle.x, pTitle.y);
      hudCtx.rotate(-0.20);
      hudCtx.font = "italic bold 54px 'DejaVu Serif', Georgia, serif";
      hudCtx.fillStyle = '#FFC425';
      hudCtx.shadowColor = 'rgba(255,140,0,0.95)';
      hudCtx.shadowBlur = 22;
      hudCtx.textAlign = 'center';
      hudCtx.fillText('Aqua Marcia', 0, 0);
      hudCtx.restore();

      const kmVal = Math.max(14, Math.round(drawFrac * 90));
      const miVal = Math.max(9, Math.round(drawFrac * 55));
      hudCtx.save();
      hudCtx.translate(Math.min(W - 210, pTip.x + 55), pTip.y + 42);
      hudCtx.rotate(-0.16);
      hudCtx.strokeStyle = '#FFFFFF';
      hudCtx.lineWidth = 2.2;
      hudCtx.beginPath();
      hudCtx.moveTo(-55, -42);
      hudCtx.lineTo(-10, -18);
      hudCtx.stroke();

      hudCtx.font = "italic bold 50px 'DejaVu Serif', Georgia, serif";
      hudCtx.fillStyle = '#FFFFFF';
      hudCtx.shadowColor = 'rgba(0,0,0,0.9)';
      hudCtx.shadowBlur = 16;
      hudCtx.fillText(`${kmVal} km`, 0, 0);
      hudCtx.font = "italic bold 28px 'DejaVu Serif', Georgia, serif";
      hudCtx.fillStyle = '#E2E8F0';
      hudCtx.fillText(`${miVal} miles`, 10, 32);
      hudCtx.restore();
      hudCtx.restore();

      drawSubtitle(hudCtx, 'The ', 'Aqua Marcia', ' carried pure mountain spring water over 90 kilometers');
    } else if (shotIdx === 2) {
      cam.position.set(0.65 - su * 1.30, -0.35 + su * 0.55, 13.7 - su * 1.45);
      cam.lookAt(0.20 - su * 0.40, 0.0, 0.0);

      const flowFrac = Math.min(1.0, Math.max(0.06, (u - 0.03) / 0.80));
      const totalF3 = s3Flow.coreGeo.index ? s3Flow.coreGeo.index.count : s3Flow.coreGeo.attributes.position.count;
      const cnt3 = Math.floor(totalF3 * flowFrac);
      s3Flow.coreGeo.setDrawRange(0, cnt3);
      s3Flow.haloGeo.setDrawRange(0, cnt3);

      const fIdx = Math.min(199, Math.floor(flowFrac * 199));
      const fPt = s3Flow.fullPts[fIdx];
      uni.uLightPos.value.set(fPt.x, fPt.y, fPt.z + 0.9);
      uni.uLightColor.value.setHex(0x00F0FF);
      uni.uLightIntensity.value = 0.72;

      renderer.render(sc, cam);

      const pSource = projectTo2D(mapPt3D(2, 0.785, 0.315, 2.25, 0.15), cam);
      const pRome3  = projectTo2D(mapPt3D(2, 0.175, 0.115, 2.25, 0.15), cam);

      hudCtx.save();
      hudCtx.font = "italic bold 42px 'DejaVu Serif', Georgia, serif";
      hudCtx.fillStyle = '#FFFFFF';
      hudCtx.textAlign = 'center';
      hudCtx.shadowColor = 'rgba(0,0,0,0.9)';
      hudCtx.shadowBlur = 14;
      hudCtx.fillText('Water', pSource.x, pSource.y - 22);
      hudCtx.fillText('source', pSource.x, pSource.y + 22);

      if (u > 0.15) {
        hudCtx.globalAlpha = Math.min(1.0, (u - 0.15) / 0.25);
        hudCtx.fillText('Rome', pRome3.x, Math.max(85, pRome3.y));
      }
      hudCtx.restore();

      drawSubtitle(hudCtx, 'Tapping high ', 'mountain springs', ', tunnels and bridges guided water by gravity alone');
    } else if (shotIdx === 3) {
      cam.position.set(-0.75 + su * 1.50, -0.18 + su * 0.36, 13.8 - su * 1.45);
      cam.lookAt(-0.15 + su * 0.30, 0.0, 0.0);

      const lFrac = Math.min(1.0, Math.max(0.15, (u + 0.1) / 0.85));
      const totalL4 = s4Laser.coreGeo.index ? s4Laser.coreGeo.index.count : s4Laser.coreGeo.attributes.position.count;
      const cnt4 = Math.floor(totalL4 * lFrac);
      s4Laser.coreGeo.setDrawRange(0, cnt4);
      s4Laser.haloGeo.setDrawRange(0, cnt4);

      const lIdx = Math.min(199, Math.floor(u * 199));
      const lPt = s4Laser.fullPts[lIdx];
      uni.uLightPos.value.set(lPt.x, lPt.y, lPt.z + 0.8);
      uni.uLightColor.value.setHex(0xFFD000);
      uni.uLightIntensity.value = 0.65;

      renderer.render(sc, cam);

      const pLaserText = projectTo2D(mapPt3D(3, 0.44, 0.24, 1.85, 0.1), cam);
      const pLaserLine = projectTo2D(mapPt3D(3, 0.52, 0.305, 1.85, 0.1), cam);

      hudCtx.save();
      hudCtx.textAlign = 'center';
      if (u < 0.52) {
        hudCtx.strokeStyle = '#FFFFFF';
        hudCtx.lineWidth = 2.8;
        hudCtx.beginPath();
        hudCtx.moveTo(pLaserText.x + 85, pLaserText.y + 22);
        hudCtx.lineTo(pLaserLine.x, pLaserLine.y);
        hudCtx.stroke();

        hudCtx.font = "italic bold 46px 'DejaVu Serif', Georgia, serif";
        hudCtx.fillStyle = '#3E3B36';
        hudCtx.fillText('1.5–3 meters per km', pLaserText.x, pLaserText.y - 12);
        hudCtx.font = "500 28px 'DejaVu Sans', Arial, sans-serif";
        hudCtx.fillStyle = '#5E5A52';
        hudCtx.fillText('(8–16 feet per mile)', pLaserText.x, pLaserText.y + 26);
      } else {
        hudCtx.globalAlpha = Math.min(1.0, (u - 0.52) / 0.25);
        hudCtx.font = "italic bold 66px 'DejaVu Serif', Georgia, serif";
        hudCtx.fillStyle = '#4A4640';
        hudCtx.fillText('0.09 – 0.17°', pLaserText.x, pLaserText.y + 10);
      }
      hudCtx.restore();

      drawSubtitle(hudCtx, 'Dropping just ', '1.5 to 3 meters', ' per kilometer — a razor-thin 0.15° gradient');
    } else {
      cam.position.set(-0.45 + su * 0.90, 0.35 - su * 0.65, 13.8 - su * 1.65);
      cam.lookAt(0.0, -0.10 * su, 0.0);

      const sFrac = Math.min(1.0, Math.max(0.08, (u - 0.03) / 0.78));
      const totalS5 = s5Siphon.coreGeo.index ? s5Siphon.coreGeo.index.count : s5Siphon.coreGeo.attributes.position.count;
      const cnt5 = Math.floor(totalS5 * sFrac);
      s5Siphon.coreGeo.setDrawRange(0, cnt5);
      s5Siphon.haloGeo.setDrawRange(0, cnt5);

      const sIdx = Math.min(199, Math.floor(sFrac * 199));
      const sPt = s5Siphon.fullPts[sIdx];
      uni.uLightPos.value.set(sPt.x, sPt.y, sPt.z + 0.9);
      uni.uLightColor.value.setHex(0x00F0FF);
      uni.uLightIntensity.value = 0.72;

      renderer.render(sc, cam);

      const pTop5 = projectTo2D(mapPt3D(4, 0.475, 0.415, 2.25, 0.15), cam);
      const pBot5 = projectTo2D(mapPt3D(4, 0.475, 0.855, 2.25, 0.15), cam);
      const pTank5 = projectTo2D(mapPt3D(4, 0.245, 0.335, 2.25, 0.15), cam);

      hudCtx.save();
      hudCtx.strokeStyle = '#FFD600';
      hudCtx.lineWidth = 3.2;
      hudCtx.setLineDash([8, 6]);
      hudCtx.beginPath();
      hudCtx.moveTo(pTop5.x, pTop5.y);
      hudCtx.lineTo(pBot5.x, pBot5.y);
      hudCtx.stroke();
      hudCtx.setLineDash([]);

      hudCtx.textAlign = 'center';
      hudCtx.font = "italic bold 42px 'DejaVu Serif', Georgia, serif";
      hudCtx.fillStyle = '#FFFFFF';
      hudCtx.shadowColor = 'rgba(0,0,0,0.92)';
      hudCtx.shadowBlur = 12;
      hudCtx.fillText('50 m', pTop5.x, pTop5.y - 26);
      hudCtx.font = "500 26px 'DejaVu Sans', Arial, sans-serif";
      hudCtx.fillText('(164 ft)', pTop5.x, pTop5.y + 4);

      hudCtx.font = "italic bold 36px 'DejaVu Serif', Georgia, serif";
      hudCtx.fillStyle = '#FFFFFF';
      hudCtx.fillText('Header tank', pTank5.x, pTank5.y);
      hudCtx.restore();

      drawSubtitle(hudCtx, 'Across valleys deeper than ', '50 meters', ', pressurized inverted siphons forced water uphill');
    }

    outCtx.clearRect(0, 0, W, H);
    outCtx.drawImage(glCanvas, 0, 0);
    outCtx.drawImage(hudCanvas, 0, 0);
    return outCanvas.toDataURL('image/jpeg', 0.94);
  };
};
