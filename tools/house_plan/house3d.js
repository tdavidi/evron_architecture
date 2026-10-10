/* The 3D model of the house (stage 3). house3d.py builds HOUSE from the same plan as the drawings (house.py): the
   walls as boxes with the doors and windows already cut out, the openings, the rooms, the furniture (with the side of
   each piece that stands against a wall), the garden and the roof. Plan coordinates: x along the street from the
   shared wall, y from the street to the back, z up, in meters; three.js gets (x, z, y), so the plan reads the same
   from above. three.js r128 loads from a CDN, like view3d.js of the ranking pages. The sun follows the season and
   the hour at the neighborhood (suncalc's formulas). The furniture, colors and materials are samples. */
(() => {
  const LIBS = ['https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
                'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'];
  let libs = null;   // three.js loads once, for every model on the page
  const loadLibs = () => libs || (libs = LIBS.reduce((p, src) => p.then(() => new Promise((ok, fail) => {
    const s = document.createElement('script');
    s.src = src; s.onload = ok; s.onerror = () => fail(new Error(src));
    document.head.appendChild(s);
  })), Promise.resolve()));

  // One model in an element of the page (root): its bar of buttons, and a .stage with a canvas and a .msg.
  // D: the data from house3d.py. opts.hash: the view from the address (the page of one model). opts.ctrlWheel: the
  // wheel zooms only with Ctrl, so that the page still scrolls over the model (a page with several models).
  function mount(root, D, opts = {}) {
    const LAT = 32.99, LNG = 35.1;          // the neighborhood, to about a kilometer (enough for the sun)
    const UP_AZ = 17;                       // the azimuth of "up" in the plans (toward the street)
    const SEASON = {winter: {m: 11, d: 21, tz: 2, name: '21 בדצמבר'}, summer: {m: 5, d: 21, tz: 3, name: '21 ביוני'}};
    const DIRS = ['צפון', 'צפון-מזרח', 'מזרח', 'דרום-מזרח', 'דרום', 'דרום-מערב', 'מערב', 'צפון-מערב'];
    const FONT = '"Segoe UI", Arial, sans-serif';
    const OPP = {x0: 'x1', x1: 'x0', y0: 'y1', y1: 'y0'};
    const [BX0, BY0, BX1, BY1] = D.bbox, CEIL = D.ceil, TOP = CEIL + 0.25;   // TOP: the roof slab's top
    const SUNK = -0.7, GARDEN = -0.1, STREET = -0.95;                     // ground levels against the floor (±0.00)
    // the parking and the path along it, 4 steps below the house (the steps zone included, they climb out of it)
    const SUNKEN = [[0, 8.1, 0, 3.6], [0, 6.85, 3.6, 5.0]];
    // fit: the narrowest screen (width / height) the view is framed for; a narrower one sees more (setView)
    const VIEWS = {
      top: {pos: [15.1, 17.9, 22.5], tgt: [7.0, 0, 11.0], fov: 45, roof: 'off', fit: 1.25},
      plan: {pos: [7.2, 64, 11.01], tgt: [7.2, 0, 11], fov: 22, roof: 'off', fit: 0.85},
      garden: {pos: [14.2, 1.65, 21.7], tgt: [7.4, 1.6, 12.6], fov: 55, roof: 'on', fit: 1.35},
      street: {pos: [16.5, 0.7, -8.5], tgt: [6.4, 1.1, 8], fov: 50, roof: 'on', fit: 1.4},
      living: {pos: [11.9, 1.6, 14.45], dir: [-3.2, -0.35, -6.4], fov: 64, roof: 'on', fit: 1.5},
      kitchen: {pos: [11.0, 1.62, 8.15], dir: [-0.1, -0.32, 6.4], fov: 64, roof: 'on', fit: 1.5},
    };
    Object.assign(VIEWS, D.views || {});   // a model's own places to stand in (the forms page)
    const PAL = {
      kid: {duvet: '#3f8f8b', head: '#e1cfaa', chair: '#e2b33c', desk: '#f5f3ef'},
      mamad: {duvet: '#e07a5f', head: '#efe3cf', chair: '#79aa6b', desk: '#f5f3ef'},
      parents: {duvet: '#cdbb9f', head: '#5c6f83'},
      den: {sofa: '#cf9f45', cushion: '#f1e6cf', chair: '#2f2f2f', desk: '#f5f3ef'},
      public: {sofa: '#4e6577', cushion: '#d8a441', arm: '#c26a45', rug: '#d9c9ad'},
    };
    const FOOD = ['#d9a441', '#c0573e', '#e8dcc4', '#7d9a5a', '#f2efe6', '#b5835a', '#e3c16f', '#9c3f2f', '#5f7f9a'];
    const BOOKS = ['#2f5b7d', '#c0573e', '#e3b33c', '#3f7f6b', '#efe9dc', '#7a4b8c', '#2b2b2b', '#d77f5e', '#8aa6b8'];
    const CLOTHES = ['#3f6e9e', '#e9e4da', '#d6704f', '#6c9a5f', '#f0c75e', '#b9b4c9'];

    const main = root, stage = root.querySelector('.stage') || root.querySelector('#stage');
    const canvas = stage.querySelector('canvas'), msg = stage.querySelector('.msg');
    const state = {view: 'top', roof: 'off', season: 'winter', hour: 12, labels: true, neighbors: true};
    let T, renderer, scene, camera, controls, sunLight, fill, bounce, M;
    const G = {};
    const LABELS = [];   // the sprites keep the same size on the screen (fitLabels)
    const RULE = [];   // rects that block a shower's entry: walls and furniture

    // ---------- small helpers ----------
    function rng(seed) {
      return () => {
        seed = seed + 0x6D2B79F5 | 0;
        let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
      };
    }
    const pick = (r, list) => list[Math.floor(r() * list.length) % list.length];
    function shade(hex, f) {   // f > 0: lighter, f < 0: darker
      const n = parseInt(hex.slice(1), 16), rgb = [n >> 16, n >> 8 & 255, n & 255], t = f < 0 ? 0 : 255, p = Math.abs(f);
      return '#' + rgb.map(v => Math.round((t - v) * p + v).toString(16).padStart(2, '0')).join('');
    }

    // ---------- textures (drawn on a canvas; one texture tile covers .meters) ----------
    function canvasTex(px, meters, draw) {
      const c = document.createElement('canvas');
      c.width = c.height = px;
      draw(c.getContext('2d'), px);
      const t = new T.CanvasTexture(c);
      t.wrapS = t.wrapT = T.RepeatWrapping;
      t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
      t.encoding = T.sRGBEncoding;
      t.meters = meters;   // (r128 textures have no userData)
      return t;
    }
    const planks = () => canvasTex(512, 2.0, (ctx, n) => {    // oak planks 20 cm wide
      const r = rng(7), rows = 10, h = n / rows;
      for (let i = 0; i < rows; i++) {
        let x = -r() * n * 0.6;
        while (x < n) {
          const len = n * (0.3 + r() * 0.45);
          ctx.fillStyle = `hsl(${30 + r() * 6}, ${36 + r() * 12}%, ${60 + r() * 9}%)`;
          ctx.fillRect(x, i * h, len, h);
          ctx.strokeStyle = 'rgba(95,62,30,.12)';
          for (let g = 0; g < 5; g++) {
            const yy = i * h + r() * h;
            ctx.beginPath(); ctx.moveTo(x, yy); ctx.bezierCurveTo(x + len / 3, yy + (r() - .5) * 5, x + len * .66, yy + (r() - .5) * 5, x + len, yy); ctx.stroke();
          }
          ctx.fillStyle = 'rgba(70,45,22,.35)'; ctx.fillRect(x, i * h, 1.5, h);
          x += len;
        }
        ctx.fillStyle = 'rgba(70,45,22,.32)'; ctx.fillRect(0, i * h, n, 1.5);
      }
    });
    const tiles = (base, grout, size, vary) => canvasTex(256, size * 2, (ctx, n) => {   // 2 x 2 floor tiles
      const r = rng(Math.round(size * 100)), s = n / 2;
      for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) {
        ctx.fillStyle = shade(base, (r() - .5) * vary); ctx.fillRect(i * s, j * s, s, s);
        for (let k = 0; k < 140; k++) {
          ctx.fillStyle = `rgba(${r() < .5 ? '255,255,255' : '90,80,70'},${r() * .05})`;
          ctx.fillRect(i * s + r() * s, j * s + r() * s, 3 + r() * 8, 3 + r() * 8);
        }
      }
      ctx.strokeStyle = grout; ctx.lineWidth = 2;
      for (let i = 0; i <= 2; i++) {
        ctx.beginPath(); ctx.moveTo(i * s, 0); ctx.lineTo(i * s, n); ctx.moveTo(0, i * s); ctx.lineTo(n, i * s); ctx.stroke();
      }
    });
    const grass = (muted) => canvasTex(512, 3, (ctx, n) => {
      const r = rng(muted ? 12 : 11);
      ctx.fillStyle = muted ? '#8fa070' : '#6f9b48'; ctx.fillRect(0, 0, n, n);
      for (let i = 0; i < 11000; i++) {
        ctx.fillStyle = muted ? `hsl(${78 + r() * 20}, ${16 + r() * 16}%, ${42 + r() * 16}%)`
                              : `hsl(${82 + r() * 26}, ${38 + r() * 24}%, ${28 + r() * 22}%)`;
        ctx.fillRect(r() * n, r() * n, 1.5 + r(), 3 + r() * 5);
      }
    });
    const cover = () => canvasTex(512, 3, (ctx, n) => {     // low planting in the front garden
      const r = rng(19);
      ctx.fillStyle = '#7d8a5a'; ctx.fillRect(0, 0, n, n);
      for (let i = 0; i < 1600; i++) {
        ctx.fillStyle = `hsl(${70 + r() * 40}, ${20 + r() * 25}%, ${26 + r() * 22}%)`;
        ctx.beginPath(); ctx.arc(r() * n, r() * n, 3 + r() * 9, 0, 6.3); ctx.fill();
      }
    });
    const deck = () => canvasTex(512, 1.8, (ctx, n) => {    // boards along x, 15 cm
      const r = rng(5), rows = 12, h = n / rows;
      ctx.fillStyle = '#4b3a2b'; ctx.fillRect(0, 0, n, n);
      for (let i = 0; i < rows; i++) {
        let x = -r() * n;
        while (x < n) {
          const len = n * (0.45 + r() * 0.6);
          ctx.fillStyle = `hsl(${26 + r() * 5}, ${30 + r() * 10}%, ${45 + r() * 9}%)`;
          ctx.fillRect(x, i * h + 1.5, len - 2, h - 3);
          x += len;
        }
      }
    });
    const pavers = (c1, c2) => canvasTex(256, 1.2, (ctx, n) => {   // 20 x 40 cm, running bond
      const r = rng(c1.length * 31), s = n / 6;
      ctx.fillStyle = '#8f8b83'; ctx.fillRect(0, 0, n, n);
      for (let j = 0; j < 6; j++) for (let i = -1; i < 4; i++) {
        ctx.fillStyle = shade(r() < .5 ? c1 : c2, (r() - .5) * .06);
        ctx.fillRect(i * 2 * s + (j % 2) * s + 1, j * s + 1, 2 * s - 2, s - 2);
      }
    });
    const gravel = () => canvasTex(256, 1, (ctx, n) => {
      const r = rng(13);
      ctx.fillStyle = '#c8c1b2'; ctx.fillRect(0, 0, n, n);
      for (let i = 0; i < 5000; i++) {
        const g = 145 + r() * 90 | 0;
        ctx.fillStyle = `rgb(${g},${g - 6},${g - 18})`; ctx.fillRect(r() * n, r() * n, 2 + r() * 2.5, 2 + r() * 2.5);
      }
    });
    const leaves = () => canvasTex(256, 1, (ctx, n) => {
      const r = rng(17);
      ctx.fillStyle = '#3f6230'; ctx.fillRect(0, 0, n, n);
      for (let i = 0; i < 2600; i++) {
        ctx.fillStyle = `hsl(${88 + r() * 32}, ${30 + r() * 30}%, ${18 + r() * 26}%)`;
        ctx.beginPath(); ctx.arc(r() * n, r() * n, 2 + r() * 4.5, 0, 6.3); ctx.fill();
      }
    });
    const roofTiles = () => canvasTex(256, 1.0, (ctx, n) => {   // courses along the ridge, 33 cm
      const r = rng(23), rows = 3, h = n / rows, cols = 4, w = n / cols;
      for (let i = 0; i < rows; i++) for (let j = 0; j < cols + 1; j++) {
        const y = j * w - (i % 2) * w / 2;
        const g = ctx.createLinearGradient(i * h, 0, (i + 1) * h, 0);
        const base = shade('#b4573a', (r() - .5) * .14);
        g.addColorStop(0, shade(base, -.25)); g.addColorStop(.25, base); g.addColorStop(1, shade(base, .08));
        ctx.fillStyle = g; ctx.fillRect(i * h, y + 1, h, w - 2);
      }
    });
    const soil = () => canvasTex(256, 1, (ctx, n) => {
      const r = rng(29);
      ctx.fillStyle = '#6b5440'; ctx.fillRect(0, 0, n, n);
      for (let i = 0; i < 3000; i++) {
        ctx.fillStyle = `hsl(${22 + r() * 14}, ${25 + r() * 20}%, ${18 + r() * 22}%)`; ctx.fillRect(r() * n, r() * n, 2, 2);
      }
    });
    const stone = () => canvasTex(256, 1.6, (ctx, n) => {      // a stone retaining wall
      const r = rng(31);
      ctx.fillStyle = '#9b9283'; ctx.fillRect(0, 0, n, n);
      const rows = 5, h = n / rows;
      for (let i = 0; i < rows; i++) {
        let x = -r() * 60;
        while (x < n) {
          const w = 40 + r() * 50;
          ctx.fillStyle = `hsl(${36 + r() * 10}, ${14 + r() * 10}%, ${66 + r() * 12}%)`;
          ctx.fillRect(x + 2, i * h + 2, w - 4, h - 4);
          x += w;
        }
      }
    });
    function sky() {
      const c = document.createElement('canvas');
      c.width = 4; c.height = 256;
      const ctx = c.getContext('2d'), g = ctx.createLinearGradient(0, 0, 0, 256);
      g.addColorStop(0, '#8fb6dd'); g.addColorStop(.55, '#cfe0ee'); g.addColorStop(1, '#eef1ef');
      ctx.fillStyle = g; ctx.fillRect(0, 0, 4, 256);
      const t = new T.CanvasTexture(c); t.encoding = T.sRGBEncoding;
      return t;
    }

    function materials() {
      const S = o => new T.MeshStandardMaterial(Object.assign({roughness: 0.85, metalness: 0}, o));
      const glass = (color, opacity) => new T.MeshStandardMaterial({color, transparent: true, opacity, roughness: 0.05,
                                                                    metalness: 0.1, depthWrite: false});
      return {
        plaster: S({color: '#f3f0e9'}), cut: S({color: '#56524c'}), mamadCut: S({color: '#7a766e'}),
        sill: S({color: '#e4ddd0', roughness: 0.5}), plinth0: S({color: '#bdb7ac'}), threshold: S({color: '#d8d1c3', roughness: 0.5}),
        ceiling: S({color: '#fbfaf7', emissive: '#77746d'}), membrane: S({color: '#cfccc5'}), coping: S({color: '#bfbab0'}),
        wood: S({map: planks(), roughness: 0.62}),
        porcelain: S({map: tiles('#e8e2d8', '#d2cbbf', 0.6, 0.05), roughness: 0.35}),
        wet: S({map: tiles('#d3d7d8', '#b5babc', 0.3, 0.06), roughness: 0.4}),
        service: S({map: tiles('#ddd6ca', '#c2baad', 0.45, 0.05), roughness: 0.45}),
        grass: S({map: grass(false)}), grassMuted: S({map: grass(true)}), cover: S({map: cover()}),
        deck: S({map: deck(), roughness: 0.7}), paverGrey: S({map: pavers('#bbb8b0', '#aeaaa2')}),
        paverWarm: S({map: pavers('#d9cfb9', '#cdbfa2')}), gravel: S({map: gravel()}), leaf: S({map: leaves()}),
        tiles: S({map: roofTiles(), roughness: 0.7}), soil: S({map: soil()}), earth: S({color: '#8d7b63'}),
        stone: S({map: stone()}), concrete: S({color: '#c9c5bc'}),
        glass: glass('#cfe4ee', 0.2), showerGlass: glass('#e2eef2', 0.16),
        frame: S({color: '#4b4e52', roughness: 0.45, metalness: 0.3}),
        door: S({color: '#f6f4ef', roughness: 0.5}), frontDoor: S({color: '#8a5a37', roughness: 0.55}),
        extDoor: S({color: '#6f7377', roughness: 0.5, metalness: 0.2}), steelDoor: S({color: '#8f9396', roughness: 0.4, metalness: 0.5}),
        oak: S({color: '#c49b6c', roughness: 0.6}), oakTop: S({color: '#b98b5b', roughness: 0.45}),
        oakLight: S({color: '#d9c09b', roughness: 0.6}), walnut: S({color: '#77523a', roughness: 0.55}),
        white: S({color: '#f5f3ef', roughness: 0.5}), black: S({color: '#2c2b29', roughness: 0.6}),
        chair: S({color: '#2f2e2c', roughness: 0.6}), sheet: S({color: '#f6f4ef'}), pillow: S({color: '#fbfaf6'}),
        steel: S({color: '#b9bcbf', roughness: 0.3, metalness: 0.7}), chrome: S({color: '#dde0e2', roughness: 0.15, metalness: 0.9}),
        fridge: S({color: '#c8cbcd', roughness: 0.3, metalness: 0.55}), gap: S({color: '#55524d'}),
        cabinet: S({color: '#f1efea', roughness: 0.45}), island: S({color: '#8ea494', roughness: 0.55}),
        quartz: S({color: '#efece6', roughness: 0.25}), plinthK: S({color: '#3a3936'}),
        hob: S({color: '#151618', roughness: 0.1, metalness: 0.2}), ring: S({color: '#3b3d40', roughness: 0.3}),
        ovenGlass: S({color: '#1d1f22', roughness: 0.08, metalness: 0.3}), sinkSteel: S({color: '#8d9093', roughness: 0.3, metalness: 0.7}),
        ceramic: S({color: '#fbfbf9', roughness: 0.25}), basinIn: S({color: '#e3e6e7', roughness: 0.2}),
        vanity: S({color: '#a77b52', roughness: 0.55}), mirror: S({color: '#cfdce4', roughness: 0.08, emissive: '#2e3438'}),
        tray: S({color: '#e4e4e1', roughness: 0.4}), appliance: S({color: '#f7f7f5', roughness: 0.35}),
        panel: S({color: '#c9ccce', roughness: 0.4}), screen: S({color: '#111214', roughness: 0.15, metalness: 0.2}),
        bark: S({color: '#6e5843'}), terracotta: S({color: '#b5653f'}), pergola: S({color: '#7a5a3c', roughness: 0.7}),
        paint: S({color: '#5a6f86', roughness: 0.35, metalness: 0.45}), carGlass: S({color: '#2a3138', roughness: 0.1, metalness: 0.3}),
        tyre: S({color: '#222222', roughness: 0.9}), line: S({color: '#f1efe8'}), gas: S({color: '#9aa3a6', roughness: 0.4, metalness: 0.4}),
        neighbor: new T.MeshStandardMaterial({color: '#eceae3', transparent: true, opacity: 0.2, depthWrite: false}),
        ghost: new T.MeshBasicMaterial({colorWrite: false, depthWrite: false}),
        trim: S({color: '#e9e7e2', roughness: 0.4}), spot: new T.MeshBasicMaterial({color: '#fff4dc'}),
      };
    }
    const MATS = new Map();
    function mat(color, o = {}) {
      const key = color + JSON.stringify(o);
      if (!MATS.has(key)) MATS.set(key, new T.MeshStandardMaterial(Object.assign({color, roughness: 0.8, metalness: 0}, o)));
      return MATS.get(key);
    }

    // ---------- geometry helpers: plan coordinates (x, y) and height z ----------
    function worldUV(geo, cx, cy, cz, m) {   // UVs in meters / m, from the box's coordinates (local + center)
      const p = geo.attributes.position, nrm = geo.attributes.normal, uv = geo.attributes.uv;
      for (let i = 0; i < p.count; i++) {
        const X = p.getX(i) + cx, Y = p.getY(i) + cy, Z = p.getZ(i) + cz;
        if (Math.abs(nrm.getX(i)) > .5) uv.setXY(i, Z / m, Y / m);
        else if (Math.abs(nrm.getY(i)) > .5) uv.setXY(i, X / m, Z / m);
        else uv.setXY(i, X / m, Y / m);
      }
      uv.needsUpdate = true;
    }
    function box(x0, x1, y0, y1, z0, z1, m, parent = G.house, o = {}) {
      const w = Math.max(x1 - x0, 1e-3), h = Math.max(z1 - z0, 1e-3), d = Math.max(y1 - y0, 1e-3);
      const cx = (x0 + x1) / 2, cy = (z0 + z1) / 2, cz = (y0 + y1) / 2;
      const geo = new T.BoxGeometry(w, h, d);
      const tm = (Array.isArray(m) ? m : [m]).find(q => q.map && q.map.meters);
      if (tm) worldUV(geo, cx, cy, cz, tm.map.meters);
      const mesh = new T.Mesh(geo, m);
      mesh.position.set(cx, cy, cz);
      mesh.castShadow = o.cast !== false; mesh.receiveShadow = o.receive !== false;
      parent.add(mesh);
      return mesh;
    }
    function cyl(x, y, z0, z1, r, m, parent = G.house, o = {}) {
      const geo = new T.CylinderGeometry(o.rTop !== undefined ? o.rTop : r, r, Math.max(z1 - z0, 1e-3), o.seg || 20, 1, !!o.open);
      const mesh = new T.Mesh(geo, m);
      mesh.position.set(x, (z0 + z1) / 2, y);
      if (o.sx || o.sy) mesh.scale.set(o.sx || 1, 1, o.sy || 1);
      mesh.castShadow = o.cast !== false; mesh.receiveShadow = true;
      parent.add(mesh);
      return mesh;
    }
    function ball(x, y, z, r, m, parent = G.house, o = {}) {
      const geo = o.ico ? new T.IcosahedronGeometry(r, o.detail !== undefined ? o.detail : 1)
                        : new T.SphereGeometry(r, 20, 14, 0, Math.PI * 2, 0, o.half ? Math.PI / 2 : Math.PI);
      const mesh = new T.Mesh(geo, m);
      mesh.position.set(x, z, y);
      if (o.sz) mesh.scale.set(1, o.sz, 1);
      mesh.castShadow = o.cast !== false; mesh.receiveShadow = true;
      parent.add(mesh);
      return mesh;
    }
    function rod(a, b, r, m, parent = G.house, o = {}) {   // a thin cylinder between two points [x, y, z]
      const A = new T.Vector3(a[0], a[2], a[1]), B = new T.Vector3(b[0], b[2], b[1]);
      const mesh = new T.Mesh(new T.CylinderGeometry(r, r, A.distanceTo(B), o.seg || 10), m);
      mesh.position.copy(A).add(B).multiplyScalar(0.5);
      mesh.quaternion.setFromUnitVectors(new T.Vector3(0, 1, 0), B.clone().sub(A).normalize());
      mesh.castShadow = o.cast !== false; mesh.receiveShadow = true;
      parent.add(mesh);
      return mesh;
    }
    function disc(x, y, z, r, axis, m, parent = G.house) {   // a flat cylinder facing along x or y
      const mesh = cyl(0, 0, -0.012, 0.012, r, m, parent, {seg: 28, cast: false});
      if (axis === 'x') mesh.rotation.z = Math.PI / 2; else mesh.rotation.x = Math.PI / 2;
      mesh.position.set(x, z, y);
      return mesh;
    }
    // A local frame for a piece of furniture: u along its back, v from the back toward the front.
    function F(r, back) {
      const [x0, y0, x1, y1] = r, alongY = back === 'y0' || back === 'y1';
      const W = alongY ? x1 - x0 : y1 - y0, L = alongY ? y1 - y0 : x1 - x0;
      const rect = (u0, u1, v0, v1) => ({
        y0: [x0 + u0, x0 + u1, y0 + v0, y0 + v1], y1: [x0 + u0, x0 + u1, y1 - v1, y1 - v0],
        x0: [x0 + v0, x0 + v1, y0 + u0, y0 + u1], x1: [x1 - v1, x1 - v0, y0 + u0, y0 + u1]}[back]);
      const pt = (u, v) => { const q = rect(u, u, v, v); return [q[0], q[2]]; };
      const inv = (x, y) => ({y0: [x - x0, y - y0], y1: [x - x0, y1 - y], x0: [y - y0, x - x0], x1: [y - y0, x1 - x]}[back]);
      const b = (u0, u1, v0, v1, z0, z1, m, parent, o) => { const q = rect(u0, u1, v0, v1); return box(q[0], q[1], q[2], q[3], z0, z1, m, parent, o); };
      return {W, L, rect, pt, inv, b, axis: alongY ? 'y' : 'x'};
    }
    const frontOf = f => f.back_wall ? OPP[f.back_wall] : 'y1';

    function label(text, x, y, z, size = 0.5, parent = G.labels, color = '#22221f') {
      const lines = text.split('\n'), px = 64, pad = 18;
      const c = document.createElement('canvas'), ctx = c.getContext('2d');
      ctx.font = `600 ${px}px ${FONT}`;
      const w = Math.max(...lines.map(l => ctx.measureText(l).width)) + pad * 2, h = lines.length * px * 1.18 + pad * 1.4;
      c.width = Math.ceil(w); c.height = Math.ceil(h);
      ctx.fillStyle = 'rgba(255,255,255,.88)';
      const rr = Math.min(28, c.height / 2);
      ctx.beginPath(); ctx.moveTo(rr, 0); ctx.arcTo(c.width, 0, c.width, c.height, rr); ctx.arcTo(c.width, c.height, 0, c.height, rr);
      ctx.arcTo(0, c.height, 0, 0, rr); ctx.arcTo(0, 0, c.width, 0, rr); ctx.closePath(); ctx.fill();
      ctx.font = `600 ${px}px ${FONT}`; ctx.direction = 'rtl'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = color;
      lines.forEach((l, i) => ctx.fillText(l, c.width / 2, pad * 0.7 + px * 0.62 + i * px * 1.18));
      const tex = new T.CanvasTexture(c);
      tex.encoding = T.sRGBEncoding; tex.anisotropy = 4;
      // the same size on the screen from near and far, so the names stay readable (fitLabels sets the scale)
      const s = new T.Sprite(new T.SpriteMaterial({map: tex, depthTest: false, transparent: true, sizeAttenuation: false}));
      s.userData.label = {w: c.width / px, h: c.height / px, size};
      s.position.set(x, z, y); s.renderOrder = 20;
      parent.add(s); LABELS.push(s);
      return s;
    }
    function fitLabels() {   // letters of about 14px (12px on a phone); size 0.3 is a room name
      const H = stage.clientHeight || 600, k = (stage.clientWidth < 600 ? 12 : 14) * 2 * Math.tan(camera.fov * Math.PI / 360) / H;
      for (const s of LABELS) {
        const u = s.userData.label, f = k * u.size / 0.3;
        s.scale.set(f * u.w, f * u.h, 1);
      }
    }

    // ---------- the house ----------
    function floorOf(room) {
      if (room.kind === 'wet') return M.wet;
      if (room.kind === 'service') return M.service;
      if (room.kind === 'room' || room.kind === 'mamad') return M.wood;
      return M.porcelain;
    }
    function house() {
      for (const [x0, y0, x1, y1] of D.blocks || [[BX0, BY0, BX1, BY1]])   // under the house only, not under a patio
        box(x0, x1, y0, y1, -0.8, 0, [M.plinth0, M.plinth0, M.threshold, M.plinth0, M.plinth0, M.plinth0], G.house, {cast: false});
      for (const r of D.rooms) for (const [x0, y0, x1, y1] of r.rects) box(x0, x1, y0, y1, 0, 0.012, floorOf(r), G.house, {cast: false});
      for (const [x0, x1, y0, y1, z0, z1, kind] of D.walls) {
        const top = z1 >= CEIL - 1e-6 ? (kind === 'mamad' ? M.mamadCut : M.cut) : M.sill;
        box(x0, x1, y0, y1, z0, z1, [M.plaster, M.plaster, top, M.plaster, M.plaster, M.plaster]);
        if (z0 < 1) RULE.push([x0, y0, x1, y1]);
      }
      for (const o of D.openings) {
        if (o.t === 'hinged' || o.t === 'steel') door(o);
        if (o.t === 'window' || o.t === 'high' || o.t === 'glass') pane(o);
      }
    }
    function door(o) {   // the leaf open at 90°, as the plan draws its swing
      const [x0, y0, x1, y1] = o.r, horiz = (x1 - x0) >= (y1 - y0), steel = o.t === 'steel', front = o.ext === 'north';
      const w = (horiz ? x1 - x0 : y1 - y0) - 0.03, th = steel ? 0.07 : front ? 0.06 : 0.04, h = D.door - 0.015;
      const m = steel ? M.steelDoor : front ? M.frontDoor : o.ext ? M.extDoor : M.door;
      const dir = o.into > 0 ? 1 : -1;
      let r, hx, hy;
      if (horiz) {
        const face = o.into > 0 ? y1 : y0, x = o.hinge === 'x0' ? x0 + 0.015 : x1 - 0.015 - th;
        r = [x, x + th, Math.min(face, face + dir * w), Math.max(face, face + dir * w)];
        hx = null; hy = face + dir * (w - 0.07);
      } else {
        const face = o.into > 0 ? x1 : x0, y = o.hinge === 'y0' ? y0 + 0.015 : y1 - 0.015 - th;
        r = [Math.min(face, face + dir * w), Math.max(face, face + dir * w), y, y + th];
        hx = face + dir * (w - 0.07); hy = null;
      }
      box(r[0], r[1], r[2], r[3], 0.01, h, m);
      if (horiz) box(r[0] - 0.03, r[1] + 0.03, hy - 0.07, hy + 0.07, 1.0, 1.025, M.chrome);
      else box(hx - 0.07, hx + 0.07, r[2] - 0.03, r[3] + 0.03, 1.0, 1.025, M.chrome);
    }
    function pane(o) {   // the frame and the glass, in the middle of the wall
      const [x0, y0, x1, y1] = o.r, horiz = (x1 - x0) >= (y1 - y0);
      const [s, h] = o.t === 'window' ? [D.sill, D.head] : o.t === 'high' ? [D.high, D.head] : [0.012, D.glass];
      const mid = horiz ? (y0 + y1) / 2 : (x0 + x1) / 2, t = 0.06, fw = 0.05;
      const a0 = horiz ? x0 : y0, a1 = horiz ? x1 : y1;
      const B = (b0, b1, z0, z1, m, cast = true) => horiz ? box(b0, b1, mid - t / 2, mid + t / 2, z0, z1, m, G.house, {cast})
                                                          : box(mid - t / 2, mid + t / 2, b0, b1, z0, z1, m, G.house, {cast});
      B(a0, a1, s, s + fw, M.frame); B(a0, a1, h - fw, h, M.frame);
      B(a0, a0 + fw, s, h, M.frame); B(a1 - fw, a1, s, h, M.frame);
      const n = o.t === 'glass' ? 2 : (a1 - a0 > 1.3 ? 2 : 1);
      for (let i = 1; i < n; i++) { const a = a0 + i * (a1 - a0) / n; B(a - fw / 2, a + fw / 2, s, h, M.frame); }
      const g = horiz ? box(a0 + fw, a1 - fw, mid - 0.008, mid + 0.008, s + fw, h - fw, M.glass, G.house, {cast: false})
                      : box(mid - 0.008, mid + 0.008, a0 + fw, a1 - fw, s + fw, h - fw, M.glass, G.house, {cast: false});
      g.renderOrder = 5;
    }

    // ---------- furniture (samples; the sizes and places are the plan's) ----------
    function furnish(f) {
      const pal = PAL[f.room] || (f.room === 'lobby2' || f.room === 'wc' ? {} : PAL.public);
      switch (f.k) {
        case 'bed': return bed(f, pal);
        case 'crib': return crib(f);
        case 'sofa': return f.room === 'den' ? sofa(f, PAL.den.sofa, PAL.den.cushion) : sofa(f, PAL.public.sofa, PAL.public.cushion);
        case 'armchair': return sofa(f, PAL.public.arm, '#efe6d6', true);
        case 'table': return table(f);
        case 'island': return island(f);
        case 'counter': return counter(f);
        case 'tall': return tall(f);
        case 'fridge': return fridge(f);
        case 'wardrobe': return wardrobe(f);
        case 'shelf': return shelf(f);
        case 'wc': return wc(f);
        case 'basin': return basin(f);
        case 'shower': return shower(f);
        case 'bath': return bath(f);
        case 'washer': return washer(f);
        case 'desk': return desk(f, pal);
        case 'low': return low(f);
        case 'tv': return tv(f);
        case 'rug': return f.room === 'laundry' ? rack(f) : rug(f.r, PAL.public.rug);
        case 'plant': return plant(f.r[0], f.r[1], f.r[2]);
        case 'chair': return chair(f.r[0], f.r[1], f.face || 'y0');
        case 'skylight': return null;   // in the roof
        default: if (f.r.length === 4) box(f.r[0], f.r[2], f.r[1], f.r[3], 0, 0.6, M.white);
      }
      return null;
    }
    function blockers() {   // furniture footprints, for the shower screens
      for (const f of D.furniture) {
        if (['rug', 'skylight', 'shower'].includes(f.k)) continue;
        if (f.r.length === 4) RULE.push([f.r[0], f.r[1], f.r[2], f.r[3]]);
        else if (f.k === 'wc') {
          const [x, y] = f.r, face = f.face || 'y1';
          const ext = {y1: [x - .22, y - .09, x + .22, y + .61], y0: [x - .22, y - .61, x + .22, y + .09],
                       x1: [x - .09, y - .22, x + .61, y + .22], x0: [x - .61, y - .22, x + .09, y + .22]}[face];
          RULE.push(ext);
        }
      }
    }
    const blocked = (x, y) => RULE.some(([x0, y0, x1, y1]) => x > x0 && x < x1 && y > y0 && y < y1);

    function bed(f, pal) {
      const q = F(f.r, f.head || 'y0'), {W, L} = q, dbl = W > 1.25;
      q.b(0.04, W - 0.04, 0.1, L - 0.04, 0, 0.08, M.black);
      q.b(0, W, 0.06, L, 0.08, 0.3, M.oak);
      q.b(0.02, W - 0.02, 0.08, L - 0.02, 0.3, 0.5, M.sheet);
      q.b(-0.015, W + 0.015, 0.7, L + 0.015, 0.34, 0.545, mat(pal.duvet || '#9fb3c8', {roughness: 0.95}));
      q.b(-0.015, W + 0.015, 0.7, 0.88, 0.545, 0.565, M.sheet);
      const n = dbl ? 2 : 1, pw = (W - 0.16 - 0.08 * (n - 1)) / n;
      for (let i = 0; i < n; i++) q.b(0.08 + i * (pw + 0.08), 0.08 + i * (pw + 0.08) + pw, 0.12, 0.52, 0.5, 0.63, M.pillow);
      q.b(0, W, 0, 0.06, 0.08, dbl ? 1.12 : 0.92, mat(pal.head || '#d9c7a3', {roughness: 0.95}));
    }
    function crib(f) {
      const q = F(f.r, f.head || 'x0'), {W, L} = q, m = M.white, t = 0.035;
      for (const [u, v] of [[0, 0], [W - t, 0], [0, L - t], [W - t, L - t]]) q.b(u, u + t, v, v + t, 0, 0.92, m);
      for (const z of [0.3, 0.87]) {
        q.b(0, W, 0, t, z, z + 0.035, m); q.b(0, W, L - t, L, z, z + 0.035, m);
        q.b(0, t, 0, L, z, z + 0.035, m); q.b(W - t, W, 0, L, z, z + 0.035, m);
      }
      for (let v = 0.09; v < L - 0.07; v += 0.075) {
        q.b(0.008, 0.026, v, v + 0.018, 0.33, 0.87, m, G.house, {cast: false});
        q.b(W - 0.026, W - 0.008, v, v + 0.018, 0.33, 0.87, m, G.house, {cast: false});
      }
      for (let u = 0.09; u < W - 0.07; u += 0.075) {
        q.b(u, u + 0.018, 0.008, 0.026, 0.33, 0.87, m, G.house, {cast: false});
        q.b(u, u + 0.018, L - 0.026, L - 0.008, 0.33, 0.87, m, G.house, {cast: false});
      }
      q.b(t, W - t, t, L - t, 0.3, 0.42, M.sheet);
      q.b(t + 0.04, W - t - 0.04, L * 0.45, L - t - 0.03, 0.42, 0.46, mat('#a9c9dc', {roughness: 0.95}));
    }
    function sofa(f, color, accent, single = false) {
      const q = F(f.r, f.back || 'y0'), {W, L} = q, fab = mat(color, {roughness: 0.95}), fab2 = mat(shade(color, 0.07), {roughness: 0.95});
      const a = single ? 0.15 : 0.18, t = single ? 0.17 : 0.2;
      for (const u of [0.05, W - 0.09]) for (const v of [0.05, L - 0.09]) q.b(u, u + 0.04, v, v + 0.04, 0, 0.08, M.black);
      q.b(0, W, 0, L, 0.08, 0.36, fab);
      q.b(0, W, 0, t, 0.36, 0.84, fab);
      q.b(0, a, t, L, 0.36, 0.6, fab); q.b(W - a, W, t, L, 0.36, 0.6, fab);
      const n = single ? 1 : (f.seats || 3), cw = (W - 2 * a) / n;
      for (let i = 0; i < n; i++) {
        q.b(a + i * cw + 0.01, a + (i + 1) * cw - 0.01, t, L - 0.02, 0.36, 0.47, fab2);
        q.b(a + i * cw + 0.02, a + (i + 1) * cw - 0.02, t, t + 0.15, 0.47, 0.8, fab2);
      }
      if (!single) {
        const am = mat(accent, {roughness: 0.95});
        q.b(a + 0.05, a + 0.45, t + 0.14, t + 0.27, 0.47, 0.83, am);
        q.b(W - a - 0.45, W - a - 0.05, t + 0.14, t + 0.27, 0.47, 0.83, am);
      }
    }
    function chair(cx, cy, face, m = M.chair) {
      const w = 0.44, d = 0.42, alongY = face === 'y0' || face === 'y1';
      const r = alongY ? [cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2] : [cx - d / 2, cy - w / 2, cx + d / 2, cy + w / 2];
      const q = F(r, OPP[face]), {W, L} = q;
      for (const u of [0.02, W - 0.05]) for (const v of [0.02, L - 0.05]) q.b(u, u + 0.03, v, v + 0.03, 0, 0.44, M.oak);
      q.b(0, W, 0, L, 0.44, 0.48, m);
      q.b(0.02, W - 0.02, 0, 0.035, 0.48, 0.86, m);
    }
    function officeChair(cx, cy, face, color) {
      cyl(cx, cy, 0.02, 0.06, 0.27, M.black, G.house, {seg: 5});
      cyl(cx, cy, 0.06, 0.44, 0.025, M.black);
      const w = 0.48, d = 0.46, alongY = face === 'y0' || face === 'y1';
      const r = alongY ? [cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2] : [cx - d / 2, cy - w / 2, cx + d / 2, cy + w / 2];
      const q = F(r, OPP[face]), {W, L} = q, m = mat(color, {roughness: 0.9});
      q.b(0, W, 0, L, 0.44, 0.52, m);
      q.b(0.03, W - 0.03, 0.0, 0.05, 0.56, 0.98, m);
      q.b(W / 2 - 0.03, W / 2 + 0.03, 0.01, 0.05, 0.48, 0.58, M.black);
    }
    function pendant(x, y, z) {
      cyl(x, y, z + 0.2, CEIL, 0.005, M.black, G.pendants, {cast: false});
      cyl(x, y, z, z + 0.2, 0.14, mat('#2b2a28', {roughness: 0.5, side: T.DoubleSide}), G.pendants, {rTop: 0.045, open: true, cast: false});
      const bulb = ball(x, y, z + 0.06, 0.045, new T.MeshBasicMaterial({color: '#fff1cf'}), G.pendants, {cast: false});
      bulb.castShadow = false;
    }
    function table(f) {
      const [x0, y0, x1, y1] = f.r;
      box(x0, x1, y0, y1, 0.72, 0.76, M.oakTop);
      for (const x of [x0 + 0.06, x1 - 0.12]) for (const y of [y0 + 0.06, y1 - 0.12]) box(x, x + 0.06, y, y + 0.06, 0, 0.72, M.oak);
      const n = f.seats || 0, longX = (x1 - x0) >= (y1 - y0);
      if (n) {
        const per = Math.floor(n / 2) - (f.ends ? 1 : 0);
        for (let i = 0; i < per; i++) {
          if (longX) { const cx = x0 + (i + 0.5) * (x1 - x0) / per; chair(cx, y0 - 0.2, 'y1'); chair(cx, y1 + 0.2, 'y0'); }
          else { const cy = y0 + (i + 0.5) * (y1 - y0) / per; chair(x0 - 0.2, cy, 'x1'); chair(x1 + 0.2, cy, 'x0'); }
        }
        if (f.ends) {
          if (longX) { chair(x0 - 0.2, (y0 + y1) / 2, 'x1'); chair(x1 + 0.2, (y0 + y1) / 2, 'x0'); }
          else { chair((x0 + x1) / 2, y0 - 0.2, 'y1'); chair((x0 + x1) / 2, y1 + 0.2, 'y0'); }
        }
      }
      // a bowl of fruit, and two pendants over the table
      cyl((x0 + x1) / 2, (y0 + y1) / 2, 0.76, 0.84, 0.13, M.white, G.house, {rTop: 0.16});
      const r = rng(41);
      for (let i = 0; i < 5; i++) ball((x0 + x1) / 2 + (r() - .5) * .14, (y0 + y1) / 2 + (r() - .5) * .14, 0.86, 0.04, mat(pick(r, ['#e0a030', '#c8452f', '#9cb84a'])), G.house, {cast: false});
      for (const a of [0.3, 0.7]) longX ? pendant(x0 + (x1 - x0) * a, (y0 + y1) / 2, 1.62) : pendant((x0 + x1) / 2, y0 + (y1 - y0) * a, 1.62);
    }
    function island(f) {
      const q = F(f.r, f.stools ? OPP[f.stools] : 'y0'), {W, L} = q, oh = 0.25;   // v: from the cook to the stools
      q.b(0.05, W - 0.05, 0.05, L - oh, 0, 0.1, M.plinthK);
      q.b(0, W, 0, L - oh, 0.1, 0.86, M.island);
      q.b(-0.01, W + 0.01, -0.01, L, 0.86, 0.9, M.quartz);
      for (let u = 0.3; u < W - 0.1; u += 0.6) q.b(u - 0.17, u + 0.17, -0.025, -0.005, 0.79, 0.805, M.steel);
      if (f.hob) {
        const [hx, hy] = f.hob;
        box(hx - 0.3, hx + 0.3, hy - 0.26, hy + 0.26, 0.9, 0.906, M.hob, G.house, {cast: false});
        for (const [dx, dy, rr] of [[-0.14, -0.12, 0.09], [0.14, 0.12, 0.09], [-0.14, 0.12, 0.065], [0.14, -0.12, 0.065]]) {
          cyl(hx + dx, hy + dy, 0.906, 0.908, rr, M.ring, G.house, {cast: false, seg: 28});
        }
        const [u] = q.inv(hx, hy);   // the oven under the hob, on the cook's side
        q.b(u - 0.3, u + 0.3, -0.012, 0.0, 0.12, 0.72, M.ovenGlass, G.house, {cast: false});
        q.b(u - 0.25, u + 0.25, -0.045, -0.012, 0.68, 0.7, M.steel, G.house, {cast: false});
      }
      const n = f.n || 3, [x0, y0, x1, y1] = f.r;
      // recessed spots in the ceiling over the island: nothing hangs between the cook and the living room
      for (const t of [0.22, 0.5, 0.78]) {
        const [px, py] = q.pt(W * t, L / 2);
        cyl(px, py, CEIL - 0.009, CEIL - 0.005, 0.065, M.trim, G.pendants, {cast: false, seg: 28});
        cyl(px, py, CEIL - 0.011, CEIL - 0.009, 0.045, M.spot, G.pendants, {cast: false, seg: 28});
      }
      for (let i = 0; i < n; i++) {
        let cx, cy;
        if (f.stools === 'y1' || f.stools === 'y0') { cx = x0 + (i + 0.5) * (x1 - x0) / n; cy = f.stools === 'y1' ? y1 + 0.25 : y0 - 0.25; }
        else { cy = y0 + (i + 0.5) * (y1 - y0) / n; cx = f.stools === 'x1' ? x1 + 0.25 : x0 - 0.25; }
        cyl(cx, cy, 0, 0.025, 0.2, M.black);
        cyl(cx, cy, 0.025, 0.63, 0.022, M.black);
        cyl(cx, cy, 0.3, 0.32, 0.15, M.black, G.house, {cast: false});
        cyl(cx, cy, 0.63, 0.68, 0.18, M.oak);
      }
    }
    function counter(f) {
      const q = F(f.r, f.front ? OPP[f.front] : (f.back_wall || 'y0')), {W, L} = q, lau = f.room === 'laundry';
      q.b(0, W, 0, L - 0.06, 0, 0.1, M.plinthK);
      q.b(0, W, 0, L - 0.02, 0.1, 0.86, lau ? M.white : M.cabinet);
      q.b(0, W, 0, L, 0.86, 0.9, M.quartz);
      for (let u = 0.3; u < W - 0.1; u += 0.6) q.b(u - 0.15, u + 0.15, L - 0.02, L, 0.79, 0.805, M.steel);
      if (f.sink) {
        const [sx, sy] = f.sink, vert = f.sinkdir === 'y';
        for (const d of [-0.21, 0.21]) {
          const [bx, by] = vert ? [sx, sy + d] : [sx + d, sy];
          const [hw, hd] = vert ? [0.19, 0.18] : [0.18, 0.19];
          box(bx - hw, bx + hw, by - hd, by + hd, 0.886, 0.903, M.sinkSteel, G.house, {cast: false});
        }
        const [tu] = q.inv(sx, sy), [tx, ty] = q.pt(tu, 0.07), [ex, ey] = q.pt(tu, 0.24);
        cyl(tx, ty, 0.9, 1.22, 0.016, M.chrome);
        box(Math.min(tx, ex) - 0.013, Math.max(tx, ex) + 0.013, Math.min(ty, ey) - 0.013, Math.max(ty, ey) + 0.013, 1.19, 1.22, M.chrome);
      }
    }
    function doorGaps(q, H, m) {   // the gaps between cabinet doors, about 50 cm apart
      const {W, L} = q, n = Math.max(1, Math.round(W / 0.5));
      for (let i = 1; i < n; i++) q.b(i * W / n - 0.004, i * W / n + 0.004, L - 0.004, L + 0.002, 0.06, H - 0.02, M.gap, G.house, {cast: false});
      return n;
    }
    function tall(f) {
      const q = F(f.r, f.back_wall || 'y0'), {W, L} = q, H = 2.3, m = f.room === 'laundry' ? M.oakLight : M.white;
      q.b(0, W, 0, L, 0, H, m);
      doorGaps(q, H, m);
    }
    function fridge(f) {
      const q = F(f.r, f.back_wall || 'y0'), {W, L} = q;
      q.b(0.015, W - 0.015, 0, L - 0.03, 0, 1.86, M.fridge);
      q.b(0.015, W - 0.015, L - 0.03, L - 0.01, 0.01, 1.86, M.fridge);
      q.b(0.015, W - 0.015, L - 0.012, L - 0.006, 0.735, 0.75, M.gap, G.house, {cast: false});
      q.b(0.05, 0.07, L - 0.01, L + 0.025, 0.9, 1.65, M.chrome, G.house, {cast: false});
      q.b(0.05, 0.07, L - 0.01, L + 0.025, 0.42, 0.7, M.chrome, G.house, {cast: false});
    }
    function wardrobe(f) {
      const q = F(f.r, f.back_wall || 'y0'), {W, L} = q, H = 2.4;
      const m = f.room === 'mamad' || f.room === 'public' ? M.white : M.oakLight;
      q.b(0, W, 0, L, 0, H, m);
      const n = doorGaps(q, H, m);
      for (let i = 0; i < n; i++) {
        const u = i * W / n + (i % 2 ? 0.06 : W / n - 0.06);
        q.b(u - 0.01, u + 0.01, L, L + 0.025, 0.95, 1.35, M.steel, G.house, {cast: false});
      }
    }
    function shelf(f) {
      const q = F(f.r, f.back_wall || 'y0'), {W, L} = q, pantry = f.room === 'pantry';
      const H = pantry ? 1.52 : 2.0, n = pantry ? 5 : 6, m = M.oakLight, step = (H - 0.1) / (n - 1);
      q.b(0, 0.025, 0, L, 0, H, m); q.b(W - 0.025, W, 0, L, 0, H, m);
      const r = rng(Math.round(f.r[0] * 100 + f.r[1] * 10));
      for (let i = 0; i < n; i++) {
        const z = 0.08 + i * step;
        q.b(0, W, 0, L, z, z + 0.025, m);
        if (i === n - 1) break;
        let u = 0.05;
        while (u < W - 0.12) {
          const w = pantry ? 0.08 + r() * 0.12 : 0.025 + r() * 0.035, h = Math.min(pantry ? 0.1 + r() * 0.17 : 0.17 + r() * 0.12, step - 0.06);
          if (r() < (pantry ? 0.8 : 0.92)) {
            const d = pantry ? L - 0.08 - r() * 0.08 : L - 0.06;
            if (pantry && r() < 0.45) {
              const [cx, cy] = q.pt(u + w / 2, 0.04 + d / 2);
              cyl(cx, cy, z + 0.025, z + 0.025 + h, Math.min(w, d) / 2, mat(pick(r, FOOD), {roughness: 0.5}), G.house, {cast: false, seg: 12});
            } else q.b(u, u + w, 0.04, 0.04 + d, z + 0.025, z + 0.025 + h, mat(pick(r, pantry ? FOOD : BOOKS)), G.house, {cast: false});
          }
          u += w + (pantry ? 0.03 : 0.004);
        }
      }
    }
    function wc(f) {
      const [x, y] = f.r, face = f.face || 'y1';
      const [dx, dy] = {y1: [0, 1], y0: [0, -1], x1: [1, 0], x0: [-1, 0]}[face], along = dx === 0;
      box(x - (along ? 0.22 : 0.09), x + (along ? 0.22 : 0.09), y - (along ? 0.09 : 0.22), y + (along ? 0.09 : 0.22), 0, 0.82, M.ceramic);
      box(x - (along ? 0.1 : 0.095), x + (along ? 0.1 : 0.095), y - (along ? 0.095 : 0.1), y + (along ? 0.095 : 0.1), 0.82, 0.825, M.chrome, G.house, {cast: false});
      const [ex, ey] = along ? [0.18, 0.25] : [0.25, 0.18];
      cyl(x + dx * 0.36, y + dy * 0.36, 0, 0.39, 0.78, M.ceramic, G.house, {rTop: 1, sx: ex, sy: ey, seg: 28});
      cyl(x + dx * 0.36, y + dy * 0.36, 0.39, 0.42, 1, M.ceramic, G.house, {sx: ex * 1.04, sy: ey * 1.04, seg: 28});
    }
    function basin(f) {
      const back = f.back_wall || 'y0', q = F(f.r, back), {W, L} = q, n = f.n || 1;
      q.b(0, W, 0, L, 0.44, 0.82, M.vanity);
      q.b(-0.005, W + 0.005, 0, L + 0.01, 0.82, 0.86, M.ceramic);
      for (let i = 0; i < n; i++) {
        const u = (i + 0.5) * W / n, [bx, by] = q.pt(u, L * 0.56), ru = W / n * 0.32, rv = L * 0.3;
        cyl(bx, by, 0.84, 0.862, 1, M.basinIn, G.house, {sx: q.axis === 'y' ? ru : rv, sy: q.axis === 'y' ? rv : ru, seg: 28, cast: false});
        const [tx, ty] = q.pt(u, 0.06), [ex, ey] = q.pt(u, 0.17);
        cyl(tx, ty, 0.86, 1.03, 0.013, M.chrome, G.house, {cast: false});
        box(Math.min(tx, ex) - 0.011, Math.max(tx, ex) + 0.011, Math.min(ty, ey) - 0.011, Math.max(ty, ey) + 0.011, 1.0, 1.025, M.chrome, G.house, {cast: false});
      }
      q.b(0.02, W - 0.02, 0, 0.02, 1.05, 1.85, M.mirror, G.house, {cast: false});
    }
    function shower(f) {
      const [x0, y0, x1, y1] = f.r, w = f.walls || {};
      box(x0, x1, y0, y1, 0, 0.035, M.tray, G.house, {cast: false});
      const open = ['x0', 'x1', 'y0', 'y1'].filter(s => (w[s] || 0) < 0.5);
      const out = s => ({x0: [x0 - 0.45, (y0 + y1) / 2], x1: [x1 + 0.45, (y0 + y1) / 2], y0: [(x0 + x1) / 2, y0 - 0.45], y1: [(x0 + x1) / 2, y1 + 0.45]}[s]);
      const len = s => s[0] === 'x' ? y1 - y0 : x1 - x0;
      let glass = open.filter(s => blocked(...out(s)));                 // screens where something stands close
      if (glass.length === open.length) glass = open.slice().sort((a, b) => len(a) - len(b)).slice(0, -1);   // keep a way in
      if (!glass.length && open.length) glass = [open.slice().sort((a, b) => len(b) - len(a))[0]];
      for (const s of glass) {
        const t = 0.012, r = {x0: [x0, x0 + t, y0, y1], x1: [x1 - t, x1, y0, y1], y0: [x0, x1, y0, y0 + t], y1: [x0, x1, y1 - t, y1]}[s];
        box(r[0], r[1], r[2], r[3], 0.035, 2.0, M.showerGlass, G.house, {cast: false}).renderOrder = 5;
        box(r[0] - 0.005, r[1] + 0.005, r[2] - 0.005, r[3] + 0.005, 1.98, 2.0, M.chrome, G.house, {cast: false});
      }
      const back = ['y0', 'x0', 'x1', 'y1'].find(s => (w[s] || 0) >= 0.5) || 'y0';
      const q = F(f.r, back), [hx, hy] = q.pt(q.W / 2, 0.025), [sx, sy] = q.pt(q.W / 2, 0.2);
      cyl(hx, hy, 0.9, 2.05, 0.012, M.chrome, G.house, {cast: false});
      box(Math.min(hx, sx) - 0.012, Math.max(hx, sx) + 0.012, Math.min(hy, sy) - 0.012, Math.max(hy, sy) + 0.012, 2.03, 2.05, M.chrome, G.house, {cast: false});
      cyl(sx, sy, 1.99, 2.03, 0.11, M.chrome, G.house, {cast: false});
    }
    function bath(f) {
      const [x0, y0, x1, y1] = f.r;
      box(x0, x1, y0, y1, 0, 0.55, M.ceramic);
      box(x0 + 0.08, x1 - 0.08, y0 + 0.08, y1 - 0.08, 0.5, 0.552, M.basinIn, G.house, {cast: false});
    }
    function washer(f) {
      const q = F(f.r, f.back_wall || 'x0'), {W, L} = q, units = f.stack ? 2 : 1;
      for (let i = 0; i < units; i++) {
        const z0 = i * 0.87;
        q.b(0.02, W - 0.02, 0.02, L - 0.04, z0, z0 + 0.85, M.appliance);
        q.b(0.04, W - 0.04, L - 0.045, L - 0.035, z0 + 0.74, z0 + 0.82, M.panel, G.house, {cast: false});
        const [dx, dy] = q.pt(W / 2, L - 0.035);
        disc(dx, dy, z0 + 0.4, 0.2, q.axis === 'y' ? 'y' : 'x', M.panel);
        const [gx, gy] = q.pt(W / 2, L - 0.02);
        disc(gx, gy, z0 + 0.4, 0.15, q.axis === 'y' ? 'y' : 'x', M.ovenGlass);
      }
      if (f.room === 'laundry') {   // the machines stand inside the long cabinet
        q.b(0, W, 0, L, units * 0.87 + 0.02, 2.3, M.oakLight);
        q.b(0, W, 0, 0.03, 0, units * 0.87 + 0.02, M.oakLight);
      }
    }
    function desk(f, pal) {
      const [x0, y0, x1, y1] = f.r;
      let back = f.back_wall;
      if (!back && f.chair) {
        const [cx, cy] = f.chair;
        back = cx > x1 ? 'x0' : cx < x0 ? 'x1' : cy > y1 ? 'y0' : 'y1';
      }
      const q = F(f.r, back || 'y0'), {W, L} = q;
      q.b(0, W, 0, L, 0.72, 0.75, mat(pal.desk || '#f5f3ef', {roughness: 0.5}));
      q.b(0.02, 0.05, 0.03, L - 0.03, 0, 0.72, M.black); q.b(W - 0.05, W - 0.02, 0.03, L - 0.03, 0, 0.72, M.black);
      if (f.room === 'den') {
        q.b(W / 2 - 0.3, W / 2 + 0.3, 0.1, 0.13, 0.93, 1.28, M.screen);
        q.b(W / 2 - 0.03, W / 2 + 0.03, 0.13, 0.17, 0.75, 0.95, M.black);
        q.b(W / 2 - 0.12, W / 2 + 0.12, 0.08, 0.24, 0.75, 0.76, M.black);
        q.b(W / 2 - 0.22, W / 2 + 0.22, 0.32, 0.47, 0.75, 0.765, M.panel, G.house, {cast: false});
      } else {
        const [lx, ly] = q.pt(0.14, 0.12);
        cyl(lx, ly, 0.75, 0.77, 0.07, M.black); cyl(lx, ly, 0.77, 1.12, 0.008, M.black, G.house, {cast: false});
        cyl(lx, ly, 1.08, 1.2, 0.1, mat(pal.chair || '#e2b33c'), G.house, {rTop: 0.04, cast: false});
        const r = rng(Math.round(x0 * 50));
        for (let i = 0; i < 4; i++) q.b(W - 0.42, W - 0.12, 0.08, 0.3, 0.75 + i * 0.035, 0.785 + i * 0.035, mat(pick(r, BOOKS)), G.house, {cast: false});
      }
      if (f.chair) officeChair(f.chair[0], f.chair[1], f.face || 'y0', pal.chair || '#2f2f2f');
    }
    function low(f) {
      const [x0, y0, x1, y1] = f.r;
      box(x0, x1, y0, y1, 0.36, 0.4, M.oakTop);
      for (const x of [x0 + 0.04, x1 - 0.08]) for (const y of [y0 + 0.04, y1 - 0.08]) box(x, x + 0.04, y, y + 0.04, 0, 0.36, M.black);
      box(x0 + 0.08, x0 + 0.3, y0 + 0.1, y0 + 0.4, 0.4, 0.43, mat('#c0573e'), G.house, {cast: false});
      cyl((x0 + x1) / 2 + 0.05, y1 - 0.2, 0.4, 0.58, 0.06, mat('#e9e4da', {roughness: 0.3}), G.house, {rTop: 0.035});
    }
    function tv(f) {
      const q = F(f.r, f.back_wall || 'x1'), {W, L} = q, sw = Math.min(1.4, W - 0.2);
      q.b(0, W, 0, L, 0.1, 0.48, M.walnut);
      q.b(W / 2 - sw / 2, W / 2 + sw / 2, 0.02, 0.055, 0.7, 0.7 + sw * 0.5625, M.screen);
    }
    function rug(r, color) {
      const [x0, y0, x1, y1] = r;
      box(x0, x1, y0, y1, 0.012, 0.024, mat(color, {roughness: 1}), G.house, {cast: false});
      box(x0 + 0.1, x1 - 0.1, y0 + 0.1, y1 - 0.1, 0.024, 0.026, mat(shade(color, -0.12), {roughness: 1}), G.house, {cast: false});
    }
    function rack(f) {   // the drying rack under the ceiling of the laundry room, with a few clothes
      const [x0, y0, x1, y1] = f.r, long = (y1 - y0) >= (x1 - x0), z = 2.12, r = rng(53);
      const span = long ? x1 - x0 : y1 - y0, run = long ? y1 - y0 : x1 - x0;
      for (let k = 0; k < 6; k++) {
        const a = 0.06 + k * (span - 0.12) / 5;
        if (long) rod([x0 + a, y0 + 0.03, z], [x0 + a, y1 - 0.03, z], 0.011, M.chrome);
        else rod([x0 + 0.03, y0 + a, z], [x1 - 0.03, y0 + a, z], 0.011, M.chrome);
      }
      for (const k of [0, 1]) {
        if (long) { const y = k ? y1 - 0.03 : y0 + 0.03; rod([x0, y, z], [x1, y, z], 0.015, M.chrome); }
        else { const x = k ? x1 - 0.03 : x0 + 0.03; rod([x, y0, z], [x, y1, z], 0.015, M.chrome); }
      }
      for (let k = 0; k < 4; k++) {
        const a = 0.06 + (k + 0.5) * (span - 0.12) / 5, s = 0.25 + r() * 0.3, at = 0.12 + r() * (run - 0.55);
        const h = 0.35 + r() * 0.3, m = mat(pick(r, CLOTHES), {roughness: 1, side: T.DoubleSide});
        if (long) box(x0 + a - 0.004, x0 + a + 0.004, y0 + at, y0 + at + s, z - h, z, m, G.house, {cast: false});
        else box(x0 + at, x0 + at + s, y0 + a - 0.004, y0 + a + 0.004, z - h, z, m, G.house, {cast: false});
      }
    }
    function plant(x, y, r = 0.22, h = 1.3) {
      cyl(x, y, 0, 0.36, r * 0.75, M.terracotta, G.house, {rTop: r});
      cyl(x, y, 0.34, 0.37, r * 0.95, M.earth, G.house, {cast: false});
      const g = mat('#4f7d3a', {roughness: 0.9, flatShading: true}), g2 = mat('#6a9a48', {roughness: 0.9, flatShading: true});
      ball(x, y, h * 0.62, r * 1.5, g, G.house, {ico: true, detail: 1});
      ball(x + r * 0.5, y - r * 0.4, h * 0.86, r * 1.1, g2, G.house, {ico: true, detail: 1});
      ball(x - r * 0.45, y + r * 0.3, h * 0.95, r * 0.9, g, G.house, {ico: true, detail: 1});
    }

    // ---------- the roof (it can hide, or stay only as a shadow) ----------
    function roof() {
      const R = G.roof;
      for (const [x0, x1, y0, y1] of D.slab) box(x0, x1, y0, y1, CEIL - 0.003, TOP, [M.plaster, M.plaster, M.membrane, M.ceiling, M.plaster, M.plaster], R);
      for (const a of D.roof) {
        const [x0, y0, x1, y1] = a.r;
        if (a.k === 'flat') {
          const P = 0.4, t = 0.25, edges = [];
          if (y0 <= BY0 + 1e-6) edges.push([x0, x1, y0, y0 + t]);
          if (y1 >= BY1 - 1e-6) edges.push([x0, x1, y1 - t, y1]);
          if (x0 <= BX0 + 1e-6) edges.push([x0, x0 + t, y0, y1]);
          if (x1 >= BX1 - 1e-6) edges.push([x1 - t, x1, y0, y1]);
          for (const [a0, a1, b0, b1] of edges) {
            box(a0, a1, b0, b1, TOP, TOP + P, M.plaster, R);
            box(a0 - 0.02, a1 + 0.02, b0 - 0.02, b1 + 0.02, TOP + P, TOP + P + 0.04, M.coping, R);
          }
        } else if (a.k === 'terrace') {   // a roof to walk on: pavers, and the railing below
          box(x0, x1, y0, y1, TOP, TOP + 0.03, M.paverWarm, R, {cast: false});
        } else tileRoof(a, R);
      }
      for (const [x0, y0, x1, y1] of D.rails || []) {   // the terrace's railing, 1.05 m: a rail, posts and glass
        const t = 0.025, z1 = TOP + 1.05, horiz = Math.abs(y1 - y0) < 1e-6;
        box(Math.min(x0, x1) - t, Math.max(x0, x1) + t, Math.min(y0, y1) - t, Math.max(y0, y1) + t, z1 - 0.05, z1, M.frame, R);
        const n = Math.max(1, Math.round(Math.hypot(x1 - x0, y1 - y0) / 1.5));
        for (let i = 0; i <= n; i++) {
          const x = x0 + (x1 - x0) * i / n, y = y0 + (y1 - y0) * i / n;
          box(x - t, x + t, y - t, y + t, TOP, z1, M.frame, R);
        }
        const g = horiz ? box(Math.min(x0, x1), Math.max(x0, x1), y0 - 0.006, y0 + 0.006, TOP + 0.08, z1 - 0.05, M.glass, R, {cast: false})
                        : box(x0 - 0.006, x0 + 0.006, Math.min(y0, y1), Math.max(y0, y1), TOP + 0.08, z1 - 0.05, M.glass, R, {cast: false});
        g.renderOrder = 5;
      }
      for (const [x0, y0, x1, y1] of D.skylights) {   // a curb and a glass top
        const c = 0.08, z1 = TOP + 0.22;
        box(x0 - c, x1 + c, y0 - c, y0, TOP, z1, M.plaster, R); box(x0 - c, x1 + c, y1, y1 + c, TOP, z1, M.plaster, R);
        box(x0 - c, x0, y0, y1, TOP, z1, M.plaster, R); box(x1, x1 + c, y0, y1, TOP, z1, M.plaster, R);
        box(x0 - c, x1 + c, y0 - c, y1 + c, z1, z1 + 0.02, M.glass, R, {cast: false}).renderOrder = 5;
      }
    }
    function slope(xa, za, xb, zb, y0, y1, R) {   // a sloped slab of tiles between two edges along y
      const len = Math.hypot(xb - xa, zb - za), t = 0.1, geo = new T.BoxGeometry(len, t, y1 - y0);
      worldUV(geo, 0, 0, (y0 + y1) / 2, M.tiles.map.meters);
      const mesh = new T.Mesh(geo, [M.coping, M.coping, M.tiles, M.ceiling, M.coping, M.coping]);
      mesh.position.set((xa + xb) / 2, (za + zb) / 2 + t / 2, (y0 + y1) / 2);
      mesh.rotation.z = Math.atan2(zb - za, xb - xa);
      mesh.castShadow = mesh.receiveShadow = true;
      R.add(mesh);
    }
    function slopeX(ya, za, yb, zb, x0, x1, R) {   // a sloped slab of tiles between two edges along x
      const len = Math.hypot(yb - ya, zb - za), t = 0.1, geo = new T.BoxGeometry(x1 - x0, t, len);
      worldUV(geo, (x0 + x1) / 2, 0, 0, M.tiles.map.meters);
      const mesh = new T.Mesh(geo, [M.coping, M.coping, M.tiles, M.ceiling, M.coping, M.coping]);
      mesh.position.set((x0 + x1) / 2, (za + zb) / 2 + t / 2, (ya + yb) / 2);
      mesh.rotation.x = Math.atan2(-(zb - za), yb - ya);
      mesh.castShadow = mesh.receiveShadow = true;
      R.add(mesh);
    }
    function tileRoof(a, R) {
      const [x0, y0, x1, y1] = a.r, s = 0.5, gy = 0.3;
      const eastOh = x1 >= BX1 - 1e-6 ? 0.5 : 0, westOh = x0 <= BX0 + 1e-6 ? 0.5 : 0;
      if (a.slope === 'gable-y') {   // the ridge along y in the middle; the water runs to -x and +x
        const cx = (x0 + x1) / 2, ridge = TOP + (cx - x0) * s;
        slope(x0 - westOh, TOP - westOh * s, cx, ridge, y0 - gy, y1 + gy, R);
        slope(cx, ridge, x1 + eastOh, TOP - eastOh * s, y0 - gy, y1 + gy, R);
        for (const [ya, yb] of [[y0, y0 + 0.25], [y1 - 0.25, y1]]) {
          const sh = new T.Shape();
          sh.moveTo(x0, TOP); sh.lineTo(x1, TOP); sh.lineTo(cx, ridge); sh.lineTo(x0, TOP);
          const mesh = new T.Mesh(new T.ExtrudeGeometry(sh, {depth: yb - ya, bevelEnabled: false}), M.plaster);
          mesh.position.z = ya; mesh.castShadow = mesh.receiveShadow = true;
          R.add(mesh);
        }
        box(cx - 0.11, cx + 0.11, y0 - gy, y1 + gy, ridge + 0.06, ridge + 0.17, M.terracotta, R);
      } else if (a.slope === 'gable-x') {   // the ridge along x in the middle; the water runs to -y and +y
        const cy = (y0 + y1) / 2, ridge = TOP + (cy - y0) * s, gx = 0.3;
        const northOh = y0 <= BY0 + 1e-6 ? 0.5 : 0, southOh = y1 >= BY1 - 1e-6 ? 0.5 : 0;
        slopeX(y0 - northOh, TOP - northOh * s, cy, ridge, x0 - gx, x1 + gx, R);
        slopeX(cy, ridge, y1 + southOh, TOP - southOh * s, x0 - gx, x1 + gx, R);
        for (const [xa, xb] of [[x0, x0 + 0.25], [x1 - 0.25, x1]]) {   // the gable ends: the shape's x is the plan's y
          const sh = new T.Shape();
          sh.moveTo(y0, TOP); sh.lineTo(y1, TOP); sh.lineTo(cy, ridge); sh.lineTo(y0, TOP);
          const mesh = new T.Mesh(new T.ExtrudeGeometry(sh, {depth: xb - xa, bevelEnabled: false}), M.plaster);
          mesh.rotation.y = -Math.PI / 2; mesh.position.x = xb;
          mesh.castShadow = mesh.receiveShadow = true;
          R.add(mesh);
        }
        box(x0 - gx, x1 + gx, cy - 0.11, cy + 0.11, ridge + 0.06, ridge + 0.17, M.terracotta, R);
      } else {   // a single slope: a simple shed for now
        box(x0, x1, y0, y1, TOP, TOP + 0.6, M.terracotta, R);
      }
    }

    // ---------- the site and the garden ----------
    function ground(x0, x1, y0, y1, top, m, parent = G.site) {
      return box(x0, x1, y0, y1, -1.6, top, [M.earth, M.earth, m, M.earth, M.earth, M.earth], parent, {cast: false});
    }
    const sunk = (x, y) => SUNKEN.some(([x0, x1, y0, y1]) => x >= x0 && x <= x1 && y >= y0 && y <= y1);
    function site() {
      const [PW, PD] = D.plot;
      ground(-40, 60, -14, 0, STREET, M.paverGrey);
      ground(-40, 60, -30, -14, -0.4, M.grassMuted);
      for (const [x0, x1, y0, y1] of SUNKEN) { ground(x0, x1, y0, y1, SUNK, M.paverGrey); ground(-x1, -x0, y0, y1, SUNK, M.paverGrey); }
      ground(8.1, PW, 0, 3.6, GARDEN, M.cover); ground(6.85, PW, 3.6, 5.0, GARDEN, M.cover);
      ground(0, PW, 5.0, PD, GARDEN, M.soil);
      ground(-PW, -8.1, 0, 3.6, GARDEN, M.grassMuted); ground(-PW, -6.85, 3.6, 5.0, GARDEN, M.grassMuted);
      ground(-PW, 0, 5.0, PD, GARDEN, M.grassMuted);
      ground(PW, 2 * PW, 0, PD, GARDEN - 0.5, M.grassMuted);
      ground(-40, -PW, 0, PD, GARDEN, M.grassMuted); ground(2 * PW, 60, 0, PD, GARDEN - 0.5, M.grassMuted);
      ground(-40, 60, PD, PD + 12.2, GARDEN, M.grassMuted);                   // the green strip
      box(-40, 60, PD + 5.4, PD + 7.2, GARDEN, GARDEN + 0.02, M.paverWarm, G.site, {cast: false});
      ground(-40, 60, PD + 12.2, 60, GARDEN + 1.0, M.grassMuted);
      box(-40, 60, PD + 12.0, PD + 12.2, GARDEN, GARDEN + 1.05, M.stone, G.site);
      // retaining walls: along the street east of the steps, between the parking and the garden, toward the east neighbors
      box(8.1, PW, -0.22, 0, STREET, GARDEN + 0.12, M.stone, G.site); box(-PW, -8.1, -0.22, 0, STREET, GARDEN + 0.12, M.stone, G.site);
      box(8.08, 8.3, 0, 3.6, SUNK, GARDEN + 0.12, M.stone, G.site); box(-8.3, -8.08, 0, 3.6, SUNK, GARDEN + 0.12, M.stone, G.site);
      box(6.83, 7.05, 3.6, 5.0, SUNK, -0.005, M.stone, G.site); box(-7.05, -6.83, 3.6, 5.0, SUNK, -0.005, M.stone, G.site);
      box(PW, PW + 0.2, 0, PD, GARDEN - 0.5, GARDEN + 0.12, M.stone, G.site);
      // the plot's edge in the garden
      box(-0.04, 0.04, BY1, PD, GARDEN, GARDEN + 0.08, M.coping, G.site, {cast: false});
      box(0, PW, PD - 0.08, PD, GARDEN, GARDEN + 0.08, M.coping, G.site, {cast: false});
      // the parking: stall lines and a car
      for (const x of [D.stalls[0][0], D.stalls[0][2], D.stalls[1][2]]) box(x - 0.05, x + 0.05, 0.3, 5.0, SUNK, SUNK + 0.006, M.line, G.site, {cast: false});
      const st = D.stalls[1];
      car((st[0] + st[2]) / 2, 0.4, SUNK);
      // the garden, from the plan
      for (const g of D.garden) gardenItem(g);
      north(16.5, -4.5);
    }
    function car(cx, y0, z) {   // nose toward the house
      const x0 = cx - 0.9, x1 = cx + 0.9, y1 = y0 + 4.4, P = G.site;
      box(x0 + 0.03, x1 - 0.03, y0 + 0.05, y1 - 0.05, z + 0.3, z + 0.82, M.paint, P);
      box(x0 + 0.1, x1 - 0.1, y0 + 0.2, y1 - 0.3, z + 0.82, z + 0.9, M.paint, P);
      box(x0 + 0.16, x1 - 0.16, y0 + 1.25, y1 - 1.25, z + 0.9, z + 1.38, M.carGlass, P);
      box(x0 + 0.18, x1 - 0.18, y0 + 1.4, y1 - 1.4, z + 1.38, z + 1.44, M.paint, P);
      for (const x of [x0 + 0.12, x1 - 0.12]) for (const y of [y0 + 0.85, y1 - 0.8]) {
        const w = cyl(x, y, z + 0.32 - 0.11, z + 0.32 + 0.11, 0.33, M.tyre, P, {seg: 18});
        w.rotation.z = Math.PI / 2; w.position.set(x, z + 0.33, y);
      }
      for (const x of [x0 + 0.25, x1 - 0.45]) box(x, x + 0.2, y0 + 0.02, y0 + 0.06, z + 0.62, z + 0.72, mat('#c4302b'), P, {cast: false});
    }
    function north(x, y) {   // a flat arrow on the street, pointing north
      const th = -UP_AZ * Math.PI / 180, dx = Math.sin(th), dy = -Math.cos(th), L = 1.6;
      const sh = new T.Shape();
      sh.moveTo(0, L / 2); sh.lineTo(0.35, -L / 2); sh.lineTo(0, -L / 4); sh.lineTo(-0.35, -L / 2); sh.lineTo(0, L / 2);
      const mesh = new T.Mesh(new T.ShapeGeometry(sh), mat('#2b2a28'));
      mesh.rotation.x = -Math.PI / 2;
      mesh.rotation.z = -th;
      mesh.position.set(x, STREET + 0.01, y);
      G.site.add(mesh);
      label('צפון', x + dx * 2.2, y + dy * 2.2, STREET + 0.4, 0.32);
    }
    function gardenItem(g) {
      const r = g.r, P = G.site;
      const [x0, y0, x1, y1] = r.length === 4 ? r : [r[0] - r[2], r[1] - r[2], r[0] + r[2], r[1] + r[2]];
      const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, lvl = sunk(cx, cy) ? SUNK : GARDEN;
      switch (g.k) {
        case 'lawn': box(x0, x1, y0, y1, GARDEN, GARDEN + 0.012, M.grass, P, {cast: false}); break;
        case 'deck': box(x0, x1, y0, y1, GARDEN, -0.015, M.deck, P, {cast: false}); break;
        case 'pergola': pergola(x0, x1, y0, y1); break;
        case 'canopy': box(x0, x1, y0, y1, 2.45, 2.6, M.plaster, P); break;
        case 'outkitchen': {   // the taboon: a stone base with the oven's dome at its far end
          box(x0, x1, y0, y1, GARDEN, 0.85, M.stone, P);
          box(x0 - 0.03, x1 + 0.03, y0 - 0.03, y1 + 0.03, 0.85, 0.9, M.coping, P);
          const dy = y1 - 0.45;
          ball(cx, dy, 0.9, 0.36, M.terracotta, P, {half: true});
          cyl(cx, dy, 1.1, 1.55, 0.05, M.terracotta, P);
          break;
        }
        case 'service':
          if (g.label === 'גז') {
            box(x0, x1, y0, y1, GARDEN, GARDEN + 0.06, M.concrete, P, {cast: false});
            for (const d of [-0.2, 0.2]) { cyl(cx + d, cy, GARDEN + 0.06, GARDEN + 1.25, 0.17, M.gas, P); ball(cx + d, cy, GARDEN + 1.25, 0.17, M.gas, P, {half: true}); }
          } else {
            box(x0, x1, y0, y1, GARDEN, GARDEN + 0.03, M.gravel, P, {cast: false});
            drier(cx, cy + 0.1);
          }
          break;
        case 'hedge': box(x0, x1, y0, y1, GARDEN, GARDEN + (y0 < 6 ? 1.2 : 1.7), M.leaf, P); break;
        case 'beds': beds(x0, x1, y0, y1); break;
        case 'tree': tree(r[0], r[1], r[2]); break;
        case 'steps': {
          const n = g.n || 4, up = g.up || '+y', rise = (0 - SUNK) / n;
          for (let i = 0; i < n; i++) {
            const z = SUNK + rise * (i + 1);
            if (up === '+y') box(x0, x1, y0 + i * (y1 - y0) / n, y1, SUNK - 0.2, z, M.paverWarm, P);
            else if (up === '-y') box(x0, x1, y0, y1 - i * (y1 - y0) / n, SUNK - 0.2, z, M.paverWarm, P);
            else if (up === '+x') box(x0 + i * (x1 - x0) / n, x1, y0, y1, SUNK - 0.2, z, M.paverWarm, P);
            else box(x0, x1 - i * (x1 - x0) / n, y0, y1, SUNK - 0.2, z, M.paverWarm, P);
          }
          break;
        }
        case 'paving': {
          const landing = !sunk(cx, cy) && Math.abs(y1 - BY0) < 0.01;   // the landing at the front door, at the floor's level
          box(x0, x1, y0, y1, landing ? GARDEN : lvl - 0.05, landing ? 0 : lvl + 0.005, M.paverWarm, P, {cast: false});
          break;
        }
        case 'wall': box(x0, x1, y0, y1, GARDEN, GARDEN + 0.6, M.stone, P); break;
        case 'column': box(x0, x1, y0, y1, GARDEN, CEIL, M.concrete, P); break;   // the entry pergola: concrete
        case 'beam': box(x0, x1, y0, y1, CEIL - 0.3, CEIL, M.concrete, P); break;
        case 'stair': stair(g); break;
        default: break;
      }
      if (g.label) {
        const [lx, ly] = g.at || [cx, cy], z = g.k === 'pergola' ? 3.3 : g.k === 'service' && g.label !== 'גז' ? 2.3 : 1.9;
        label(g.label, lx, ly, z, 0.3);
      }
    }
    function stair(g) {   // the stair to the roof: treads, the landing, and the rails 0.9 m over the treads
      const P = G.site;
      for (const [x0, y0, x1, y1, z] of g.steps3d || []) {
        const landing = x1 - x0 > 0.5 && y1 - y0 > 0.5;
        box(x0, x1, y0, y1, z - (landing ? 0.15 : 0.05), z, landing ? M.concrete : M.oak, P);
      }
      for (const line of g.rails3d || []) {
        line.forEach((q, i) => {
          rod([q[0], q[1], q[2] - 0.9], q, 0.018, M.frame, P);   // a post
          if (i) rod(line[i - 1], q, 0.022, M.frame, P);
        });
      }
    }
    function pergola(x0, x1, y0, y1) {
      const P = G.site, m = M.pergola, z = 2.62, post = 0.12;
      const n = Math.max(2, Math.round((x1 - x0) / 3));
      for (let i = 0; i <= n; i++) {
        const x = Math.min(x1 - post, Math.max(x0, x0 + i * (x1 - x0) / n - post / 2));
        box(x, x + post, y1 - post, y1, -0.015, z, m, P);
      }
      box(x0, x1, y1 - 0.14, y1 + 0.02, z, z + 0.2, m, P);                 // the beam at the far end
      box(x0, x1, y0, y0 + 0.08, z, z + 0.2, m, P);                        // the ledger on the house wall
      for (const x of [x0, x1 - 0.08]) box(x, x + 0.08, y0, y1, z, z + 0.2, m, P);
      const k = Math.max(2, Math.round((x1 - x0) / 0.55));
      for (let i = 1; i < k; i++) { const x = x0 + i * (x1 - x0) / k; box(x - 0.025, x + 0.025, y0, y1 + 0.1, z + 0.2, z + 0.35, m, P); }
    }
    function drier(x, y) {   // a rotary drier with a few clothes
      const P = G.site, z = GARDEN + 1.72, r = rng(61);
      cyl(x, y, GARDEN, GARDEN + 1.78, 0.025, M.chrome, P);
      for (let k = 0; k < 4; k++) {
        const a = k * Math.PI / 2 + 0.3, ex = Math.cos(a), ey = Math.sin(a);
        rod([x, y, z + 0.04], [x + ex * 0.95, y + ey * 0.95, z], 0.012, M.chrome, P);
        if (k % 2 === 0) {
          const cx = x + ex * 0.55, cy = y + ey * 0.55, h = 0.5, w = 0.4;
          const m = mat(pick(r, CLOTHES), {roughness: 1, side: T.DoubleSide});
          const geo = new T.PlaneGeometry(w, h), cl = new T.Mesh(geo, m);
          cl.position.set(cx, z - h / 2, cy); cl.rotation.y = -a; cl.castShadow = true;
          P.add(cl);
        }
      }
      for (const d of [0.35, 0.6, 0.85]) {   // the lines between the arms
        for (let k = 0; k < 4; k++) {
          const a = k * Math.PI / 2 + 0.3, b = a + Math.PI / 2;
          rod([x + Math.cos(a) * d, y + Math.sin(a) * d, z], [x + Math.cos(b) * d, y + Math.sin(b) * d, z], 0.003, M.white, P, {cast: false, seg: 4});
        }
      }
    }
    function beds(x0, x1, y0, y1) {   // a raised bed, the plants in four rows
      const P = G.site, t = 0.05, top = GARDEN + 0.4;
      for (const [a0, a1, b0, b1] of [[x0, x1, y0, y0 + t], [x0, x1, y1 - t, y1], [x0, x0 + t, y0, y1], [x1 - t, x1, y0, y1]]) box(a0, a1, b0, b1, GARDEN, top, M.oak, P);
      box(x0 + t, x1 - t, y0 + t, y1 - t, GARDEN, top - 0.05, M.soil, P, {cast: false});
      const r = rng(71), rows = 4;
      for (let i = 0; i < rows; i++) {
        const y = y0 + (i + 0.5) * (y1 - y0) / rows;
        for (let x = x0 + 0.25; x < x1 - 0.2; x += 0.32 + r() * 0.12) {
          const g = mat(pick(r, ['#5d8f3e', '#6fa04a', '#4c7a36', '#87ad57']), {roughness: 0.9, flatShading: true});
          ball(x, y, top - 0.02, 0.1 + r() * 0.08, g, P, {ico: true, detail: 0, sz: 0.8 + r() * 0.8});
          if (i === 1 && r() < 0.5) ball(x + 0.06, y + 0.05, top + 0.1, 0.035, mat('#d0402d'), P, {cast: false});
        }
      }
    }
    function tree(x, y, r) {
      const P = G.site, h = 2.0 + r * 0.6;
      cyl(x, y, GARDEN, GARDEN + h, 0.11, M.bark, P, {rTop: 0.08});
      const rr = rng(Math.round(x * 31 + y * 7)), greens = ['#5f8f3f', '#6c9c48', '#527f37', '#77a552'];
      for (let i = 0; i < 6; i++) {
        const a = rr() * 6.28, d = r * 0.45 * rr();
        ball(x + Math.cos(a) * d, y + Math.sin(a) * d, GARDEN + h + r * 0.5 + rr() * r * 0.6, r * (0.55 + rr() * 0.3),
             mat(pick(rr, greens), {roughness: 0.9, flatShading: true}), P, {ico: true, detail: 1});
      }
    }
    function neighbors() {
      const N = G.neighbors, h = 6.4;
      const add = (x0, x1, y0, y1, z0, lx, text) => {   // lx: the label stays near our plot, inside the views
        const mesh = box(x0, x1, y0, y1, z0, z0 + h, M.neighbor, N, {cast: false, receive: false});
        mesh.renderOrder = 4;
        const e = new T.LineSegments(new T.EdgesGeometry(mesh.geometry), new T.LineBasicMaterial({color: 0x6b6a65, transparent: true, opacity: 0.6}));
        e.position.copy(mesh.position); N.add(e);
        label(text, lx, (y0 + y1) / 2, z0 + h + 0.8, 0.34, G.nlabels, '#55534d');
      };
      const NL = D.nlabels || ['השותפים\nהנחה: שתי קומות', 'השכנים\nהנחה: שתי קומות'];
      add(-(BX1 - BX0), 0, BY0, BY1, 0, -3, NL[0]);
      add(D.plot[0] + 3, D.plot[0] + 3 + (BX1 - BX0), BY0, BY1, -0.5, D.plot[0] + 5, NL[1]);
    }

    // ---------- the sun ----------
    const RAD = Math.PI / 180, OBL = RAD * 23.4397;
    function sunAt(date) {   // azimuth from the south, positive to the west; altitude above the horizon (radians)
      const d = date.valueOf() / 864e5 - 0.5 + 2440588 - 2451545;
      const Ma = RAD * (357.5291 + 0.98560028 * d);
      const L = Ma + RAD * (1.9148 * Math.sin(Ma) + 0.02 * Math.sin(2 * Ma) + 0.0003 * Math.sin(3 * Ma)) + RAD * 102.9372 + Math.PI;
      const dec = Math.asin(Math.sin(OBL) * Math.sin(L)), ra = Math.atan2(Math.sin(L) * Math.cos(OBL), Math.cos(L));
      const H = RAD * (280.16 + 360.9856235 * d) + RAD * LNG - ra, phi = RAD * LAT;
      return {az: Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(phi) - Math.tan(dec) * Math.cos(phi)),
              alt: Math.asin(Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H))};
    }
    const clock = (s, h) => new Date(Date.UTC(2026, SEASON[s].m, SEASON[s].d, 0, 0) + (h - SEASON[s].tz) * 36e5);
    const hhmm = h => `${String(Math.floor(h)).padStart(2, '0')}:${String(Math.round((h % 1) * 60)).padStart(2, '0')}`;
    function daylight(s) {
      let rise = null, set = null;
      for (let h = 3; h <= 22; h += 1 / 60) {
        const up = sunAt(clock(s, h)).alt > -0.833 * RAD;
        if (up && rise === null) rise = h;
        if (up) set = h;
      }
      return [rise, set];
    }
    function sun() {
      const p = sunAt(clock(state.season, state.hour));
      const az = ((p.az / RAD + 180) % 360 + 360) % 360, alt = p.alt / RAD;   // from the north, clockwise
      const th = (az - UP_AZ) * RAD, ch = Math.cos(p.alt);
      const v = new T.Vector3(ch * Math.sin(th), Math.sin(p.alt), -ch * Math.cos(th));
      const c = new T.Vector3(8.5, 0, 12);
      sunLight.position.copy(v).multiplyScalar(70).add(c); sunLight.target.position.copy(c);
      sunLight.intensity = alt > 0 ? 0.3 + 0.75 * Math.sin(p.alt) : 0;
      main.querySelector('.sunread').textContent = alt > 0
        ? `${SEASON[state.season].name}, ${hhmm(state.hour)}: השמש ב${DIRS[Math.round(az / 45) % 8]}, ${Math.round(alt)}° מעל האופק`
        : `${SEASON[state.season].name}, ${hhmm(state.hour)}: השמש מתחת לאופק`;
      render();
    }
    function setSeason(s) {
      state.season = s;
      main.querySelectorAll('[data-season]').forEach(b => b.setAttribute('aria-pressed', b.dataset.season === s));
      const [rise, set] = daylight(s), input = main.querySelector('.hour');
      input.min = Math.ceil(rise * 4) / 4; input.max = Math.floor(set * 4) / 4;
      state.hour = Math.min(Math.max(state.hour, +input.min), +input.max);
      input.value = state.hour;
      sun();
    }

    // ---------- views and modes ----------
    function setRoof(mode) {
      state.roof = mode;
      main.querySelectorAll('[data-roof]').forEach(b => b.setAttribute('aria-pressed', b.dataset.roof === mode));
      G.roof.visible = mode !== 'off';
      G.roof.traverse(o => {
        if (!o.isMesh) return;
        if (!o.userData.mat) o.userData.mat = o.material;
        o.material = mode === 'shade' ? M.ghost : o.userData.mat;
      });
      G.pendants.visible = mode === 'on';
      G.labels.visible = state.labels && mode !== 'on';
      render();
    }
    function setView(name) {
      const v = VIEWS[name];
      state.view = name;
      main.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', b.dataset.view === name));
      // a screen narrower than the view was framed for (a phone held upright): step back outside, see wider inside
      const a = (stage.clientWidth || 16) / (stage.clientHeight || 10), more = Math.min(Math.max((v.fit || 1.3) / a, 1), 2.2);
      camera.fov = v.dir ? Math.min(Math.atan(Math.tan(v.fov * Math.PI / 360) * Math.sqrt(more)) * 360 / Math.PI, 90) : v.fov;
      camera.updateProjectionMatrix();
      camera.position.set(...v.pos);
      if (v.dir) {   // inside: look around from where you stand
        const d = new T.Vector3(...v.dir).normalize();
        controls.target.copy(camera.position).addScaledVector(d, 0.6);
        controls.minDistance = 0.05; controls.maxDistance = 6;
      } else {
        controls.target.set(...v.tgt);
        camera.position.sub(controls.target).multiplyScalar(more ** 0.85).add(controls.target);
        controls.minDistance = 0.5; controls.maxDistance = 140;
      }
      camera.lookAt(controls.target);
      controls.update();
      fitLabels();
      setRoof(v.roof);
    }
    let pending = false;
    function render() {
      if (!renderer || pending) return;
      pending = true;
      requestAnimationFrame(() => {
        pending = false;
        // inside, the light that bounces off the floor and the walls: without it the white walls look grey
        const p = camera.position, inside = state.roof === 'on' && p.y < CEIL && p.x > BX0 && p.x < BX1 && p.z > BY0 && p.z < BY1;
        fill.intensity = inside ? 0.24 : 0.1; bounce.intensity = inside ? 0.3 : 0;
        M.ceiling.emissive.setHex(inside ? 0x4a4844 : 0x77746d);
        renderer.render(scene, camera);
        document.documentElement.dataset.ready = '1';
      });
    }
    function resize() {
      const w = stage.clientWidth, h = stage.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      camera.aspect = w / h; camera.updateProjectionMatrix();
      fitLabels();
      render();
    }

    function build() {
      renderer = new T.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: true});
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.outputEncoding = T.sRGBEncoding;
      renderer.toneMapping = T.NoToneMapping;
      renderer.shadowMap.enabled = true; renderer.shadowMap.type = T.PCFSoftShadowMap;
      scene = new T.Scene();
      scene.background = sky();
      scene.fog = new T.Fog(0xe3eaee, 75, 190);
      camera = new T.PerspectiveCamera(45, 1, 0.05, 500);
      controls = new T.OrbitControls(camera, canvas);
      controls.screenSpacePanning = true; controls.maxPolarAngle = Math.PI * 0.495;
      controls.addEventListener('change', render);
      M = materials();
      for (const k of ['house', 'roof', 'pendants', 'labels', 'site', 'neighbors']) { G[k] = new T.Group(); scene.add(G[k]); }
      G.nlabels = new T.Group(); G.labels.add(G.nlabels);   // the neighbors' labels: hidden with the labels or the neighbors
      // inside the house (render): more fill, and a soft light from the garden side that tells the walls apart
      fill = new T.AmbientLight(0xffffff, 0.1);
      bounce = new T.DirectionalLight(0xfff6ea, 0); bounce.position.set(0.6, 1, 1);
      scene.add(new T.HemisphereLight(0xe4eef8, 0x9d917a, 0.5), fill, bounce);
      sunLight = new T.DirectionalLight(0xfff1dc, 1.0);
      sunLight.castShadow = true;
      const big = Math.min(window.innerWidth, window.innerHeight) > 700;
      sunLight.shadow.mapSize.set(big ? 4096 : 2048, big ? 4096 : 2048);
      Object.assign(sunLight.shadow.camera, {left: -19, right: 19, top: 19, bottom: -19, near: 1, far: 160});
      sunLight.shadow.bias = -0.0004; sunLight.shadow.normalBias = 0.025;
      scene.add(sunLight, sunLight.target);

      house();
      blockers();
      for (const f of D.furniture) furnish(f);
      for (const r of D.rugs || [[10.05, 11.75, 12.25, 13.8]]) rug(r, PAL.public.rug);   // samples beyond the plan
      for (const q of D.plants || [[12.7, 14.15, 0.2, 1.35]]) plant(...q);
      for (const l of D.labels) label(l.text, l.x, l.y, 3.15, 0.3);
      for (const l of D.glabels) label(l.text, l.x, l.y, l.z, 0.3);
      roof();
      site();
      neighbors();
    }

    function wire() {
      main.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => setView(b.dataset.view)));
      main.querySelectorAll('[data-roof]').forEach(b => b.addEventListener('click', () => setRoof(b.dataset.roof)));
      main.querySelectorAll('[data-season]').forEach(b => b.addEventListener('click', () => setSeason(b.dataset.season)));
      main.querySelector('.hour').addEventListener('input', e => { state.hour = +e.target.value; sun(); });
      main.querySelector('.labels').addEventListener('change', e => { state.labels = e.target.checked; setRoof(state.roof); });
      main.querySelector('.neighbors').addEventListener('change', e => {
        state.neighbors = e.target.checked; G.neighbors.visible = G.nlabels.visible = e.target.checked; render();
      });
      main.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => {   // the + and − buttons
        const k = b.dataset.zoom === 'in' ? 0.8 : 1.25, v = VIEWS[state.view];
        if (v && v.dir) {   // inside: a narrower or a wider lens
          camera.fov = Math.min(Math.max(camera.fov * k, 20), 90);
          camera.updateProjectionMatrix(); fitLabels();
        } else {
          camera.position.sub(controls.target).multiplyScalar(k).add(controls.target);
          controls.update();
        }
        render();
      }));
      if (opts.ctrlWheel)   // the wheel scrolls the page; with Ctrl, or a pinch on a touchpad, it zooms the model
        stage.addEventListener('wheel', e => { if (!e.ctrlKey) e.stopPropagation(); }, {capture: true});
      new ResizeObserver(resize).observe(stage);
    }

    function start() {
      const q = new URLSearchParams(opts.hash ? location.hash.slice(1) : '');   // #view=garden&roof=on&season=summer&hour=9 (for links and pictures)
      if (q.get('shot')) document.body.classList.add('shot');   // only the model, for the pictures
      const cam = (q.get('cam') || '').split(',').map(Number);   // cam=x,y,z,tx,ty,tz in plan coordinates (x, y, height)
      if (cam.length === 6 && cam.every(Number.isFinite)) VIEWS.custom = {pos: [cam[0], cam[2], cam[1]], tgt: [cam[3], cam[5], cam[4]], fov: +q.get('fov') || 50, roof: 'off'};
      if (q.get('hour')) state.hour = +q.get('hour');
      if (q.get('labels') === '0') { state.labels = false; main.querySelector('.labels').checked = false; }
      if (q.get('nb') === '0') { state.neighbors = false; main.querySelector('.neighbors').checked = false; G.neighbors.visible = G.nlabels.visible = false; }
      setSeason(SEASON[q.get('season')] ? q.get('season') : 'winter');
      setView(VIEWS.custom ? 'custom' : VIEWS[q.get('view')] ? q.get('view') : 'top');
      if (['on', 'off', 'shade'].includes(q.get('roof'))) setRoof(q.get('roof'));
      resize();
    }

    if (!document.createElement('canvas').getContext('webgl')) {
      msg.textContent = 'הדפדפן הזה לא מציג תלת-ממד (WebGL).';
      return;
    }
    loadLibs().then(() => {
      T = window.THREE;
      build();
      wire();
      start();
      msg.remove();
    }).catch(e => {
      msg.textContent = 'לא הצלחתי לטעון את ספריית התלת-ממד (three.js). צריך חיבור לאינטרנט.';
      console.error(e);
    });
  }

  window.House3D = {mount};
  if (typeof HOUSE !== 'undefined' && document.getElementById('stage')) mount(document.querySelector('main'), HOUSE, {hash: true});
})();
