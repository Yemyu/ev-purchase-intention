(function () {
  'use strict';
  var pageLang = (document.documentElement.lang || '').toLowerCase().indexOf('en') === 0 ? 'en' : 'zh';
  var state = { lang: pageLang === 'en' ? 'en' : (localStorage.getItem('ev-report-lang') || 'zh'), data: null };
  var T = window.EV_REPORT_THEME;
  var charts = [];
  var EN = {
    '技术认知 T': 'Technology recognition T', '功能价值 V': 'Function value V',
    '技术认知': 'Technology recognition', '功能价值': 'Function value',
    '驾驶乐趣 M1': 'Driving pleasure M1', '出行效率 M2': 'Travel efficiency M2', '控制变量': 'Controls',
    '驾驶乐趣': 'Driving pleasure', '出行效率': 'Travel efficiency',
    '性别：类别 2': 'Gender: category 2', '驾驶频率：类别 2': 'Driving frequency: category 2',
    '驾驶频率：类别 3': 'Driving frequency: category 3', '驾驶频率：类别 4': 'Driving frequency: category 4',
    '驾驶频率：类别 5': 'Driving frequency: category 5', '学历：类别 2': 'Education: category 2',
    '学历：类别 3': 'Education: category 3', '学历：类别 4': 'Education: category 4',
    '驾龄：类别 2': 'Driving experience: category 2', '驾龄：类别 3': 'Driving experience: category 3',
    '驾龄：类别 4': 'Driving experience: category 4', '驾龄：类别 5': 'Driving experience: category 5',
    '年龄：类别 2': 'Age: category 2', '年龄：类别 3': 'Age: category 3',
    '年龄：类别 4': 'Age: category 4', '年龄：类别 5': 'Age: category 5',
    '收入：类别 2': 'Income: category 2', '收入：类别 3': 'Income: category 3',
    '收入：类别 4': 'Income: category 4',
    '间接关联': 'Indirect association',
    '性别': 'Gender', '年龄': 'Age', '月收入': 'Monthly income', '驾龄': 'Driving experience', '驾驶频率': 'Driving frequency',
    '控制变量 + T/V': 'Controls + T/V', '扩展变量 + M1/M2': 'Extended + M1/M2',
    '多数类基线': 'Majority baseline', '有序 Logit': 'Ordered logit', '随机森林': 'Random forest',
    '是': 'Yes', '否': 'No'
  };
  function qs(sel) { return document.querySelector(sel); }
  function tr(value) { return state.lang === 'en' ? (EN[value] || value) : value; }
  function fmt(value, digits) { return Number(value).toFixed(digits == null ? 2 : digits); }
  function pct(value, digits) { return (Number(value) * 100).toFixed(digits == null ? 1 : digits) + '%'; }
  function pval(value) { return Number(value) < .001 ? '<0.001' : Number(value).toFixed(3); }
  function shapLabel(row) {
    var match = /^control_(gender|age|education|income|driving_exp|driving_freq)_(\d+)$/.exec(row.feature || '');
    if (!match) return tr(row.label);
    var names = { gender: '性别', age: '年龄', education: '学历', income: '收入', driving_exp: '驾龄', driving_freq: '驾驶频率' };
    return tr(names[match[1]] + '：类别 ' + match[2]);
  }
  function setLang(lang) {
    state.lang = lang; localStorage.setItem('ev-report-lang', lang);
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    document.body.classList.remove('lang-zh', 'lang-en'); document.body.classList.add('lang-' + lang);
    var button = qs('#langSwitch'); if (button) button.textContent = lang === 'zh' ? 'English' : '中文';
    charts.forEach(function (chart) { if (chart && chart.resize) chart.resize(); });
    if (state.data) {
      charts.forEach(function (chart) { if (chart && chart.dispose) chart.dispose(); });
      charts = [];
      render(state.data);
    }
  }
  function makeChart(id, option) {
    var node = document.getElementById(id); if (!node || !window.echarts) return null;
    var chart = window.echarts.init(node); chart.setOption(option); charts.push(chart); return chart;
  }
  function commonGrid() { return { left: 48, right: 28, top: 34, bottom: 42, containLabel: true }; }
  function baseOption() { return { animationDuration: 500, textStyle: { fontFamily: '-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif' }, grid: commonGrid(), tooltip: { backgroundColor: 'rgba(43,39,33,.94)', borderWidth: 0, textStyle: { color: '#fff' } } }; }
  function renderMetricCards(d) {
    qs('#metric-n').textContent = d.hero.n;
    qs('#metric-t').textContent = fmt(d.hero.primary_t_or);
    qs('#metric-v').textContent = fmt(d.hero.primary_v_or);
    qs('#metric-qwk').textContent = fmt(d.hero.extended_qwk, 3);
  }
  function renderDirect(d) {
    var rows = d.direct.filter(function (x) { return x.specification === 'primary'; });
    qs('#directTable').innerHTML = rows.map(function (row) {
      return '<tr class="primary"><td><strong>' + tr(row.label) + '</strong><br><span class="badge">primary / controlled</span></td>' +
        '<td>' + fmt(row.odds_ratio) + '</td><td>[' + fmt(row.ci_low) + ', ' + fmt(row.ci_high) + ']</td><td>' + pval(row.p_value) + '</td><td>' + row.n_obs + '</td></tr>';
    }).join('');
    var all = d.direct.filter(function (x) { return x.term === 'T' || x.term === 'V'; });
    makeChart('directChart', Object.assign(baseOption(), {
      yAxis: { type: 'category', data: ['primary / V', 'primary / T'], axisLine: { lineStyle: { color: T.line } }, axisLabel: { color: T.muted } },
      xAxis: { type: 'value', min: 0, max: 5, name: 'OR', nameTextStyle: { color: T.muted }, splitLine: { lineStyle: { color: T.grid } }, axisLabel: { color: T.muted } },
      series: [{ type: 'bar', data: [rows[1].odds_ratio, rows[0].odds_ratio], barWidth: 24, itemStyle: { color: T.primary, borderRadius: [0, 4, 4, 0] }, label: { show: true, position: 'right', color: T.ink, formatter: function (p) { return fmt(p.value); } }, markLine: { symbol: 'none', lineStyle: { color: T.earth, type: 'dashed' }, data: [{ xAxis: 1 }] } }]
    }));
    var specRows = ['primary', 'sensitivity', 'legacy'];
    qs('#specTable').innerHTML = specRows.map(function (spec) {
      var t = all.find(function (x) { return x.specification === spec && x.term === 'T'; });
      var v = all.find(function (x) { return x.specification === spec && x.term === 'V'; });
      return '<tr><td><span class="badge">' + spec + '</span></td><td>' + fmt(t.odds_ratio) + '</td><td>' + fmt(v.odds_ratio) + '</td><td>' + tr(t.converged && v.converged ? '是' : '否') + '</td></tr>';
    }).join('');
  }
  function intervalSeries(rows) {
    return {
      type: 'custom', silent: true,
      data: rows.slice().reverse().map(function (r, i) { return [r.ci_low, r.ci_high, i]; }),
      renderItem: function (params, api) {
        var a = api.coord([api.value(0), api.value(2)]);
        var b = api.coord([api.value(1), api.value(2)]);
        return { type: 'group', children: [
          { type: 'line', shape: { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, style: { stroke: T.secondary, lineWidth: 2 } },
          { type: 'line', shape: { x1: a[0], y1: a[1]-4, x2: a[0], y2: a[1]+4 }, style: { stroke: T.secondary } },
          { type: 'line', shape: { x1: b[0], y1: b[1]-4, x2: b[0], y2: b[1]+4 }, style: { stroke: T.secondary } }
        ] };
      }, encode: { x: [0, 1], y: 2 }
    };
  }
  function renderMediation(d) {
    qs('#mediationTable').innerHTML = d.mediation.map(function (row) {
      return '<tr><td>' + tr(row.x) + ' → ' + tr(row.mediator) + ' → Y</td><td>' + fmt(row.indirect, 3) + '</td><td>[' + fmt(row.ci_low, 3) + ', ' + fmt(row.ci_high, 3) + ']</td><td>' + row.bootstrap_valid + '/' + row.bootstrap_iterations + '</td></tr>';
    }).join('');
    makeChart('mediationChart', Object.assign(baseOption(), {
      grid: { left: 12, right: 26, top: 24, bottom: 48, containLabel: true },
      yAxis: { type: 'category', data: d.mediation.map(function (x) { return tr(x.x) + ' → ' + tr(x.mediator); }).reverse(), axisLabel: { color: T.muted, fontSize: 10, width: 155, overflow: 'break' }, axisLine: { lineStyle: { color: T.line } } },
      xAxis: { type: 'value', name: tr('间接关联'), nameLocation: 'middle', nameGap: 28, splitLine: { lineStyle: { color: T.grid } }, axisLabel: { color: T.muted } },
      series: [intervalSeries(d.mediation), { type: 'scatter', symbolSize: 10, itemStyle: { color: T.secondary }, data: d.mediation.map(function (x) { return [x.indirect, tr(x.x) + ' → ' + tr(x.mediator)]; }).reverse(), markLine: { symbol: 'none', lineStyle: { color: T.earth, type: 'dashed' }, data: [{ xAxis: 0 }] } }]
    }));
  }
  function renderHeterogeneity(d) {
    qs('#heteroTable').innerHTML = d.heterogeneity.map(function (row) {
      return '<tr><td>' + tr(row.label) + '</td><td>' + row.n_groups + '</td><td>' + fmt(row.lr_stat, 2) + '</td><td>' + pval(row.p_raw) + '</td><td>' + pval(row.p_holm) + '</td></tr>';
    }).join('');
    makeChart('heteroChart', Object.assign(baseOption(), {
      grid: { left: 82, right: 34, top: 32, bottom: 48 },
      xAxis: { type: 'category', data: d.heterogeneity.map(function (x) { return tr(x.label); }), axisLabel: { color: T.muted } },
      yAxis: { type: 'value', max: .8, name: 'Holm p', splitLine: { lineStyle: { color: T.grid } }, axisLabel: { color: T.muted } },
      series: [{ type: 'bar', data: d.heterogeneity.map(function (x) { return { value: x.p_holm, itemStyle: { color: x.p_holm < .05 ? T.red : T.primary, borderRadius: [4,4,0,0] } }; }), barMaxWidth: 34, label: { show: true, position: 'top', color: T.ink, formatter: function (p) { return p.value.toFixed(3); } }, markLine: { symbol: 'none', lineStyle: { color: T.earth, type: 'dashed' }, data: [{ yAxis: .05 }] } }]
    }));
  }
  function renderMl(d) {
    var rows = d.ml;
    qs('#mlTable').innerHTML = rows.map(function (row) {
      return '<tr' + (row.feature_set === 'extended' && row.model === 'ordered_logit' ? ' class="primary"' : '') + '><td>' + tr(row.feature_label) + '</td><td>' + tr(row.model_label) + '</td><td>' + fmt(row.accuracy, 3) + '</td><td>' + fmt(row.macro_f1, 3) + '</td><td>' + fmt(row.qwk, 3) + '</td><td>' + fmt(row.mae, 3) + '</td></tr>';
    }).join('');
    makeChart('mlChart', Object.assign(baseOption(), {
      legend: { top: 0, textStyle: { color: T.muted } },
      xAxis: { type: 'category', data: [tr('控制变量'), tr('控制变量 + T/V'), tr('扩展变量 + M1/M2')], axisLabel: { color: T.muted } },
      yAxis: { type: 'value', min: -.05, max: .8, name: 'QWK', splitLine: { lineStyle: { color: T.grid } }, axisLabel: { color: T.muted } },
      series: ['ordered_logit', 'random_forest'].map(function (model, i) { return { name: tr(i === 0 ? '有序 Logit' : '随机森林'), type: 'bar', barMaxWidth: 30, data: ['controls', 'core', 'extended'].map(function (feature) { var row = d.ml.find(function (x) { return x.feature_set === feature && x.model === model; }); return row.qwk; }), itemStyle: { color: i === 0 ? T.primary : T.secondary, borderRadius: [4,4,0,0] }, label: { show: true, position: 'top', color: T.ink, formatter: function (p) { return p.value.toFixed(3); } } }; })
    }));
    var shapRows = d.shap || [];
    var shapNode = document.getElementById('shapChart');
    if (shapNode) {
      shapNode.style.height = Math.max(430, shapRows.length * 28) + 'px';
      var core = { V: T.primary, T: T.secondary, M1: T.earth, M2: T.red };
      var labels = shapRows.map(shapLabel).reverse();
      var values = shapRows.map(function (row) {
        return { value: row.importance, itemStyle: { color: core[row.feature] || T.faint, borderRadius: [0, 4, 4, 0] } };
      }).reverse();
      makeChart('shapChart', Object.assign(baseOption(), {
        grid: { left: 22, right: 64, top: 22, bottom: 30, containLabel: true },
        yAxis: { type: 'category', data: labels, axisLine: { lineStyle: { color: T.line } }, axisLabel: { color: T.muted, fontSize: 11 } },
        xAxis: { type: 'value', name: 'mean |SHAP|', nameLocation: 'middle', nameGap: 26, nameTextStyle: { color: T.muted }, splitLine: { lineStyle: { color: T.grid } }, axisLabel: { color: T.muted, formatter: function (value) { return Number(value).toFixed(3); } } },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: function (items) { var item = items[0]; return item.name + '<br>mean |SHAP|: ' + Number(item.value).toFixed(4); } },
        series: [{ type: 'bar', data: values, barMaxWidth: 18, label: { show: true, position: 'right', color: T.ink, fontSize: 10, formatter: function (p) { return Number(p.value).toFixed(3); } } }]
      }));
    }
  }
  function renderAudit(d) {
    var audit = d.audit || {};
    var comps = audit.composites || {};
    var t = comps.T_primary || {};
    var v = comps.V_primary || {};
    qs('#auditRows').textContent = audit.n_rows == null ? '—' : audit.n_rows;
    qs('#auditAlphaT').textContent = t.cronbach_alpha == null ? '—' : fmt(t.cronbach_alpha, 3);
    qs('#auditAlphaV').textContent = v.cronbach_alpha == null ? '—' : fmt(v.cronbach_alpha, 3);
  }
  function render(d) {
    qs('#provenance').textContent = d.meta.run_id + ' · ' + d.meta.created_at_utc + '\nGit: ' + d.meta.git_commit + '\nSHA256: ' + d.meta.data_sha256;
    renderMetricCards(d); renderAudit(d); renderDirect(d); renderMediation(d); renderHeterogeneity(d); renderMl(d); }
  function initSectionNavigation() {
    var sections = Array.from(document.querySelectorAll('section.section[id]'));
    var links = document.querySelectorAll('.nav-links a, .toc a, .book-index a');
    var header = qs('.topbar');
    var pending = false;
    function update() {
      pending = false;
      var offset = header.getBoundingClientRect().height + 20;
      document.documentElement.style.setProperty('--nav-offset', offset + 'px');
      var current = null;
      sections.forEach(function (section) {
        if (section.getBoundingClientRect().top <= offset + 24) current = section.id;
      });
      links.forEach(function (link) {
        if (link.getAttribute('href') === '#' + current) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }
    function schedule() { if (!pending) { pending = true; requestAnimationFrame(update); } }
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    if (window.ResizeObserver) new ResizeObserver(schedule).observe(header);
    update();
  }
  function init() {
    initSectionNavigation();
    var book = qs('.book-viewport');
    if (book) {
      var previous = qs('#bookPrev'), next = qs('#bookNext');
      function updateBook() {
        previous.disabled = book.scrollLeft < 2;
        next.disabled = book.scrollLeft + book.clientWidth >= book.scrollWidth - 2;
      }
      function turn(direction) {
        var spread = book.querySelector('.book-spread');
        book.scrollBy({left: direction * (spread.getBoundingClientRect().width + 20), behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
      }
      previous.addEventListener('click', function () { turn(-1); });
      next.addEventListener('click', function () { turn(1); });
      book.addEventListener('scroll', updateBook);
      window.addEventListener('resize', updateBook);
      updateBook();
    }
    qs('#langSwitch').addEventListener('click', function () { setLang(state.lang === 'zh' ? 'en' : 'zh'); });
    fetch('static/data/report.json').then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }).then(function (d) { state.data = d; setLang(state.lang); }).catch(function (error) { qs('#loadStatus').hidden = false; console.error(error); });
    window.addEventListener('resize', function () { charts.forEach(function (chart) { chart.resize(); }); });
  }
  document.addEventListener('DOMContentLoaded', init);
})();
