# cases/raw/ — 转换后的 56 个 Solomon-100 扩展格式实例

> 本目录由 `solomon_to_extended.py` 自动生成，**包含完整的 56 个 Solomon-100
> 实例**（C 类 17 个 + R 类 23 个 + RC 类 16 个）。每个 `.txt` 文件均为本题的
> `EUC_2D_X10` 扩展格式（含 `MAX_VEHICLES` 字段）。

## 数据来源链路

```
                      第 1 步                   第 2 步
   GitHub 公开镜像  ──────────►  raw_solomon100/ ──────────►  raw/
   (iRB-Lab/                   (Solomon 原始格式)           (本题扩展格式)
    py-ga-VRPTW)
                  curl 56 次                    solomon_to_extended.py
```

具体步骤（出题方部署评测时执行一次）：
```bash
cd internal/cases

# 第 1 步：从 GitHub 公开镜像拉取 56 个 Solomon-100 原始文件
mkdir -p raw_solomon100
for name in C101 C102 ... RC208; do  # 56 个名字详见 fetch_solomon.sh
  curl -sfL --max-time 15 \
    "https://raw.githubusercontent.com/iRB-Lab/py-ga-VRPTW/master/data/text/${name}.txt" \
    -o "raw_solomon100/${name}.txt"
done

# 第 2 步：转换成本题扩展格式（写入 raw/）
python3 solomon_to_extended.py raw_solomon100/ raw/
```

`workspace/instances/public/fetch_solomon.sh` 是 Agent 本地侧的"一键版本"，
它合并了上述两步，并附带写入 `.bks` 文件。

## 文件清单

`raw_solomon100/`：56 个 Solomon-100 原始格式（带 `VEHICLE NUMBER CAPACITY` /
`CUSTOMER CUST NO. ...` 表头）。

`raw/`：56 个本题扩展格式（带 `NAME` / `DIMENSION` / `CAPACITY` /
`MAX_VEHICLES` / `EDGE_WEIGHT_TYPE : EUC_2D_X10` 等头）。

## 远端评测时的部署

评测端通常会再做一步**节点编号置乱**（防止硬编码答案），通过
`scramble_nodes.py` 把 `raw/` 转换为 `scrambled/`，然后挂载到 evaluator：
```bash
python3 scramble_nodes.py \
    --src raw/ \
    --dst scrambled/ \
    --map ../scramble_map.json \
    --seed 20260507

docker run -d --name evaluator \
    -v "$PWD/scrambled":/srv/cvrptw/cases:ro \
    -v "$PWD/bks_snapshot.csv":/srv/cvrptw/bks_snapshot.csv:ro \
    -v "$PWD/../scramble_map.json":/srv/cvrptw/scramble_map.json:ro \
    cvrptw-evaluator:latest
```

## 自助验证

部署后运维 sanity check：
```bash
test "$(ls raw/*.txt | wc -l)" -eq 56 || echo "FAIL: not 56 instances"
test "$(tail -n +2 bks_snapshot.csv | wc -l)" -eq 56 || echo "FAIL: bks_snapshot rows"
```

## 数据合规

Solomon-100 数据集自 Solomon (1987) 论文起即为公开学术基准，多数 OR 教科书
与论文均直接引用，无版权争议。`iRB-Lab/py-ga-VRPTW` GitHub 仓库托管的副本
与 SINTEF 官方 VRPTW 页面（https://www.sintef.no/projectweb/top/vrptw/）
内容一致。
