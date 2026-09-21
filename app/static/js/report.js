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
    qs('#shapTable').innerHTML = d.shap.slice(0, 4).map(function (row) { return '<tr><td>' + tr(row.label) + '</td><td>' + fmt(row.importance, 3) + '</td></tr>'; }).join('');
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
  function init() {
    qs('#langSwitch').addEventListener('click', function () { setLang(state.lang === 'zh' ? 'en' : 'zh'); });
    fetch('static/data/report.json').then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }).then(function (d) { state.data = d; setLang(state.lang); }).catch(function (error) { qs('#loadStatus').hidden = false; console.error(error); });
    window.addEventListener('resize', function () { charts.forEach(function (chart) { chart.resize(); }); });
  }
  document.addEventListener('DOMContentLoaded', init);
})();
