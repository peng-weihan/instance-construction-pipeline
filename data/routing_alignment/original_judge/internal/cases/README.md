# internal/cases/ — 远端评测数据集

> **不下发给 Agent**。由出题方/运维在每次评测部署时使用。

## 文件清单

```
cases/
├── README.md                  # 本文件
├── bks_snapshot.csv           # 56 实例的 BKS（来自 SINTEF 公布的 2024 快照）
├── solomon_to_extended.py     # Solomon 原始格式 → 本题扩展格式 转换器
├── scramble_nodes.py          # 节点编号置乱脚本（防硬编码答案）
├── gen_custom.py              # 自定义大规模实例生成器（备用，不计入主榜）
├── raw_solomon100/            # 56 个 Solomon-100 原始文件（GitHub 公开镜像副本）
│   └── *.txt × 56
├── raw/                       # 转换后的扩展格式实例（运行评测的输入）
│   ├── README.md              # 数据来源 + 转换流程
│   └── *.txt × 56
└── scrambled/                 # 节点编号置乱后的远端版本（每次部署重新生成）
```

## 数据流

```
                                          
   GitHub 公开镜像                    第 1 步
   iRB-Lab/py-ga-VRPTW   ──curl──►  raw_solomon100/
                                          │
                                          │ 第 2 步
                                          │ python3 solomon_to_extended.py
                                          ▼
                                        raw/                   第 3 步
                                          │  ──python3 scramble_nodes.py──►
                                          ▼
                                                              scrambled/
                                                                   │
                                                                   │ docker volume mount
                                                                   ▼
                                                              evaluator
```

## 操作指南（部署评测时）

### 第 1 步：拉取 56 个原始 Solomon-100 文件
```bash
mkdir -p raw_solomon100
for name in $(awk -F, 'NR>1{print $1}' bks_snapshot.csv); do
    curl -sfL --max-time 15 \
        "https://raw.githubusercontent.com/iRB-Lab/py-ga-VRPTW/master/data/text/${name}.txt" \
        -o "raw_solomon100/${name}.txt"
done
test "$(ls raw_solomon100/*.txt | wc -l)" -eq 56 || echo "FAIL: missing instances"
```

### 第 2 步：转换为扩展格式
```bash
python3 solomon_to_extended.py raw_solomon100/ raw/
```

### 第 3 步：节点编号置乱
```bash
python3 scramble_nodes.py \
    --src raw/ \
    --dst scrambled/ \
    --map ../scramble_map.json \
    --seed 20260507
```
- `--seed` 决定置乱密钥；同 seed 可复现。
- 输出 56 个 `<orig>_<6hex>.txt`，几何坐标不变，仅客户 ID 重排。
- `scramble_map.json` 保存反向映射（用于评测端复算原始 BKS），不下发。

### 第 4 步：启动 evaluator 并挂载数据
```bash
docker run -d --name evaluator -p 8080:8080 \
    -v "$PWD/scrambled":/srv/cvrptw/cases:ro \
    -v "$PWD/bks_snapshot.csv":/srv/cvrptw/bks_snapshot.csv:ro \
    -v "$PWD/../scramble_map.json":/srv/cvrptw/scramble_map.json:ro \
    -v /var/run/docker.sock:/var/run/docker.sock \
    cvrptw-evaluator:latest
```

## BKS 来源声明

`bks_snapshot.csv` 中每行包含：
- `name`：实例名（与 SINTEF/Solomon 1987 一致）
- `nv`：最佳已知车辆数
- `td`：在该 nv 下的最佳已知总距离
- `source`：`SINTEF-Solomon-2024`
- `verified`：出题方独立验证日期

所有 56 个 BKS 与 SINTEF VRPTW 页面（https://www.sintef.no/projectweb/top/vrptw/solomon-benchmark/100-customers/）公开榜单一致。

## 自定义实例生成器（备用）

`gen_custom.py` 用于在审核 / 调试时快速生成更大规模实例（200/500/1000/...
节点）：
```bash
python3 gen_custom.py --n 200 --kind C  --seed 42 --out /tmp/c200_42.txt
```
不计入正式评测，仅用于：
- 验证求解器在更大规模下的稳定性（regression test）；
- 制作"突破 BKS"的人工对照；
- 抗污染——LLM 训练数据中不会包含这些 seed-+-shape 组合。
