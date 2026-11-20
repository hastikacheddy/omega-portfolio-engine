<div align="center">

# OMEGA 投资组合引擎

### 面向生产环境加固、带硬性合规门禁的混合投资组合构建引擎

[English](README.md) | 简体中文

[![CI](https://github.com/hastikacheddy/omega-portfolio-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/hastikacheddy/omega-portfolio-engine/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.1.0-informational.svg)](CHANGELOG.md)

</div>

---

## 概述

OMEGA 投资组合引擎是 [WISER Vanguard 挑战赛研究流水线](https://github.com/hastikacheddy/wiser-vanguard-quantum) 面向生产环境加固后的引擎版本：
**HRP 层次风险平价分解 → ADMM 协调 → 凸优化配置**。其中免惩罚项的量子 QAOA+ 选股路径以功能开关模块的形式提供（默认**关闭**），并始终由精确的经典算法兜底。

它把可部署的经典核心封装成一个可安装的库，提供受治理的 API、命令行工具、每次运行的审计清单、滚动前推（walk-forward）回测框架、持续集成下的测试套件，以及模型治理文档。

## 范围

明确界定范围本身就是设计的一部分。

| 已交付 | 有意不在范围内 |
|---|---|
| 可安装的软件包，含受治理的 API 与 CLI | 交易执行 / 订单管理系统（OMS）集成 |
| **硬性合规门禁**——绝不输出任何违反约束的组合 | 商业风险模型与时点（point-in-time）数据源 |
| 每次运行的**审计清单**（输入哈希、配置、诊断信息） | 流动性 / 日均成交量（ADV）及税批次约束 |
| **滚动前推**样本外回测（无未来信息泄漏） | 多用户服务接口 |
| pytest 不变量测试套件 + GitHub Actions CI | 独立的模型验证签核 |
| [MODEL_CARD.md](MODEL_CARD.md) 模型治理文档 | — |

右侧一栏列出的是组织层面的交付物，而非仓库内容，详见模型卡中的范围章节。

## 安装

需要 Python 3.10 及以上版本。

```bash
pip install -e ".[quantum,test]"
pytest                                       # 运行不变量测试套件
```

## 使用方法

### 命令行

```bash
# 基于已提交的 41 只 ETF 数据快照执行一次受治理的运行（离线）
omega-engine run --source snapshot --k 12 --w-max 0.15 \
    --income-floor 0.02 --cvar-weight 5 --out runs/

# 样本外滚动前推回放（按季度再平衡）
omega-engine backtest --k 10 --rebalance 63

# 量子选股路径（实验性开关；精确兜底始终启用）
omega-engine run --source synthetic --n 60 --k 15 --quantum
```

### Python API

```python
from omega_engine import ADMMConfig, PortfolioEngine
from omega_engine.market_snapshot import load_market_snapshot

engine = PortfolioEngine(
    config=ADMMConfig(income_floor=0.02, cvar_weight=5.0),
    quantum_enabled=False,          # 经典核心——今天即可部署
    output_dir="runs/",
)

result = engine.run(load_market_snapshot(), k_total=12, w_max=0.15)
print(result.summary())             # 一旦违反约束即抛出 EngineComplianceError
```

## 引擎保证

每一项保证都在代码中强制执行，并由 CI 测试套件覆盖。

1. **要么零违规输出，要么抛出异常**——绝不返回违反硬性约束的权重，而是抛出 `EngineComplianceError`。
2. **精确选出 K 个资产**——量子路径通过线路对称性保证（实测态矢量泄漏约 10⁻¹⁰），经典路径通过精确枚举保证。
3. **完全可审计**——每次运行都会生成 JSON 清单，包含输入哈希、配置、各聚类的 ADMM 诊断、违规审计和耗时；固定随机种子下结果确定可复现。
4. **故障安全**——量子路径的任何失败都会自动降级为精确的经典 z 更新并记录日志，不会阻塞流水线。

## 测试

```bash
pytest                                       # 编码、可行性、引擎、回测
```

测试套件会用暴力枚举验证 Ising 编码，验证拟设（ansatz）的汉明重量守恒、引擎合规约定与清单生成，并运行一个要求每次再平衡都零违规的滚动前推回测。每次推送都会通过 [GitHub Actions](.github/workflows/ci.yml) 自动运行。

## 文档

- **[MODEL_CARD.md](MODEL_CARD.md)**——用途、假设、验证证据、已知局限和变更管理（治理风格）。
- **[CHANGELOG.md](CHANGELOG.md)**——版本发布说明。

## 作者

**hastikacheddy** —— [github.com/hastikacheddy](https://github.com/hastikacheddy) · hastikacheddy06@gmail.com（个人参赛作品）

研究仓库（挑战赛提交，含演示文稿、数学建模、仪表盘和对抗性基准测试）：
[wiser-vanguard-quantum](https://github.com/hastikacheddy/wiser-vanguard-quantum)。

## 致谢与引用

**数据。** 已提交的 ETF 价格快照（[`data/etf_prices.csv`](data/etf_prices.csv)）为通过 [`yfinance`](https://github.com/ranaroussi/yfinance) 库从 **Yahoo Finance** 一次性获取的每日复权收盘价，仅用于研究演示。

**开源工具。**
[Qiskit](https://www.ibm.com/quantum/qiskit) / Qiskit Aer / Qiskit Algorithms ·
[CVXPY](https://www.cvxpy.org/)（Clarabel / OSQP / ECOS / SCS）·
[NumPy](https://numpy.org/) · [SciPy](https://scipy.org/) ·
[pandas](https://pandas.pydata.org/)。

**方法。**
HRP —— López de Prado (2016) ·
Dicke 态 —— Bärtschi & Eidenbenz (arXiv:1904.07358) ·
ADMM —— Boyd 等 (2011) ·
CVaR —— Rockafellar & Uryasev (2000)。

## 许可证

基于 [MIT 许可证](LICENSE) 发布。版本 0.1.0，详见 [CHANGELOG.md](CHANGELOG.md)。
