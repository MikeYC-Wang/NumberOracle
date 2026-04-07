# 🔮 NumberOracle 號碼神諭

台灣樂透資料分析與選號預測平台，支援 **今彩539**、**大樂透**、**威力彩** 三種彩種。透過歷史開獎資料的統計分析與機率計算，提供熱冷號、遺漏值、走勢、區間分布、AC 值等多維度分析工具，並內建多種選號策略與回測系統。

> 本專案僅供資料分析與學術研究用途，樂透為獨立隨機事件，任何分析結果都不保證中獎。

---

## ✨ 功能特色

### 📊 資料分析
- **熱冷號分析**：依出現頻率排序，視覺化熱門/冷門號碼
- **遺漏值統計**：每個號碼距離上次出現的期數
- **走勢圖**：逐期號碼出現軌跡
- **連碰尾數 / 區間分布 / 奇偶大小 / AC 值 / 對碰頻率 / 路圖**
- **自選期數窗口**：所有分析支援近 N 期動態調整

### 🎯 選號預測
- **純隨機**：對照基準
- **熱門加權**：依頻率加權抽號
- **冷門加權**：依遺漏值加權抽號
- **均衡策略**：熱門 + 冷門組合（後端決定論版，前端隨機版）
- **手動選號**：互動式號碼球點選
- **跑馬燈動畫**：模擬真實搖獎體驗

### 👤 帳號功能
- 註冊 / 登入 / 登出（DRF Token 認證）
- **我的收藏**：儲存自選號碼組合
- **匯出 CSV**：下載開獎歷史資料

### 🧪 回測系統
- 蒙地卡羅模擬：N 期測試 × M 次模擬
- 自動跑「純隨機對照組」對比策略效果
- 命中數分布視覺化、平均命中、至少中 1/3 個比例

### ✅ 核對中獎
- 輸入號碼快速核對歷史開獎結果

---

## 🛠️ 技術棧

**後端**
- Django 6 + Django REST Framework
- PostgreSQL（`INTEGER[]` ArrayField + GIN 索引）
- DRF Token Authentication

**前端**
- Vue 3（Composition API）+ TypeScript
- Vite 8
- Pinia 狀態管理
- ECharts 圖表
- FontAwesome 圖示

---

## 📁 專案結構

```
NumberOracle/
├── backend/
│   ├── core/              # Django 專案設定
│   ├── lottery/           # 主應用：模型、ViewSet、management commands
│   │   └── management/commands/
│   │       ├── seed_games.py        # 初始化 3 種彩種
│   │       ├── fetch_draws.py       # 抓取歷史開獎資料
│   │       └── update_latest.py     # 更新最近兩個月資料（cron 用）
│   ├── accounts/          # 帳號應用：註冊/登入/個人資料
│   └── manage.py
├── frontend/
│   └── src/
│       ├── stores/        # Pinia: authStore, lotteryStore, analysisStore
│       ├── views/         # Dashboard, 三種彩種分析頁, 預測頁, 回測頁等
│       ├── components/
│       │   ├── charts/    # ECharts 包裝元件
│       │   └── common/    # LotteryBall, StatCard, DataTable 等
│       ├── composables/   # useChartOptions 等
│       └── types/         # TypeScript 介面定義
├── .env                   # 資料庫與 API 設定
├── CLAUDE.md              # Claude Code 開發指引
└── README.md
```

---

## 📋 環境需求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

---

## 🚀 安裝與設定

### 1. 取得專案
```bash
git clone <repository-url>
cd NumberOracle
```

### 2. 設定環境變數

在專案根目錄建立 `.env`：

```env
# 資料庫
DB_NAME=numberoracle
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# 前端 API 位址
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
```

### 3. 後端設定

```bash
cd backend

# 建立並啟用虛擬環境
python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash)
# venv\Scripts\Activate.ps1     # Windows (PowerShell)
# source venv/bin/activate      # macOS/Linux

# 安裝依賴
pip install -r requirements.txt

# 資料庫遷移
python manage.py migrate

# 初始化彩種資料
python manage.py seed_games

# 抓取歷史開獎資料
python manage.py fetch_draws --game daily_cash --year 2025
python manage.py fetch_draws --game lotto649 --year 2025
python manage.py fetch_draws --game super_lotto --year 2025

# 建立管理員帳號（選用）
python manage.py createsuperuser
```

