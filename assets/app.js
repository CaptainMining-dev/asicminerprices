// asicminerprices.com — shared interactions
(function () {
  var RATE_KEY = 'amp_elec_rate';
  var slider = document.getElementById('elec-rate');
  var rateVal = document.getElementById('rate-val');

  function currentRate() {
    var saved = parseFloat(localStorage.getItem(RATE_KEY));
    if (!isNaN(saved)) return saved < 1 ? saved : saved / 1000; // legacy $ values vs slider milli-units
    return slider ? parseFloat(slider.value) / 1000 : 0.072;
  }

  function fmt(x, dec) {
    if (dec === undefined) dec = 2;
    return (x < 0 ? '-$' : '$') + Math.abs(x).toFixed(dec);
  }

  // ---- live profit recompute (tables with data attributes) ----
  function recompute() {
    var rate = currentRate();
    if (rateVal) rateVal.textContent = '$' + rate.toFixed(3) + '/kWh';
    document.querySelectorAll('tr[data-hr]').forEach(function (tr) {
      var hr = parseFloat(tr.dataset.hr);
      var hp = parseFloat(tr.dataset.hp);       // revenue $ per hashrate unit / day
      var pw = parseFloat(tr.dataset.power);    // watts
      var price = parseFloat(tr.dataset.price);
      var profit = hr * hp - (pw / 1000) * 24 * rate;
      var cell = tr.querySelector('.profit-cell');
      if (cell) {
        cell.innerHTML = '<span class="' + (profit >= 0 ? 'pill-profit' : 'pill-loss') + '">' +
          (profit >= 0 ? '+' : '') + fmt(profit) + '</span>';
        cell.dataset.sort = profit;
      }
      var roi = tr.querySelector('.roi-cell');
      if (roi) {
        roi.textContent = profit > 0 ? Math.round(price / profit) + ' d' : '—';
        roi.dataset.sort = profit > 0 ? price / profit : 1e9;
      }
    });
    // re-sort tbody rows by profit desc if table is in profit-sort mode
    document.querySelectorAll('table.autosort tbody').forEach(function (tb) {
      var rows = Array.from(tb.querySelectorAll('tr'));
      rows.sort(function (a, b) {
        var pa = parseFloat(a.querySelector('.profit-cell').dataset.sort || 0);
        var pb = parseFloat(b.querySelector('.profit-cell').dataset.sort || 0);
        return pb - pa;
      });
      rows.forEach(function (r) { tb.appendChild(r); });
    });
    // dynamic summary cards
    document.querySelectorAll('[data-dyn-profit]').forEach(function (el) {
      var p = parseFloat(el.dataset.hr) * parseFloat(el.dataset.hp) - (parseFloat(el.dataset.power) / 1000) * 24 * rate;
      el.textContent = fmt(p);
      el.style.color = p >= 0 ? 'var(--green)' : 'var(--red)';
    });
    document.querySelectorAll('[data-dyn-roi]').forEach(function (el) {
      var p = parseFloat(el.dataset.hr) * parseFloat(el.dataset.hp) - (parseFloat(el.dataset.power) / 1000) * 24 * rate;
      el.textContent = p > 0 ? 'ROI ' + Math.round(parseFloat(el.dataset.price) / p) + ' days' : 'not profitable at this rate';
    });
    document.querySelectorAll('.dyn-rate').forEach(function (el) {
      el.textContent = '$' + rate.toFixed(3) + '/kWh';
    });
    // bar chart
    document.querySelectorAll('.bars .b i[data-hr]').forEach(function (bar) {
      var hr = parseFloat(bar.dataset.hr), hp = parseFloat(bar.dataset.hp), pw = parseFloat(bar.dataset.power);
      var p = hr * hp - (pw / 1000) * 24 * rate;
      var max = parseFloat(bar.closest('.bars').dataset.max || 1);
      bar.style.height = Math.max(2, (Math.max(0, p) / max) * 100) + '%';
      var lbl = bar.parentElement.querySelector('em');
      if (lbl) lbl.textContent = fmt(p, 0);
    });
  }

  if (slider) {
    var saved = localStorage.getItem(RATE_KEY);
    if (saved) slider.value = saved;
    slider.addEventListener('input', function () {
      localStorage.setItem(RATE_KEY, slider.value);
      recompute();
    });
  }

  // ---- algo filter tabs ----
  document.querySelectorAll('.tabs button[data-algo]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.tabs button').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      var algo = btn.dataset.algo;
      document.querySelectorAll('tr[data-algo]').forEach(function (tr) {
        tr.style.display = (algo === 'all' || tr.dataset.algo === algo) ? '' : 'none';
      });
    });
  });

  // ---- sortable headers ----
  document.querySelectorAll('thead th[data-col]').forEach(function (th) {
    th.addEventListener('click', function () {
      var col = th.dataset.col;
      var tb = th.closest('table').querySelector('tbody');
      var asc = th.dataset.dir === 'asc';
      th.dataset.dir = asc ? 'desc' : 'asc';
      var rows = Array.from(tb.querySelectorAll('tr'));
      rows.sort(function (a, b) {
        var ca = a.querySelector('[data-col-val="' + col + '"]');
        var cb = b.querySelector('[data-col-val="' + col + '"]');
        var va = ca ? parseFloat(ca.dataset.sort !== undefined ? ca.dataset.sort : ca.textContent.replace(/[^0-9.\-]/g, '')) : 0;
        var vb = cb ? parseFloat(cb.dataset.sort !== undefined ? cb.dataset.sort : cb.textContent.replace(/[^0-9.\-]/g, '')) : 0;
        return asc ? va - vb : vb - va;
      });
      rows.forEach(function (r) { tb.appendChild(r); });
    });
  });

  // ---- calculator page ----
  var calcForm = document.getElementById('calc-form');
  if (calcForm && window.MINERS) {
    var sel = document.getElementById('calc-miner');
    window.MINERS.forEach(function (m, i) {
      var o = document.createElement('option');
      o.value = i; o.textContent = m.name + ' — ' + m.hr + ' ' + m.unit;
      sel.appendChild(o);
    });
    function calc() {
      var m = window.MINERS[parseInt(sel.value || 0)];
      var rate = parseFloat(document.getElementById('calc-rate').value || 0.10);
      var fee = parseFloat(document.getElementById('calc-fee').value || 1) / 100;
      var rev = m.hr * m.hp * (1 - fee);
      var cost = (m.power / 1000) * 24 * rate;
      var net = rev - cost;
      document.getElementById('calc-daily').textContent = fmt(net);
      document.getElementById('calc-monthly').textContent = fmt(net * 30.44);
      document.getElementById('calc-yearly').textContent = fmt(net * 365);
      document.getElementById('calc-rev').textContent = fmt(rev);
      document.getElementById('calc-cost').textContent = fmt(cost);
      document.getElementById('calc-be').textContent = '$' + (rev / ((m.power / 1000) * 24)).toFixed(4) + '/kWh';
      document.getElementById('calc-roi').textContent = net > 0 ? Math.round(m.price / net) + ' days' : 'Not profitable at this rate';
      var hero = document.getElementById('calc-daily');
      hero.style.color = net >= 0 ? 'var(--green)' : 'var(--red)';
    }
    calcForm.addEventListener('input', calc);
    calc();
  }

  recompute();
})();
