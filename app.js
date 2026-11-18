// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
// Interfaz de la demo: dos péndulos dobles separados por delta, divergencia a la vista.
(function () {
  'use strict';

  var P = window.Pendulum;
  var DT = 0.001;          // paso de integración (s)
  var SAMPLE_EVERY = 50;   // pasos entre muestras de la gráfica (0,05 s)
  var MAX_FRAME = 0.1;     // tope de tiempo real por fotograma (s)
  var TRAIL = 500;         // puntos de estela
  var MAX_HIST = 4000;     // muestras máximas (200 s)
  var PRESETS = { chaotic: [2.0, 2.5], regular: [0.5, 0.6] };

  function $(id) { return document.getElementById(id); }
  var scene = $('scene'), plot = $('plot');
  var sctx = scene.getContext('2d'), pctx = plot.getContext('2d');

  var S = {
    a: null, b: null, n: 0, acc: 0, last: null,
    playing: true, speed: 1, delta: 1e-6, preset: 'chaotic',
    trailA: [], trailB: [], hist: []
  };

  function wrap(d) { return d - 2 * Math.PI * Math.round(d / (2 * Math.PI)); }
  function separation() {
    return Math.hypot(wrap(S.a[0] - S.b[0]), wrap(S.a[1] - S.b[1]));
  }
  function fmt(v, d) { return v.toFixed(d).replace('.', ','); }
  function fmtExp(v) { return v.toExponential(2).replace('.', ','); }

  function pushTrails() {
    S.trailA.push([Math.sin(S.a[0]) + Math.sin(S.a[1]), Math.cos(S.a[0]) + Math.cos(S.a[1])]);
    S.trailB.push([Math.sin(S.b[0]) + Math.sin(S.b[1]), Math.cos(S.b[0]) + Math.cos(S.b[1])]);
    if (S.trailA.length > TRAIL) { S.trailA.shift(); S.trailB.shift(); }
  }

  function reset() {
    var p = PRESETS[S.preset];
    S.a = [p[0], p[1], 0, 0];
    S.b = [p[0] + S.delta, p[1], 0, 0];
    S.n = 0; S.acc = 0; S.last = null;
    S.trailA = []; S.trailB = [];
    S.hist = [[0, separation()]];
    pushTrails();
  }

  function advance(dtReal) {
    S.acc += Math.min(dtReal, MAX_FRAME) * S.speed;
    while (S.acc >= DT) {
      S.a = P.step(S.a, DT);
      S.b = P.step(S.b, DT);
      S.n += 1;
      S.acc -= DT;
      if (S.n % SAMPLE_EVERY === 0 && S.hist.length < MAX_HIST) {
        S.hist.push([S.n * DT, separation()]);
      }
    }
    pushTrails();
  }

  function colors() {
    var cs = getComputedStyle(document.documentElement);
    var g = function (k) { return cs.getPropertyValue(k).trim(); };
    return { fg: g('--fg'), muted: g('--muted'), grid: g('--grid'), a: g('--a'), b: g('--b') };
  }

  function fit(canvas, ctx) {
    var r = canvas.getBoundingClientRect();
    var dpr = window.devicePixelRatio || 1;
    var w = Math.max(1, Math.round(r.width * dpr)), h = Math.max(1, Math.round(r.height * dpr));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { w: r.width, h: r.height };
  }

  function drawScene(c) {
    var d = fit(scene, sctx), ctx = sctx;
    ctx.clearRect(0, 0, d.w, d.h);
    var px = d.w / 2, py = d.h * 0.38;
    var s = Math.min((d.w / 2) * 0.9 / 2, d.h * 0.62 * 0.9 / 2);
    function trail(tr, color) {
      ctx.strokeStyle = color; ctx.lineWidth = 1.5;
      for (var i = 1; i < tr.length; i++) {
        ctx.globalAlpha = (i / tr.length) * 0.7;
        ctx.beginPath();
        ctx.moveTo(px + s * tr[i - 1][0], py + s * tr[i - 1][1]);
        ctx.lineTo(px + s * tr[i][0], py + s * tr[i][1]);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }
    function pendulum(y, color) {
      var x1 = px + s * Math.sin(y[0]), y1 = py + s * Math.cos(y[0]);
      var x2 = x1 + s * Math.sin(y[1]), y2 = y1 + s * Math.cos(y[1]);
      ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      ctx.beginPath(); ctx.arc(x1, y1, 5, 0, 2 * Math.PI); ctx.fill();
      ctx.beginPath(); ctx.arc(x2, y2, 6, 0, 2 * Math.PI); ctx.fill();
    }
    trail(S.trailA, c.a); trail(S.trailB, c.b);
    ctx.globalAlpha = 0.9; pendulum(S.a, c.a);
    ctx.globalAlpha = 0.9; pendulum(S.b, c.b);
    ctx.globalAlpha = 1;
    ctx.fillStyle = c.fg; ctx.beginPath(); ctx.arc(px, py, 3, 0, 2 * Math.PI); ctx.fill();
  }

  function drawPlot(c) {
    var d = fit(plot, pctx), ctx = pctx;
    ctx.clearRect(0, 0, d.w, d.h);
    var l = 52, r = 10, t = 10, b = 26;
    var pw = d.w - l - r, ph = d.h - t - b;
    var yMin = -13, yMax = 1;
    var tNow = S.n * DT;
    var xMax = Math.max(30, Math.ceil(tNow / 10) * 10);
    function X(v) { return l + (v / xMax) * pw; }
    function Y(e) { return t + (1 - (e - yMin) / (yMax - yMin)) * ph; }
    ctx.font = '11px system-ui, sans-serif';
    ctx.strokeStyle = c.grid; ctx.fillStyle = c.muted; ctx.lineWidth = 1;
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    for (var e = -12; e <= 0; e += 2) {
      ctx.beginPath(); ctx.moveTo(l, Y(e)); ctx.lineTo(l + pw, Y(e)); ctx.stroke();
      ctx.fillText('1e' + e, l - 6, Y(e));
    }
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    for (var x = 0; x <= xMax; x += 10) {
      ctx.beginPath(); ctx.moveTo(X(x), t); ctx.lineTo(X(x), t + ph); ctx.stroke();
      ctx.fillText(String(x), X(x), t + ph + 6);
    }
    ctx.fillText('t (s)', l + pw / 2, t + ph + 14);
    ctx.strokeStyle = c.b; ctx.lineWidth = 2;
    ctx.beginPath();
    for (var i = 0; i < S.hist.length; i++) {
      var yy = Math.log10(Math.max(S.hist[i][1], 1e-16));
      var xx = X(S.hist[i][0]), py = Y(Math.min(Math.max(yy, yMin), yMax));
      if (i === 0) { ctx.moveTo(xx, py); } else { ctx.lineTo(xx, py); }
    }
    ctx.stroke();
  }

  function readouts() {
    var sep = separation();
    $('r-t').textContent = fmt(S.n * DT, 1) + ' s';
    $('r-sep').textContent = fmtExp(sep);
    $('r-amp').textContent = '×' + (sep / S.delta >= 1000 ? fmtExp(sep / S.delta) : fmt(sep / S.delta, 1));
    $('r-status').textContent = sep < 1e-3 ? 'Indistinguibles' : (sep < 0.1 ? 'Divergiendo' : 'Independientes');
  }

  function frame(ts) {
    if (S.last === null) { S.last = ts; }
    var dtReal = (ts - S.last) / 1000;
    S.last = ts;
    if (S.playing) { advance(dtReal); }
    var c = colors();
    drawScene(c); drawPlot(c); readouts();
    window.requestAnimationFrame(frame);
  }

  $('play').addEventListener('click', function () {
    S.playing = !S.playing;
    $('play').textContent = S.playing ? 'Pausa' : 'Reproducir';
  });
  $('reset').addEventListener('click', reset);
  $('preset').addEventListener('change', function (ev) { S.preset = ev.target.value; reset(); });
  $('delta').addEventListener('change', function (ev) { S.delta = parseFloat(ev.target.value); reset(); });
  $('speed').addEventListener('change', function (ev) { S.speed = parseFloat(ev.target.value); });
  $('theme').addEventListener('click', function () {
    var root = document.documentElement;
    var dark = root.getAttribute('data-theme') === 'dark';
    root.setAttribute('data-theme', dark ? 'light' : 'dark');
    $('theme').textContent = dark ? '☾ Oscuro' : '☀ Claro';
  });

  reset();
  window.requestAnimationFrame(frame);
})();
