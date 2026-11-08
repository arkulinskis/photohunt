/* ph-art.js: PhotoHunt's drawings, as SVG. The birthday cake (one candle per treasure, lit when found), the cake
   toppers kids pick as their avatar, the stickers they win, and QR codes (with ph-qrgen.js).
   Python reaches it through client_code/ph.py; custom components (Components/Cake, Topper, Sticker, QrCode) call
   PH.cake(el, opts) etc. and redraw when a property changes. Everything is drawn from literal colours so it looks the
   same in light and dark mode (the cake sits on its own plate). */
(function () {
  'use strict';
  var PH = window.PH = window.PH || {};
  var INK = '#3A1E2A';

  PH.FLAVOURS = {
    strawberry: { label: 'Strawberry', frost: '#FF9DBD', drip: '#F0679A', sponge: '#FFE3BF', sponge2: '#F5C88E', fill: '#FF5C8A' },
    chocolate:  { label: 'Chocolate',  frost: '#8A5A43', drip: '#64392A', sponge: '#D39A68', sponge2: '#B27446', fill: '#F6D7AE' },
    vanilla:    { label: 'Vanilla',    frost: '#FFF4D6', drip: '#F2DB9E', sponge: '#F8D9A0', sponge2: '#E8BE7A', fill: '#FF8FB3' },
    mint:       { label: 'Mint choc',  frost: '#A9EED3', drip: '#68D1AA', sponge: '#7E4E38', sponge2: '#5F3826', fill: '#FFFFFF' },
    blueberry:  { label: 'Blueberry',  frost: '#B6CBFF', drip: '#7F9DF4', sponge: '#FFE8C4', sponge2: '#F1CD95', fill: '#6F82E2' },
    lemon:      { label: 'Lemon',      frost: '#FFE57E', drip: '#F3C631', sponge: '#FFF2CF', sponge2: '#F4DA98', fill: '#FFFFFF' }
  };
  PH.COLOURS = { pink: '#FF6FA3', mint: '#22B07F', blue: '#4A7BF0', lemon: '#F5B700', orange: '#FF8A3D', berry: '#C2255C' };
  var SPRINKLES = ['#FF6FA3', '#22B07F', '#4A7BF0', '#F5B700', '#FF8A3D', '#FFFFFF'];

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function rnd(seed) { var x = seed || 1; return function () { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; }
  function mix(hex, other, t) {
    var a = parseInt(hex.slice(1), 16), b = parseInt(other.slice(1), 16);
    var r = Math.round(((a >> 16) & 255) * (1 - t) + ((b >> 16) & 255) * t);
    var g = Math.round(((a >> 8) & 255) * (1 - t) + ((b >> 8) & 255) * t);
    var bl = Math.round((a & 255) * (1 - t) + (b & 255) * t);
    return '#' + ((1 << 24) + (r << 16) + (g << 8) + bl).toString(16).slice(1);
  }

  /* ---------------------------------------------------------------- the cake */
  function candle(x, y, h, colour, lit, blown, i) {
    var w = 7, out = '<g class="ph-candle' + (lit ? ' lit' : '') + '" style="--i:' + i + '">';
    out += '<rect x="' + (x - w / 2) + '" y="' + (y - h) + '" width="' + w + '" height="' + h + '" rx="2" fill="' + colour + '" stroke="' + INK + '" stroke-width="1.2"/>';
    for (var s = 0; s < 3; s++) {
      var sy = y - h + 5 + s * (h / 3.2);
      out += '<path d="M' + (x - w / 2 + .6) + ' ' + (sy + 3) + 'L' + (x + w / 2 - .6) + ' ' + sy + '" stroke="#fff" stroke-width="1.6" opacity=".8"/>';
    }
    out += '<path d="M' + x + ' ' + (y - h) + 'v-4" stroke="' + INK + '" stroke-width="1.3" stroke-linecap="round"/>';
    if (lit) {
      out += '<g class="ph-flame"><path d="M' + x + ' ' + (y - h - 19) + 'c4 5 6 8 6 11a6 6 0 0 1-12 0c0-3 2-6 6-11z" fill="#FFC234" stroke="#E07B00" stroke-width="1"/>' +
             '<path d="M' + x + ' ' + (y - h - 12) + 'c2 3 3 4 3 6a3 3 0 0 1-6 0c0-2 1-3 3-6z" fill="#FFF3B0"/></g>';
    } else if (blown) {
      out += '<path class="ph-smoke" d="M' + x + ' ' + (y - h - 5) + 'c-4-5 4-8 0-13s4-8 0-12" fill="none" stroke="#B9A6AE" stroke-width="2" stroke-linecap="round"/>';
    }
    return out + '</g>';
  }

  PH.cakeSvg = function (o) {
    o = o || {};
    var f = PH.FLAVOURS[o.flavour] || PH.FLAVOURS.strawberry;
    var total = Math.max(0, Math.min(30, o.total | 0)), lit = Math.max(0, Math.min(total, o.lit | 0));
    var r = rnd(7 + total * 13 + (o.flavour || '').length);
    var cx = 120, top = 104, rx = 92, ry = 20, bottom = 168;
    var s = '<svg viewBox="0 0 240 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="' +
            esc(o.label || ('Birthday cake with ' + lit + ' of ' + total + ' candles lit')) + '">';
    // plate
    s += '<ellipse cx="120" cy="186" rx="112" ry="17" fill="#FFFFFF" stroke="' + INK + '" stroke-width="2"/>';
    s += '<ellipse cx="120" cy="183" rx="96" ry="11" fill="#F3E6EA"/>';
    // sponge body with a filling stripe
    s += '<path d="M' + (cx - rx) + ' ' + top + 'V' + bottom + 'a' + rx + ' ' + ry + ' 0 0 0 ' + (2 * rx) + ' 0V' + top + 'z" fill="' + f.sponge + '" stroke="' + INK + '" stroke-width="2"/>';
    s += '<path d="M' + (cx - rx) + ' ' + (top + 34) + 'a' + rx + ' ' + ry + ' 0 0 0 ' + (2 * rx) + ' 0v9a' + rx + ' ' + ry + ' 0 0 1 -' + (2 * rx) + ' 0z" fill="' + f.fill + '" opacity=".95"/>';
    s += '<path d="M' + (cx - rx) + ' ' + (bottom - 10) + 'a' + rx + ' ' + ry + ' 0 0 0 ' + (2 * rx) + ' 0V' + bottom + 'a' + rx + ' ' + ry + ' 0 0 1 -' + (2 * rx) + ' 0z" fill="' + f.sponge2 + '" opacity=".7"/>';
    // frosting top with drips
    var d = 'M' + (cx - rx) + ' ' + top;
    var drips = 9;
    for (var i = 0; i < drips; i++) {
      var x0 = cx - rx + (2 * rx) * i / drips, x1 = cx - rx + (2 * rx) * (i + 1) / drips;
      var t0 = (i + .5) / drips * Math.PI, yy = top + Math.sin(t0) * ry;
      var len = 10 + Math.round(r() * 18);
      d += 'L' + x0.toFixed(1) + ' ' + (top + Math.sin(i / drips * Math.PI) * ry).toFixed(1);
      d += 'C' + (x0 + 2).toFixed(1) + ' ' + (yy + len).toFixed(1) + ' ' + (x1 - 2).toFixed(1) + ' ' + (yy + len).toFixed(1) + ' ' + x1.toFixed(1) + ' ' + (top + Math.sin((i + 1) / drips * Math.PI) * ry).toFixed(1);
    }
    d += 'L' + (cx + rx) + ' ' + top + 'A' + rx + ' ' + ry + ' 0 0 0 ' + (cx - rx) + ' ' + top + 'z';
    s += '<path d="' + d + '" fill="' + f.drip + '" stroke="' + INK + '" stroke-width="2" stroke-linejoin="round"/>';
    s += '<ellipse cx="' + cx + '" cy="' + top + '" rx="' + rx + '" ry="' + ry + '" fill="' + f.frost + '" stroke="' + INK + '" stroke-width="2"/>';
    // sprinkles on the frosting
    for (var k = 0; k < 26; k++) {
      var a = r() * Math.PI * 2, rr = Math.sqrt(r()) * .82;
      var sx = cx + Math.cos(a) * rx * rr, sy = top + Math.sin(a) * ry * rr, rot = Math.round(r() * 180);
      s += '<rect x="' + (sx - 3.5).toFixed(1) + '" y="' + (sy - 1.2).toFixed(1) + '" width="7" height="2.4" rx="1.2" fill="' + SPRINKLES[k % SPRINKLES.length] +
           '" transform="rotate(' + rot + ' ' + sx.toFixed(1) + ' ' + sy.toFixed(1) + ')"/>';
    }
    // candles: back row first, then the front row
    var rows = total > 8 ? (total > 18 ? 3 : 2) : 1, placed = [], per = Math.ceil(total / rows);
    for (var row = 0; row < rows; row++) {
      var n = Math.min(per, total - row * per);
      var depth = rows === 1 ? 0.15 : (row / (rows - 1)) * 0.9 - 0.45;  // -0.45 (back) .. 0.45 (front)
      var spanRx = rx * 0.78 * Math.sqrt(1 - depth * depth);
      for (var c = 0; c < n; c++) {
        var tx = n === 1 ? 0 : (c / (n - 1)) * 2 - 1;
        placed.push({ x: cx + tx * spanRx, y: top + depth * ry * 1.7 + 4, idx: row * per + c });
      }
    }
    placed.sort(function (p, q) { return p.y - q.y; });
    var h = total > 18 ? 24 : (total > 8 ? 28 : 34);
    placed.forEach(function (p) {
      s += candle(p.x, p.y, h, SPRINKLES[p.idx % 5], p.idx < lit && !o.blown, !!o.blown, p.idx);
    });
    if (!total) {
      s += '<text x="120" y="' + (top + 4) + '" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="' + INK + '">Add treasures for candles</text>';
    }
    return s + '</svg>';
  };

  PH.cake = function (el, o) { if (el) el.innerHTML = PH.cakeSvg(o); };

  /* ---------------------------------------------------------------- toppers (kid avatars) */
  var TOPPERS = {
    star: '<path d="M24 9l4.4 9 9.9 1.4-7.2 7 1.7 9.8L24 31.6l-8.8 4.6 1.7-9.8-7.2-7 9.9-1.4z"/>',
    heart: '<path d="M24 37s-13-7.6-13-17a7 7 0 0 1 13-3.6A7 7 0 0 1 37 20c0 9.4-13 17-13 17z"/>',
    crown: '<path d="M10 33l-2-17 9 7 7-11 7 11 9-7-2 17z"/><rect x="10" y="33" width="28" height="4" rx="1.5"/>',
    rocket: '<path d="M24 7c6 5 8 12 7 21h-14c-1-9 1-16 7-21z"/><path d="M17 26l-5 7h6M31 26l5 7h-6"/><circle cx="24" cy="19" r="3" fill="#fff"/><path d="M21 31h6l-3 7z" fill="#FFC234"/>',
    flower: '<circle cx="24" cy="15" r="6"/><circle cx="33" cy="22" r="6"/><circle cx="29" cy="32" r="6"/><circle cx="19" cy="32" r="6"/><circle cx="15" cy="22" r="6"/><circle cx="24" cy="24" r="5" fill="#FFC234"/>',
    balloon: '<ellipse cx="24" cy="20" rx="10" ry="12"/><path d="M22 32h4l-2 3z"/><path d="M24 35c-3 3 3 5 0 8" fill="none" stroke-width="1.6"/>',
    dino: '<path d="M10 34c0-8 5-13 13-13h3l2-6c3-1 7 1 8 4l-3 1 1 4c4 2 5 6 4 10z"/><path d="M14 25l2-4 3 3M20 21l2-4 3 3" /><circle cx="31" cy="19" r="1.4" fill="' + INK + '"/>',
    moon: '<path d="M30 9a15 15 0 1 0 8 23A12 12 0 0 1 30 9z"/>',
    bolt: '<path d="M27 7L13 27h9l-3 14 15-21h-9z"/>',
    fish: '<path d="M8 24c5-8 16-10 23-3l7-6v18l-7-6c-7 7-18 5-23-3z"/><circle cx="17" cy="22" r="1.6" fill="' + INK + '"/>',
    cat: '<path d="M12 17l2-9 7 6h6l7-6 2 9v10c0 7-6 11-12 11s-12-4-12-11z"/><circle cx="19" cy="24" r="1.6" fill="' + INK + '"/><circle cx="29" cy="24" r="1.6" fill="' + INK + '"/><path d="M22 29l2 1.5 2-1.5" fill="none"/>',
    rainbow: '<path d="M8 32a16 16 0 0 1 32 0h-5a11 11 0 0 0-22 0z"/><path d="M15 32a9 9 0 0 1 18 0h-4a5 5 0 0 0-10 0z" fill="#FFC234"/>'
  };
  PH.TOPPERS = Object.keys(TOPPERS);
  PH.topperSvg = function (o) {
    o = o || {};
    var col = PH.COLOURS[o.colour] || PH.COLOURS.pink, shape = TOPPERS[o.topper] || TOPPERS.star;
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<circle cx="24" cy="24" r="22.5" fill="' + mix(col, '#ffffff', .72) + '" stroke="' + col + '" stroke-width="3"/>' +
      '<g fill="' + col + '" stroke="' + INK + '" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round">' + shape + '</g></svg>';
  };
  PH.topper = function (el, o) { if (el) el.innerHTML = PH.topperSvg(o); };

  /* ---------------------------------------------------------------- stickers */
  var STICKERS = {
    party:  ['#FF6FA3', '<path d="M24 8l9 26H15z" fill="#FFC234"/><path d="M19 22l11 4M17 28l14 4" stroke="#FF6FA3" stroke-width="2.5"/><circle cx="24" cy="8" r="3" fill="#4A7BF0"/>'],
    cake:   ['#F0679A', '<path d="M12 26h24v10H12z" fill="#FFE3BF"/><path d="M12 26c0-4 4-6 12-6s12 2 12 6c-2 3-4 0-6 3-2-3-4 1-6-2-2 3-4-1-6 2-2-3-4 0-6-3z" fill="#FF9DBD"/><rect x="22" y="11" width="4" height="9" rx="1" fill="#4A7BF0"/><path d="M24 4c2 3 3 4 3 5.5a3 3 0 0 1-6 0C21 8 22 7 24 4z" fill="#FFC234"/>'],
    first:  ['#4A7BF0', '<path d="M17 30l-4 12 6-3 3 5 3-11M31 30l4 12-6-3-3 5-3-11" fill="#FF6FA3"/><circle cx="24" cy="21" r="12" fill="#FFC234"/><path d="M22 16l3-2v14" fill="none" stroke="' + INK + '" stroke-width="2.6" stroke-linecap="round"/>'],
    speedy: ['#F5B700', '<path d="M27 6L13 27h9l-3 15 15-21h-9z" fill="#FFF3B0"/>'],
    winner: ['#FF8A3D', '<path d="M15 10h18v8a9 9 0 0 1-18 0z" fill="#FFC234"/><path d="M15 13h-5c0 6 3 8 6 8M33 13h5c0 6-3 8-6 8" fill="none" stroke="#FFC234" stroke-width="2.4"/><rect x="21" y="27" width="6" height="6" fill="#FFC234"/><rect x="16" y="33" width="16" height="5" rx="1.5" fill="#fff"/>'],
    sharp:  ['#22B07F', '<path d="M8 24c4-7 10-10 16-10s12 3 16 10c-4 7-10 10-16 10S12 31 8 24z" fill="#fff"/><circle cx="24" cy="24" r="6" fill="#4A7BF0"/><circle cx="24" cy="24" r="2.5" fill="' + INK + '"/>'],
    voice:  ['#4A7BF0', '<path d="M12 20h6l8-7v22l-8-7h-6z" fill="#fff"/><path d="M30 18c3 3 3 9 0 12M34 14c5 5 5 15 0 20" fill="none" stroke="#FFC234" stroke-width="2.6" stroke-linecap="round"/>'],
    task:   ['#FF8A3D', '<circle cx="24" cy="24" r="13" fill="#FFC234"/><path d="M24 15l2.6 5.4 5.9.8-4.3 4.2 1 5.8L24 28.4l-5.2 2.8 1-5.8-4.3-4.2 5.9-.8z" fill="#fff"/>'],
    bingo:  ['#22B07F', '<rect x="12" y="12" width="24" height="24" rx="3" fill="#fff"/><path d="M20 12v24M28 12v24M12 20h24M12 28h24" stroke="#22B07F" stroke-width="1.5"/><circle cx="16" cy="16" r="2.6" fill="#FF6FA3"/><circle cx="24" cy="24" r="2.6" fill="#FF6FA3"/><circle cx="32" cy="32" r="2.6" fill="#FF6FA3"/><path d="M13 13l22 22" stroke="#C2255C" stroke-width="2.6" stroke-linecap="round"/>'],
    team:   ['#C2255C', '<path d="M24 36s-11-6.5-11-14.5A6 6 0 0 1 24 18a6 6 0 0 1 11 3.5C35 29.5 24 36 24 36z" fill="#FF9DBD"/><circle cx="16" cy="13" r="4" fill="#FFC234"/><circle cx="32" cy="13" r="4" fill="#22B07F"/>']
  };
  PH.stickerSvg = function (o) {
    o = o || {};
    var st = STICKERS[o.id] || STICKERS.party, col = st[0], scallop = '';
    for (var i = 0; i < 16; i++) {
      var a = i / 16 * Math.PI * 2;
      scallop += '<circle cx="' + (24 + Math.cos(a) * 19.5).toFixed(2) + '" cy="' + (24 + Math.sin(a) * 19.5).toFixed(2) + '" r="4.6"/>';
    }
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><g fill="' + col + '">' + scallop +
      '<circle cx="24" cy="24" r="20"/></g><circle cx="24" cy="24" r="16.5" fill="none" stroke="#fff" stroke-width="1.5" stroke-dasharray="2 3" opacity=".8"/>' +
      '<g stroke-linejoin="round">' + st[1] + '</g></svg>';
  };
  PH.sticker = function (el, o) { if (el) el.innerHTML = PH.stickerSvg(o); };

  /* ---------------------------------------------------------------- QR codes (ph-qrgen.js = qrcode-generator, MIT) */
  PH.qrSvg = function (text, dark) {
    if (!window.qrcode) return '';
    var q = window.qrcode(0, 'M');
    q.addData(String(text || ''));
    q.make();
    var n = q.getModuleCount(), pad = 3, d = '';
    for (var y = 0; y < n; y++) for (var x = 0; x < n; x++) if (q.isDark(y, x)) d += 'M' + (x + pad) + ' ' + (y + pad) + 'h1v1h-1z';
    var size = n + pad * 2;
    return '<svg viewBox="0 0 ' + size + ' ' + size + '" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" role="img" aria-label="QR code">' +
      '<rect width="' + size + '" height="' + size + '" fill="#ffffff"/><path d="' + d + '" fill="' + (dark || '#2A0F1A') + '"/></svg>';
  };
  PH.qr = function (el, text, dark) { if (el) el.innerHTML = PH.qrSvg(text, dark); };
})();
