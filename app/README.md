# EV Purchase Intention · Report page

这是项目的静态研究报告页，采用中文优先、英文可切换的纸张编辑风格。页面读取 [`static/data/report.json`](static/data/report.json) 中的汇总结果，不加载逐行问卷、逐行预测或逐行 SHAP。

## 本地预览

在项目根目录执行：

```bash
.venv/bin/python -m http.server 8787 --directory app
```

然后打开 <http://127.0.0.1:8787/>。

## 更新汇总结果

完整分析完成后，把运行目录传给构建脚本：

```bash
.venv/bin/python app/build_report_data.py --run-dir figures/runs/run-YYYYMMDD-HHMMSS
```

脚本只生成网页所需的聚合 JSON；它不会把原始 CSV 或逐行中间产物复制到 `app/`。提交前检查 `static/data/report.json` 中的运行时间、数据 SHA256、Git 提交号和主要指标。

## 发布

`main` 分支的推送会触发 `.github/workflows/pages.yml`，将 `app/` 发布到 GitHub Pages。预期地址：<https://yemyu.github.io/ev-purchase-intention/>。
