# 报告页

[中文](README.md) · [English](README.en.md) · [项目说明](../README.md)

中英文报告展示样本、变量定义和四个分析模块。图表读取 `static/data/report.json` 的汇总结果。

## 本地预览

从项目根目录、已激活的 Python 环境执行：

```bash
python -m http.server 8787 --directory app
```

中文入口为 <http://127.0.0.1:8787/>，英文入口为 <http://127.0.0.1:8787/en.html>。

## 更新结果

完整分析生成运行目录后：

```bash
python app/build_report_data.py --run-dir figures/runs/run-YYYYMMDD-HHMMSS
```

构建脚本更新网页汇总 JSON。页面只加载汇总结果；原始回答、逐行预测和逐行 SHAP 不作为网页资源。

发布前核对表格、图表和中英文说明中的数值。完整运行记录保存在本地结果目录。

## 发布

`.github/workflows/pages.yml` 在 `main` 分支推送后将 `app/` 发布到 [GitHub Pages](https://yemyu.github.io/ev-purchase-intention/)。

第三方图表库的许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
