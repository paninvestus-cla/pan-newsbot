# ニュース駆動＋モメンタムBot（配布版）

PAN米国株研究会の認定サポーター向けの配布リポジトリです。

- 現在のバージョン: **v3.9.152**
- 変更内容は [CHANGELOG.md](CHANGELOG.md) を参照してください

## 入っているファイル

| ファイル | 内容 |
|---|---|
| `moomoo_trade_v1.py` | Bot本体 |
| `setup_wizard.py` | セットアップWizard（`.env` を作る） |
| `CHANGELOG.md` | 変更履歴 |

## 使い方

1. `python setup_wizard.py` で設定（`.env`）を作る
2. `python moomoo_trade_v1.py` でデモ口座から試す（`--live` で実口座）

実行にはmoomoo OpenDと、`moomoo-api` / `anthropic` / `python-dotenv` /
`requests` などのライブラリが必要です。

## 注意

- **このリポジトリは自動生成です。**ここを直しても本家には反映されません
- `.env`（APIキー・口座情報）は各自の環境で作るもので、ここには含まれません。
  作成した `.env` は絶対に共有しないでください
- 実口座での運用は自己責任でお願いします