### 4. 前端設定

```bash
cd frontend
npm install
```

---

## ▶️ 啟動開發環境

### 後端（從 `backend/` 目錄）
```bash
python manage.py runserver 8001
```
API 服務：http://127.0.0.1:8001

### 前端（從 `frontend/` 目錄）
```bash
npm run dev
```
網頁介面：http://localhost:5173

> **注意**：若 5173 被佔用，Vite 會自動換到 5174/5175，此時需將該 port 加入 `backend/core/settings.py` 的 `CORS_ALLOWED_ORIGINS`。

---

## ⚙️ 常用指令

### 後端（從 `backend/`）
| 指令 | 說明 |
|---|---|
| `python manage.py runserver 8001` | 啟動開發伺服器 |
| `python manage.py migrate` | 套用資料庫遷移 |
| `python manage.py makemigrations lottery` | 產生 lottery app 的遷移檔 |
| `python manage.py seed_games` | 初始化 3 種彩種記錄 |
| `python manage.py fetch_draws --game <code> --year <year>` | 抓取指定彩種與年份資料 |
| `python manage.py update_latest` | 更新最近兩個月資料（適合排程） |

### 前端（從 `frontend/`）
| 指令 | 說明 |
|---|---|
| `npm run dev` | Vite 開發伺服器 |
| `npm run build` | 型別檢查 + 正式版建置 |
| `npm run preview` | 預覽 build 結果 |
| `npx vue-tsc --noEmit` | 僅型別檢查 |

---

## 🎰 彩種代碼

| Code | 名稱 | 主號 | 特別號 |
|---|---|---|---|
| `daily_cash` | 今彩539 | 5 / 39 | 無 |
| `lotto649` | 大樂透 | 6 / 49 | 1 / 49 |
| `super_lotto` | 威力彩 | 6 / 38 | 1 / 8 |

---

## 🔌 API 端點概覽

所有端點以 `/api/v1/` 為前綴。

### 公開資料
- `GET /games/` — 取得所有彩種
- `GET /games/<code>/` — 取得特定彩種
- `GET /draws/` — 開獎資料列表（支援 `?game=&page_size=`）
- `GET /draws/hot_cold/?game=&recent=` — 熱冷號分析
- `GET /draws/missing_values/?game=` — 遺漏值
- `GET /draws/trend/?game=&recent=` — 走勢
- `GET /draws/summary/?game=` — 統計摘要
- `GET /draws/consecutive_tail/` / `zone_distribution/` / `odd_even_size/` / `ac_value/` / `pair_frequency/` / `road_map/` — 各類分析
- `POST /draws/check_numbers/` — 核對中獎
- `POST /draws/refresh/` — 刷新開獎資料（60 秒節流）
- `POST /draws/backtest/` — 策略回測

### 帳號（需登入則需 `Authorization: Token <token>`）
- `POST /auth/register/` — 註冊
- `POST /auth/login/` — 登入（取得 token）
- `POST /auth/logout/` — 登出
- `GET /auth/profile/` — 個人資料

---

## 🎨 設計約束

- **無 emoji**：UI 全面使用 FontAwesome 圖示
- **配色**：背景 `#F4F1DE` / 主色 `#E9C46A` / 次色 `#2A9D8F` / 強調色 `#E76F51`
- **語言**：UI 全面使用繁體中文（zh-Hant）
- **手機相容**：圖表元件需包在 `.chart-scroll-wrapper` 內以支援水平捲動

---

## 📦 資料來源

開獎資料透過 `fetch_draws` 指令從台灣彩券公開 API 取得，存入 PostgreSQL 的 `draw_results` 資料表（號碼以 `INTEGER[]` 陣列儲存，並建立 GIN 索引加速查詢）。

---

## 📄 授權

本專案僅供個人學習與資料分析使用。
