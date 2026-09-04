"""
setup_wizard.py
===============
moomoo_trade_v1.py 用 .env セットアップウィザード（完全版）
最新バージョン: v1.41  最終更新日: 2026-07-25

使い方:
  python3 setup_wizard.py   # Mac
  python  setup_wizard.py   # Windows

出力:
  moomoo_trade_v1.py と同じフォルダに .env ファイルを生成します。
  再実行時は変更前の設定を .env.backup_日時 に自動バックアップします。
  完了時に WIZARD_COMPLETED=true を .env に書き込みます。
"""

# =============================================================================
# 更新履歴
# =============================================================================
#
# v1.42 2026-08-06  Codexレビュー対応（表示番号の不整合5件）。①[0]戦略プロファイルの説明文とメニュー番号の逆転を解消（標準を[1]・選抜を[2]に並べ替え）。②ask_choiceのcustom_range指定時は「位置番号」ではなく「値そのもの」で選択（タイムアウトで「5」＝5分・指値バッファで「1」＝1%等の衝突を解消。表示も〔入力: 値〕形式に）。③トレール発動/幅・指値バッファの数値直接入力を正しく反映。④[2-c]setup_modeの既定を動的化（既存がカスタムなら[2]個別選択を既定にしEnterで上書きしない）。⑤番号参照ヒント（[2]/[4]を選択→値を入力）を修正。
# v1.41 2026-07-25  [6]損切りの方式に「+flatstop 検証群」の説明を追加（Bot v3.9.128 連動）。標準プロファイルで[2]固定損切りを選ぶと
#                   シートに+flatstopタグが付き、建玉トレール群との実データ比較に使われる（段階導入・Codex/週次レビュー優先度1）。設定挙動は不変。
# v1.43 2026-08-19  [5b]の表記を実挙動に一致（認定サポーターNの指摘）。損切り幅プロファイルは
#                   現在シャドー計測にのみ適用され、モメンタム実発注には効かないことを明記。
#                   上級者向け MOMENTUM_STOP_MULT_<SYM> も同様である旨を追記。設定値の意味・
#                   書き出しキーは不変更（再設定は不要）。
# v1.40 2026-07-21  [5b]の説明を実装方針に一致（Bot v3.9.123 連動・PAN方針決定）。
#   モメンタム実発注は「損切り幅のみボラ別に拡大・発注サイズは縮小しない」。旧文言の
#   「幅拡大とセットで発注サイズは÷倍率＝1回の想定損失額は一定」は削除（高ボラ銘柄ほど
#   手数料に勝ちやすくエッジの主力のため、サイズを削らない。総量はサーキットブレーカー管理）。
# v1.39 2026-07-19  UX改善5件（PANレビュー対応）。
#   ①STEP2タイムアウト: 全期間集計の根拠を表示（10分設定コホートが最良 +$5,261/2,473件・30分は-$10,657）＋
#     任意の分数を直接入力できる旨を明示（機能は v1.38 の custom_range 0〜240 で対応済み）。
#   ②STEP5時間帯: 「発注しない」選択時はそのセッション中のニュース取得・AI判定も停止される旨を明記
#     （Bot v3.9.6 で実装済み・API消費ゼロ。Wizard画面に説明が無かっただけ）。
#   ③STEP5移行前全決済: 「5分前」はBot既定(CLOSE_BEFORE_INACTIVE_MIN=5)と一致で正しい。
#     .env の CLOSE_BEFORE_INACTIVE_MIN(1〜60分)で変更可能な旨を追記。
#   ④STEP7指値バッファ: 選択肢を刷新。新標準は「ETF 0.30%／個別株 0.50%（銘柄タイプで使い分け）」
#     （キー未設定でBot内蔵の使い分け・v2.99.4実装が働く）。従来のWizard既定1.0%は単一値でこれを上書きし広すぎた。
#     バッファは「最悪許容の上限」であり通常は気配値付近で約定する旨も説明。0.30/0.50/1.0一律＋自由入力も可。
#   ⑤STEP11実口座ID取得: moomoo SDK の内部ログ(接続/切断行)を取得中は抑制し、受講生に見せない。
# v1.38 2026-07-19  外部AIコードレビュー(Codex)対応＋新標準値（全期間バックアップ集計10,053件で検証・非保証）。
#   【レビュー対応】①[3]リスク許容度の表示値を Bot 実プリセット(v3.9.x現行)に一致（旧表示は1段緩い値で不一致）。
#   ②選抜プロファイル選択時も「実発注するか」を必ず確認（従来はスキップで実発注ONのまま通過）。
#   ③起動バナーの版数を定数化(WIZARD_VERSION)し v1.23 表示の取り残しを解消。
#   ④ask_choice: Enter時の既定値も選択肢/範囲で検証（無効な既存.env値の素通り防止）。
#   ⑤警告レビュー画面の数値キー(MAX_LOSS_PCT等)に数値検証を追加（非数値で上書きするとBot起動拒否になるため）。
#   ⑥BUDGET入力の inf/nan ガード。⑦アラート音の夜間ミュートを HH:MM-HH:MM 形式で検証。
#   ⑧.env生成コメントの陳腐化修正（TRAIL_FROM_ENTRY: true=標準 / STOP_LOSS_PCTはSTEP13[5]で設定 / profile既定=select_v1）。
#   ⑨_build_env_lines の profileフォールバックを select_v1 に統一。⑩旧表記(×100変換)発生時に変換内容を表示。
#   ⑪[4]の「0.8%+は発注しない」説明を[2-d]上限設定と整合。⑫スキップ時文言に新規時の既定値を明記。
#   ⑬MOMENTUM_REVERSE_EXIT を .env 生成に追記（既定false=転換抑制・上級者向けコメント付き）。
#   【新標準値（集計根拠）】⑭利確トレール発動 TRAIL_TRIGGER_PCT 標準 0.30→0.22%
#     （全期間・最大含み益ベースの反実仮想で 全体+$4,152/建玉トレール+$2,546/モメンタム+$3,958 の改善。
#      旧標準0.30のままの既存userには新標準を既定候補として提示・Enterで移行、[2]で0.30維持可。近似・非保証）。
#   ⑮発注前の個別株トレンドチェックを新標準に: STOCK_DOWNTREND_15M/60M ±0.7/1.5→±0.3/0.9
#     （旧閾値は全期間で発火わずか＝実質機能せず。15分実測で新ブロック帯111件の実損益-$171を回避。
#      UPTREND側も対称に変更。未設定userのみ新標準を書き出し・手動設定済みの値は維持）。
# v1.37 2026-07-17  [0]戦略プロファイルの既定を「標準」→「選抜プロファイル v1」に変更（Bot既定は不変・env値で制御）。理由: 過去集計で標準より相対的に成績が良好かつ、実発注が少なく1トレードのリスクも小さい（＝より保守的）ため。未設定の新規は select_v1 を既定表示。表現は「標準よりマシ・低リスク」に留め、戦略全体はまだ黒字化していない旨・利益非保証を明記（誇張しない）。標準はいつでも[1]で選べる。※発見済みだが検証中の施策（寄りドリフトSHORTフィルタ・利益トレール発動0.22%）は未検証のため既定に含めない。
# v1.36 2026-07-11  [0]で選抜プロファイル v1 を選ぶと、STEP13の詳細設定([1]発火頻度〜[6]損切り方式)を尋ねずスキップして次STEPへ進むように変更。プロファイルが実発注の絞り込み（SHORTのみ・SPY除外・ET9/10/12/13時台・固定損切り・日次1.5%）を内蔵するため。スキップ時、発火頻度/リスク/最大%/損切り幅等は現在値(未設定なら既定)を維持し書き出す。標準を選べば従来どおり全設定を対話。
# v1.35 2026-07-11  STEP13冒頭に[0]戦略プロファイルを追加（Bot v3.9.116連動）。標準（今まで通り・既定）/選抜プロファイルv1（絞り込み運転）の2択。選抜=SHORTのみ・SPY除外・ET9/10/12/13時台のみ実発注・固定損切り・日次損失予算1.5%。約5週間の全取引データ集計（実発注4,266件＋ユニークシャドーシグナル4,952件・5週すべてプラス・前半/後半スプリット検証済み）に基づく。書き出しキーに MOMENTUM_STRATEGY_PROFILE を追加。選ばなければ完全に従来どおり。表現は数値基準＋過去観察（非保証）。
# v1.34 2026-07-08  STEP13モメンタムに2項目追加（Bot v3.9.114連動）。[2-d]ロング発注のシグナル強度レンジ（5分・下限0.70/上限選択式・「ロングは発注しない」でBUYサイド除外）、[5b]損切り幅プロファイル（狭め/標準(既定)/広め/一律/env個別・ボラ別倍率 SMH×3.0 QQQ×2.0 SPY×1.3 DRAM×2.0 IWM×1.0）。書き出しキーに MOMENTUM_STOP_PROFILE / MOMENTUM_LONG_MIN_SIGNAL_PCT / MOMENTUM_LONG_MAX_SIGNAL_PCT を追加。表現は数値基準＋過去観察（非保証）で統一し「勝てる」等の断定は不使用。
# v1.33 2026-07-05  STEP12(データ収集)の説明を実態に更新。①送信タイミングを項目別に明記（トレード=決済ごと/シャドー観察=セッション中にまとめて/日次集計=1日1回EOD後）。②シャドー観察（未発注シグナルの理論損益・見送り理由）を送信データに明示。③負荷抑制のためまとめて送る旨・収集項目は改善に応じ最適化する旨を追記（Bot v3.9.110 のシャドー軽量化と整合）。「1日1回/EOD後に全送信」という旧表記の誤りを修正。
# v1.32 2026-07-04  STEP3(トレール発動/トレール幅)を自由入力対応（選択肢番号のほか数値の直接入力可・0.05〜5.0%）。.env直接編集ができない受講生でも任意の値を設定できるように。プリセット外の既存カスタム値はEnterで維持と明示。
# v1.31 2026-07-02  実口座向け注意文を追加。STEP1（予算）と実口座ID設定後に「BUDGET_USDは実際の信用余力の範囲内に（複数銘柄の同時保有を考慮）」を表示（信用余力不足による発注拒否の予防・Bot v3.9.106 連動）。
# v1.30 2026-07-02  外部コードレビュー対応2件。①STEP5: カスタムしきい値/ベース変更後の旧値をEnter「維持」すると黙って「発注しない(2.00)」に置換されるバグを修正（custom検出で既存値をそのまま維持・非数値でもクラッシュしない・カスタム値≥2.0は発注しない扱い）。②STEP11: MOOMOO_PORTを検証（数値1〜65535・不正は再入力。無検証保存だと本体が起動時int()で即死するため）。
# v1.29 2026-06-28  マスク入力のブラケットペースト対応バグ修正。端末の括弧付き貼り付け(ESC[200~ … ESC[201~)時、ESC後を固定2バイトしか捨てず残骸(00~/01~)が値先頭末尾に混入→正しいURL/キーでも検証が誤失敗していた(Discord URLや sk-ant- 等全secret入力に影響)。ESCシーケンスを終端まで読み捨て(両OS)＋_sanitize_api_keyでマーカー除去(保険)。Discord URL判定を許容形広め(旧discordapp.com/canary./ptb./apiバージョン)に統一。
# v1.28 2026-06-28  STEP11実口座IDの「手動入力」を廃止（受講生はacc_idを手動取得する手段がないため）。取得はOpenD自動取得に一本化。取得失敗時は「再試行／いまは設定しない(デモのみ・既存維持)」の2択。口座選択の「0=手動入力」も削除。
# v1.27 2026-06-28  STEP11実口座IDの自動取得を堅牢化。OpenD未起動時はSDK生成前にTCP到達性を確認(2秒)して即・無汚染で失敗（従来はECONNREFUSEDで数回リトライ＆ログがマスク入力に被り表示/入力が乱れた）。失敗時は強制で手動に落とさず「OpenD起動して再試行/手動入力/いまは設定しない」を選択可能に。手動入力は既存値ありならEnter=維持と明示。
# v1.26 2026-06-27  各STEP末尾で「b＋Enter＝ひとつ前のSTEPに戻る」を追加（先頭STEPを除く）。やり直し時は前回入力値を既定表示。STEP間依存(予算/ベース自信度)はstate参照に変更。最初からやり直し/.env直編集が不要に。STEP番号・項目は不変。
# v1.25 2026-06-27  STEP10(Finnhub)内にDiscord Webhook設定を追加（従来の「手動記入のみ」を廃止）。Webhook URLは一部マスク表示・secret入力・形式チェック付き。STEP番号は据え置き（マニュアル影響なし）。
# v1.24 2026-06-27  STEP11(OpenD接続)に実口座(--live)用 MOOMOO_ACC_ID 設定を追加。「実口座を使うか」を確認し、OpenDから口座一覧を自動取得して選択 or 手動入力→.envへ書込（手動編集が不要に）。デモのみなら従来どおりスキップ。実口座移行の解禁に対応。
# v1.23 2026-06-19  [6]損切りの方式の既定を「建玉トレール（標準）」に変更（番号も[1]建玉トレール/[2]従来固定に入替）。未設定はtrue扱い。Bot v3.9.90 連動。
# v1.22 2026-06-12  モメンタムSTEPに[6]損切りの方式を追加（従来=固定[標準]/建玉トレール[検証中の実験]・MOMENTUM_TRAIL_FROM_ENTRY/既定false）。利益は減らさず即切り額を小さくする検証用。Bot v3.9.85 連動。
# v1.21 2026-06-10  STEPを11→14に再編(データ収集12/モメンタム13/アラート音14を正式STEP化)＋モメンタムを重要STEPに格上げ。実発注にY/N確認クッション追加。[2-c]に標準セット一括プリセット＋1日損失目安$表示。ask_ynの日本語対応(「いいえ」誤判定の修正)。STEP6クロス参照を「STEP13」に。お勧め文言/Finnhub標準/山型配分の表現を整理。
# v1.20 2026-06-09  IWM/DRAMをシャドー観察のみに戻す（実発注選択不可・[2-c]はSPY/QQQ/SMHのみ）。発注対象の説明も更新 (Bot v3.9.79 連動)
# v1.19 2026-06-09  発注対象の説明を修正（デモ空売りは対応済み＝誤った『空売り不可→シャドー』文言を削除）。[2-c]にDRAMを追加しIWM/DRAMを実験機能と明記（DRAM既定=観察のみ/opt-in）
# v1.18 2026-06-09  STEP6を「ニュース駆動の銘柄」と明確化＋現在のモメンタム実発注銘柄を表示／確認画面にMOMENTUM実発注行を追加（TRIGGER_TICKERSと別系統と明示）。[2-c]の「(標準: 売りのみ)」表記を撤去し既定を「両方」に変更（買い・売り両方のデータ取得のため）
# v1.17 2026-06-09  STEP6 の銘柄選択説明を修正（「信用取引口座のため現物ETFで発注」の矛盾表現を「対象は米国ETF。買い・空売りの両方に対応」に変更）
# v1.16 2026-06-07  PCT入力を「1=1%」に統一(TRAIL_TRIGGER/TRAIL_DROP/LIMIT_BUFFER)。旧 .env の小数(0.003等)は再実行時に×100で半自動変換し新表記を既定提示 (Bot v3.9.73 連動)
# v1.15 2026-06-05  [2-c]を銘柄ごとの買い/売り個別選択に変更 (SPY/QQQ/SMH/IWM・標準既定=売り中心) (Bot v3.9.71 連動)
# v1.14 2026-06-04  [2-c]実発注対象サイド選択を追加しMOMENTUM_ENABLED_SIDESを明示書き出し / DRAMは実発注対象外 (Bot v3.9.70 連動)
# v1.13 2026-06-03  動作モード/デモ空売りの既定をON化 + [2-b]デモ空売りトグル追加 (Bot v3.9.68 連動)
# v1.12 2026-06-02  デモ・ネッティング空売り DEMO_SHORT_ENABLED を .env 出力に追加 (Bot v3.9.65 連動)
# v1.11 2026-06-01  モメンタム損切りライン MOMENTUM_STOP_LOSS_PCT を選択可能に (Bot v3.9.63 連動)
#                   - モメンタム STEP に [5] 損切りライン (%) を追加 (標準 0.50%)
#                   - ボット側で MOMENTUM_STOP_LOSS_PCT を実際に強制損切りへ適用
# v1.10 2026-05-24  損切り / トレール標準値を改訂 (Bot v3.9.46 連動)
#                   - MAX_LOSS_PCT       標準: 0.50% → 0.30% (損失幅縮小)
#                   - TRAIL_TRIGGER_PCT  標準: 1.0%  → 0.30% (トレール発動を早く)
#                   - TRAIL_DROP_PCT     標準: 0.5%  → 0.15% (利益取りこぼし減)
#                   損益非対称性を 5:1 → 2:1 に改善・損益分岐 WR 67% を目標。
#                   既存の .env 設定値は維持され、選択肢として旧標準値も残す。
# v1.9  2026-05-23  API キーの非 ASCII 文字を保存前にサニタイズ (Bot v3.9.42 連動)
#                   - 受講生 .env で ANTHROPIC_API_KEY 末尾に全角スペース・
#                     スマートクォート・日本語コメントが混入していたため、httpx が
#                     HTTP ヘッダの ASCII エンコードで毎回 UnicodeEncodeError を出して
#                     AI 呼出が 5/18-22 で 3,924 件全失敗・発注ゼロという深刻な
#                     不具合が発生。Wizard 側で .env 保存前に
#                     ANTHROPIC_API_KEY / FINNHUB_API_KEY / ALPACA_API_KEY_ID /
#                     ALPACA_API_SECRET_KEY / DISCORD_WEBHOOK_URL の非 ASCII 文字
#                     と囲みクォートを除去し、混入があれば警告を表示する。
# v1.8  2026-05-22  表示文言「推奨」を「標準」に統一 + APIキーマスク強化 + 表示整理
#                   - 「推奨」表現は投資助言と受け取られる可能性があるため、
#                     Wizard 内の全表示文言を「標準」「標準的な範囲」等に置換
#                   - 対象: STRONG_BUY_CONFIDENCE 目安 / モメンタム LEVEL /
#                     リスク LEVEL / Finnhub STEP / 設定警告メッセージ群
#                   - 値の選択肢マーカーは「← まずここから」に統一
#                   - APIキー漏洩防止: FINNHUB_API_KEY / ALPACA_API_KEY_ID の
#                     入力欄を secret=True 化（画面に平文表示しない・マスク表示）
#                     設定警告メッセージのキー表示も _mask_key() でマスク
#                   - モメンタム STEP の「上級者向け（任意）」.env 案内を削除
#                   - アラート音 STEP の macOS 音源パス選択を削除
#                     (既存値 or デフォルト Sosumi をそのまま使用)
# v1.7  2026-05-22  STEP 2 に高ボラ銘柄の損切り自動調整の説明を追加
#                   （moomoo_trade_v1.py v3.9.32 連動）
#                   - NVDA/SMH 等の高ボラ銘柄は損切り幅を 2.5 倍に自動拡大し、
#                     同時にポジションサイズを 1/2.5 に縮小する旨を明示
#                   - 「想定最大損失額は ETF と同水準」「設定不要・自動」を案内
#                   - 無効化したい場合の STOCK_HIGHVOL_LOSS_MULT=0 も併記
# v1.3  2026-05-08  クリア機能・マスク表示入力・STEP リナンバー
#                   - ask() に allow_clear=True 追加：
#                     「-」「なし」「none」「クリア」入力で空文字を返し、
#                     設定値を明示的にクリア可能（_CLEAR_TOKENS）
#                   - 適用箇所: STEP 6 個別株 / STEP 9 Alpaca / STEP 10 Finnhub
#                   - _read_masked_input() 新規追加（v1.3）：
#                     getpass.getpass() の「入力が見えない」問題への対策
#                     1 文字入力ごとに '*' を表示しながら受け取る
#                     Windows: msvcrt / Mac/Linux: termios+tty
#                   - 機密入力 4 箇所すべて ask(secret=True) 経由に統一
#                   - STEP 7 「Enter=デフォルト」→「Enter=現在値を維持」に統一
#                     （他STEPと表現を揃える・サポーター指摘）
#                   - STEP 9 欠番を解消（旧 STEP 10/11/12 → 9/10/11）
#                     TOTAL = 12 → 11、main() 呼び出しと step_labels 更新
#                   - 起動画面 step_labels の STEP 3-8 既存ラベルずれを修正
#                     （実装と 2 ステップずれていたバグの解消）
#                   - moomoo_trade_v1.py v3.6.0 と連動：STEP 5「発注しない」
#                     セッションは AI 送信・ニュース取得・発注すべてが停止
#
# v1.2  2026-05-01  全12STEPに再構成・起動画面統一・複数機能追加
#                   - 起動画面を初回/再実行で統一（STEPリスト表示）
#                   - STEP 1: BUDGET説明文を手数料負けリスク案内に変更
#                   - STEP 5: SESSION を全面刷新
#                     発注しない/慎重/標準/積極の4択（セッション別）
#                     移行前全決済オプション（CLOSE_BEFORE_INACTIVE）追加
#                   - STEP 6: SYMBOLS を新プリセット体系に変更
#                     SPY / SPY+QQQ / SPY+QQQ+SMH の3択
#                     個別株追加時にETFバリデーション追加
#                   - STEP 10: Alpaca News API を独立STEPとして追加
#                   - STEP 11: Finnhub（推奨）に変更
#                   - STEP 12: moomoo接続（従来STEP 10）
#
# v1.1  2026-04-29  保存前の設定レビュー・警告チェック機能を追加
#                   - PCT単位誤り / 極端値 / 論理矛盾 / APIキー形式を自動検出
#                   - エラー（E）: 保存前に修正必須
#                   - 警告（W）: 確認後スキップ可
#                   - パターンC方式: 問題項目をその場でインライン修正 -> 再チェック
#
# v1.0  2026-04-19  起動コマンド案内を OS 別に自動切り替え
#                   - Windows: python moomoo_trade_v1.py
#                   - Mac/Linux: python3 moomoo_trade_v1.py
#
# v0.9  2026-04-15  各設定の説明文・選択肢ラベルを改善
#                   - 時間切れ決済の説明を「鮮度」の観点で補足
#                   - 銘柄選択の「推奨」→「標準」に変更
#                   - ピラミッディングの目的説明を追加
#                   - PYRAMID_ALLIN_THRESHOLD の選択肢ラベル修正
#                   - Alpha Vantage・AlpacaをSTEP 9から除外（既存値引き継ぎ）
#                   - バージョン履歴をBotと同形式に統一
#
# v0.8  2026-04-14  全設定項目対応・グループ化・全10ステップに再構成
#                   - PANIC_CONFIDENCE追加（STEP 4）
#                   - 発注詳細グループ追加（STEP 7）:
#                     LIMIT_BUFFER_PCT / ORDER_CANCEL_MINUTES /
#                     PYRAMID_MAX_ENTRIES / PYRAMID_ALLIN_THRESHOLD
#                   - FINNHUB / ALPHAVANTAGE / ALPACA を STEP 9 に集約
#                   - Discord設定をWizardから除外（手動記入方式）
#
# v0.7  2026-04-14  時間帯別AIしきい値（STEP 6）を追加
#                   CONFIDENCE_PREMARKET / AFTERHOURS / OVERNIGHT を出力
#
# v0.6  2026-04-14  Alpacaキーを手動記入方式に変更・Wizardから削除
#
# v0.5  2026-04-14  Alpaca APIキー設定を追加
#
# v0.4  2026-04-14  MOOMOO_TRADE_PASSWORD設定を削除
#
# v0.3  2026-04-14  ブル/ベア→ロング/ショートに用語統一
#
# v0.2  2026-04-13  10ステップ化
#
# v0.1  2026-04-13  初回リリース（5ステップ構成）

import os
import sys
import getpass
import datetime
import math  # v1.38: BUDGET 入力の inf/nan ガードに使用
import re
import platform  # v1.4: アラート音 STEP で OS 判定に使用
import subprocess  # v1.8: アラート音テスト再生で OS コマンド呼出に使用
import socket  # v1.27: OpenD 自動取得前の到達性チェック（SDKの長い再試行/ログ汚染を回避）


def _play_test_sound(macos_file: str = "/System/Library/Sounds/Sosumi.aiff") -> bool:
    """★ v1.8: アラート音を実際に 1 回鳴らして確認できるようにする。
    OS 別にコマンドを切り替え。音声デバイス無し / SSH リモート等で失敗しても
    例外は出さず False を返すだけ (Bot 本体の _play_alert_sound と同じ方針)。
    """
    try:
        system = platform.system()
        if system == "Darwin":          # macOS
            subprocess.run(["afplay", macos_file], timeout=5,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        elif system == "Windows":       # Windows
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            return True
        else:                            # Linux ほか
            for _cmd in (["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"],
                         ["aplay", "/usr/share/sounds/alsa/Front_Center.wav"]):
                try:
                    subprocess.run(_cmd, timeout=5,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
                except Exception:
                    continue
            # 端末ベル (最終フォールバック)
            sys.stdout.write("\a")
            sys.stdout.flush()
            return False
    except Exception:
        return False

def _c(code, text): return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text
def bold(t):   return _c("1", t)
def dim(t):    return _c("2", t)
def red(t):    return _c("91", t)
def yellow(t): return _c("93", t)
def green(t):  return _c("92", t)
def cyan(t):   return _c("96", t)
def blue(t):   return _c("94", t)

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def hr():
    print(dim("─" * 60))

def header(step, total, title):
    clear()
    steps_str = "  ".join(
        bold(f"[{i}]") if i == step else dim(f"[{i}]")
        for i in range(1, total + 1)
    )
    print(f"\n  {steps_str}")
    print(f"\n  {bold(title)}\n")
    hr()
    print()

# ── ★ v1.3: クリアトークン（クリア時に空文字を返すための入力値）─────────────
_CLEAR_TOKENS = ("-", "なし", "none", "クリア")

def _read_masked_input() -> str:
    """
    機密入力を 1 文字ずつ '*' でマスクしながら受け取る（v1.3 新規）。
    getpass.getpass() の「入力中に何も表示されない」問題への対策。

    挙動:
      - 通常文字  : '*' を表示してバッファに追加
      - Backspace : バッファから削除＋画面の '*' を消す
      - Enter     : 改行して入力確定
      - Ctrl+C    : KeyboardInterrupt
      - 制御文字  : 無視（矢印キー・Function キー等）

    対応 OS:
      - Windows  : msvcrt.getwch()
      - Mac/Linux: termios + tty で raw モード
      - 上記不可 : getpass.getpass() にフォールバック（パイプ実行等）
    """
    chars: list = []

    if os.name == "nt":
        try:
            import msvcrt
            while True:
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    sys.stdout.write("\n"); sys.stdout.flush()
                    return "".join(chars)
                elif ch == "\x03":
                    raise KeyboardInterrupt
                elif ch in ("\b", "\x7f"):
                    if chars:
                        chars.pop()
                        sys.stdout.write("\b \b"); sys.stdout.flush()
                elif ch == "\x00" or ch == "\xe0":
                    msvcrt.getwch()  # 2バイト目を捨てる（矢印等）
                elif ch == "\x1b":
                    # ★ v1.29: ESC シーケンス（矢印 / ブラケットペースト ESC[200~ 等）を
                    #          終端バイト(0x40-0x7E)まで読み捨てる。これをしないと貼り付け時に
                    #          [200~ / [201~ の残骸が値に混入し URL/キー検証が誤って失敗する。
                    nxt = msvcrt.getwch() if msvcrt.kbhit() else ""
                    if nxt == "[":
                        while msvcrt.kbhit():
                            fb = msvcrt.getwch()
                            if "\x40" <= fb <= "\x7e":
                                break
                elif ch.isprintable():
                    chars.append(ch)
                    sys.stdout.write("*"); sys.stdout.flush()
        except (ImportError, OSError):
            pass
    else:
        try:
            import termios, tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        sys.stdout.write("\r\n"); sys.stdout.flush()
                        return "".join(chars)
                    elif ch == "\x03":
                        raise KeyboardInterrupt
                    elif ch in ("\b", "\x7f"):
                        if chars:
                            chars.pop()
                            sys.stdout.write("\b \b"); sys.stdout.flush()
                    elif ch == "\x1b":  # ESC: 矢印キー/ブラケットペースト(ESC[200~ 等)
                        # ★ v1.29: 固定2バイトでは ESC[200~ (6バイト) を取りこぼし、
                        #          残骸 00~ / 01~ が値に混入して URL/キー検証が誤失敗していた。
                        #          終端バイト(0x40-0x7E)まで読み捨てる。
                        try:
                            import select as _sel
                            nxt = sys.stdin.read(1) if _sel.select([sys.stdin], [], [], 0.05)[0] else ""
                            if nxt == "[":
                                while _sel.select([sys.stdin], [], [], 0.05)[0]:
                                    fb = sys.stdin.read(1)
                                    if not fb or ("\x40" <= fb <= "\x7e"):
                                        break
                        except Exception:
                            pass
                    elif ch.isprintable():
                        chars.append(ch)
                        sys.stdout.write("*"); sys.stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (ImportError, OSError, Exception):
            pass

    # フォールバック（パイプ実行・サポート外端末など）
    return getpass.getpass("")


def ask(prompt, default="", secret=False, allow_clear=False):
    disp = f"  {cyan('?')} {prompt}"
    if default and not secret:
        # secret=True の場合はデフォルト値を表示しない（APIキー漏洩防止）
        disp += f"  {dim(f'[現在: {default}]')}"
    elif default and secret:
        disp += f"  {dim('[現在: 設定済み / Enter で維持]')}"
    if allow_clear:
        disp += f"  {dim('[クリアは「-」]')}"
    if secret:
        disp += f"  {dim('[* で表示]')}"
    disp += "  "
    while True:
        try:
            if secret:
                sys.stdout.write(disp); sys.stdout.flush()
                val = _read_masked_input().strip()
            else:
                val = input(disp).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  " + yellow("キャンセルしました。"))
            sys.exit(0)
        # ★ v1.3: クリア指示を最優先で判定（_CLEAR_TOKENS のいずれかなら空文字を返す）
        if allow_clear and val in _CLEAR_TOKENS:
            return ""
        if not val and default:
            return default
        if val:
            return val
        if not default:
            return ""

def ask_yn(prompt, default=True):
    # ★ v1.21 (点5b): 日本語「はい/いいえ」も受け付ける。従来は「いいえ」が True(=はい)
    #   扱いになる不具合があった（N/NO 以外は全て True だったため）。
    hint = "(Y/N)"
    raw = ask(f"{prompt} {dim(hint)}", default="Y" if default else "N")
    s = raw.strip().lower()
    if s in ("n", "no", "いいえ", "no.", "いや", "しない"):
        return False
    if s in ("y", "yes", "はい", "する", "ok"):
        return True
    # 不明な入力は既定値を採用（誤って True に倒さない）
    return default

def ask_choice(prompt, choices, default="", custom_range=None):
    """選択式入力。custom_range=(min,max) を渡すと『値の直接入力』モードになる。
    ★ v1.42: custom_range 指定時は位置番号[1][2]ではなく“値そのもの”で選ぶ
    （番号と値の衝突を防止。例: タイムアウトで「5」＝5分、指値バッファで「1」＝1%）。
    一覧の値と一致すればそれ、範囲内の数値ならその値を採用。custom_range 無しの
    ときは従来どおり [1][2]… の番号で選ぶ（★ v1.32: .env 直接編集不可の受講生向け）。"""
    def _normalize(v):
        """'0.010' と '0.01' を同一視するため数値に変換して比較"""
        try:
            return float(v)
        except (ValueError, TypeError):
            return v

    default_norm = _normalize(default)
    matched = False
    for i, (key, label) in enumerate(choices, 1):
        is_cur = _normalize(key) == default_norm
        matched = matched or is_cur
        marker = green("▶") if is_cur else " "
        if custom_range is not None:
            # ★ v1.42: 値入力モードは位置番号を出さず、入力すべき値を示す（番号/値の衝突防止）
            print(f"  {marker} {label}　〔入力: {key}〕")
        else:
            print(f"  {marker} [{i}] {label}")
    if custom_range is not None and not matched and default:
        print(f"  {green('▶')} [Enter] 現在の値 {default} を維持")
    print()
    while True:
        val = ask(prompt, default="")
        if not val and default:
            # ★ v1.38: Enter維持でも既定値の妥当性を検証（無効な既存 .env 値の素通り防止）
            if any(default == c[0] for c in choices):
                return default
            if custom_range is not None:
                try:
                    _dv = float(default)
                    _lo, _hi = custom_range
                    if _lo <= _dv <= _hi:
                        return default
                except (ValueError, TypeError):
                    pass
            warn(f"現在の値 {default!r} は選択肢・許容範囲の外です。番号か有効な数値を入力してください")
            continue
        if custom_range is not None:
            # ★ v1.42: 値として解釈（一覧の値と一致 → 範囲内の数値）。位置番号は使わない。
            for _k, _ in choices:
                if _normalize(val) == _normalize(_k):
                    return _k
            try:
                fv = float(val)
                lo, hi = custom_range
                if lo <= fv <= hi:
                    return f"{fv:g}"
            except (ValueError, TypeError):
                pass
            lo, hi = custom_range
            warn(f"一覧の値、または {lo}〜{hi} の数値を入力してください（例: {choices[0][0]}）")
            continue
        try:
            idx = int(val) - 1
            if 0 <= idx < len(choices):
                return choices[idx][0]
        except ValueError:
            pass
        warn(f"1〜{len(choices)} の番号を入力してください")

def info(text):
    print(f"  {dim(text)}\n")

def warn(text):
    for line in text.strip().splitlines():
        print(f"  {yellow('!')} {yellow(line)}")
    print()

def ok(text):
    print(f"  {green('✓')} {green(text)}\n")

def success(text):
    print(f"  {green('✓')} {text}")

def box(title, lines, color=None):
    if color is None:
        color = dim
    print(f"  ┌─ {bold(title)}")
    for line in lines:
        print(f"  │  {color(line)}")
    print(f"  └{'─' * 48}")
    print()

# 機密キーのマスク表示
_SENSITIVE_KEYS = {
    "ANTHROPIC_API_KEY", "FINNHUB_API_KEY", "ALPACA_API_KEY_ID",
    "ALPACA_API_SECRET_KEY", "DISCORD_WEBHOOK_URL",
    "MOOMOO_ACC_ID",   # ★ v1.24: 実口座IDも機密扱い（確認画面の編集でもマスク＆secret入力）
}

def _mask_key(val):
    """APIキーを安全にマスク表示する"""
    if not val:
        return dim("（未設定）")
    visible = min(6, len(val) // 3)
    return green(val[:visible] + "●●●●●●●●" + (val[-4:] if len(val) > visible + 4 else ""))


# ★ v1.29: Discord Webhook URL の許容形を広めに判定（正規/旧ドメイン/サブドメイン/APIバージョン対応）。
#   従来は "https://discord.com/api/webhooks/" 完全一致のみで、正しいURLでも誤警告が出ていた。
_DISCORD_WEBHOOK_RE = re.compile(
    r"^https://(canary\.|ptb\.)?discord(app)?\.com/api/(v\d+/)?webhooks/\d+/\S+$",
    re.IGNORECASE,
)
def _is_discord_webhook(u):
    return bool(_DISCORD_WEBHOOK_RE.match((u or "").strip()))


def _sanitize_api_key(raw, key_name=""):
    """★ v1.9 (Bot v3.9.42 連動): API キー / Webhook URL から非 ASCII 文字 / 囲み
    クォート / 全角スペース等を除去する。

    .env のコピペ時に混入したスマートクォート ("" '' U+2018/U+2019/U+201C/U+201D)・
    全角スペース・日本語コメント・BOM・末尾の改行や制御文字を全て除去し、
    httpx が HTTP ヘッダの ASCII エンコードで毎回 UnicodeEncodeError を出して
    ボットの AI 呼出が全失敗する (5/18-22 ログで 3,924 件確認) のを防ぐ。

    何か除去された場合は (clean, dropped_count) を返し、呼び出し側で必要なら
    通知できるようにする。
    """
    if not raw:
        return "", 0
    s = "".join(ch for ch in raw if ord(ch) < 128)
    # ★ v1.29: ブラケットペースト/ANSI の残骸を除去（raw貼り付け対策・保険）。
    #   端末の括弧付き貼り付けで ESC[200~ … ESC[201~ が値に混入すると
    #   URL/キー検証が誤って失敗する。ESC本体とマーカーを除去する。
    s = s.replace("\x1b", "")
    s = re.sub(r"\[20[01]~", "", s)
    s = s.strip()
    if len(s) >= 2 and s[0] in ("'", '"', "`") and s[-1] == s[0]:
        s = s[1:-1].strip()
    dropped = len(raw) - len(s)
    if dropped > 0 and key_name:
        try:
            warn(
                f"{key_name} の前後 / 中に {dropped} 文字の非 ASCII 文字 または "
                f"囲みクォートが混入していたため除去しました。"
                f" (.env コピペ時のスマートクォート/全角スペース/日本語混入対策)"
            )
        except Exception:
            pass
    return s, dropped

def ok_box(pairs):
    """各STEPの確認サマリーボックスを表示する"""
    print()
    w = 56
    print(f"  {cyan('┌─ 確認 ' + '─' * (w - 4) + '┐')}")
    for key, val in pairs:
        key_str = dim(str(key).ljust(26))
        val_str = green(str(val))
        print(f"  {cyan('│')}  {key_str} {val_str}")
    print(f"  {cyan('└' + '─' * w + '┘')}")
    print()

class _GoBack(Exception):
    """ウィザードで「ひとつ前のステップに戻る」要求を表す内部例外。
    next_step_pause() が送出し、main() のステップループが捕捉して前STEPへ戻す。"""
    pass


# ★ v1.26: main() が各ステップ実行前に設定。先頭STEP（戻り先なし）では False。
_WIZARD_CAN_GO_BACK = False
_BACK_TOKENS = {"b", "back", "戻る", "もどる"}


def next_step_pause():
    """次のSTEPへ進む前にEnterを待つ。'b' 入力で前のステップへ戻る（v1.26）。"""
    if _WIZARD_CAN_GO_BACK:
        prompt = f"  {dim('次の STEP へ進む: Enter ／ ひとつ前に戻る: b を入力 + Enter : ')}"
    else:
        prompt = f"  {dim('次の STEP へ進む場合は Enter : ')}"
    try:
        ans = input(prompt).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  " + yellow("キャンセルしました。"))
        sys.exit(0)
    if _WIZARD_CAN_GO_BACK and ans in _BACK_TOKENS:
        raise _GoBack()
    print()

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def _load_existing_env():
    if not os.path.exists(ENV_PATH):
        return {}
    values = {}
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                values[k.strip()] = v.strip()
    return values

def _backup_env():
    if os.path.exists(ENV_PATH):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = ENV_PATH + f".backup_{ts}"
        with open(ENV_PATH, encoding="utf-8") as f:
            content = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  {dim(f'既存の .env をバックアップしました: {os.path.basename(backup_path)}')}")
        print()

TOTAL = 14   # ★ v1.21: 11→14（データ収集12・モメンタム13・アラート音14を正式STEP化）

# 既知ETFリスト（STOCK_TICKERS入力時のバリデーション用）
# ★ v1.38: 版数は必ずここを更新する（起動バナー・ヘッダ表示で共用。取り残し防止）
WIZARD_VERSION = "v1.45"

_KNOWN_ETFS = {
    "SPY", "QQQ", "SMH", "SPXL", "SPXS", "TQQQ", "SQQQ", "SOXL", "SOXS",
    "IWM", "DIA", "GLD", "SLV", "TLT", "VTI", "VOO", "VEA", "VWO", "AGG",
    "LQD", "HYG", "XLF", "XLK", "XLE", "XLV", "XLI", "XLB", "XLRE",
    "EEM", "FXI", "EWJ", "GDX", "ARKK", "XBI", "IBB", "UVXY", "VXX",
    "SOXX", "MCHI", "KWEB", "SQQQ", "UPRO", "SPXU",
}

# 発注しない設定の sentinel 値（AI confidence は 0.0〜1.0 なので 2.0 は絶対に超えない）
_DISABLED_CONF = "2.00"

def step1_budget(existing):
    header(1, TOTAL, "💰 STEP 1 ── 予算（BUDGET_USD）")
    print("  最大投資上限額（ドル）を設定します。\n")
    box("目安", [
        "$10,000 未満だと、1回の発注額が小さくなり手数料負けのリスクが大きくなります。",
        "（金額はご自身の資金計画に合わせて設定してください）",
        "実口座（--live）で使う場合は、口座の実際の信用余力の範囲内に設定してください。",
        "余力を超えると、複数銘柄の同時保有時に発注が拒否されます（信用余力不足）。",
    ])
    cur = existing.get("BUDGET_USD", "10000")
    while True:
        val = ask("BUDGET_USD（ドル）", default=cur)
        try:
            v = float(val.replace(",", ""))
            # ★ v1.38: inf / nan / 極端値ガード（int(inf) の OverflowError でクラッシュしないように）
            if math.isfinite(v) and 0 < v <= 1_000_000_000:
                result = str(int(v))
                ok_box([("BUDGET_USD", f"${v:,.0f}")])
                next_step_pause()
                return result
        except (ValueError, OverflowError):
            pass
        warn("正の数値で入力してください（例: 30000）")

def step2_risk(existing, budget):
    header(2, TOTAL, "🛡 STEP 2 ── リスク管理")
    budget_val = float(budget)

    print("  【損切りライン（MAX_LOSS_PCT）】\n")
    print("  ポジション評価額が元値からこの%下落したら自動で損切りします。\n")
    box("目安", [
        "0.30%  標準型（タイト・小さな損失で素早く撤退）← まずここから",
        "0.50%  ゆとりあり（旧 v3.9.45 以前の標準）",
        "1.00%  保守的（損失額は大きくなる）",
    ])
    cur_loss = existing.get("MAX_LOSS_PCT", "0.30")
    while True:
        val = ask("MAX_LOSS_PCT（%）", default=cur_loss)
        try:
            v = float(val)
            if 0 < v <= 10:
                ok(f"-{v:.2f}% でカット")
                max_loss = f"{v:.2f}"
                break
        except ValueError:
            pass
        warn("0〜10 の数値で入力してください（例: 0.50）")

    # ★ v1.7: 高ボラ銘柄の損切り自動調整を明示 (moomoo_trade_v1.py v3.9.32 連動)
    _hv_mult = 2.5
    try:
        _hv = float(max_loss) * _hv_mult
    except ValueError:
        _hv = 0.0
    print()
    box(f"⚙ 自動調整: 値動きの大きい銘柄は損切り幅を {_hv_mult:g} 倍に広げます", [
        f"対象: NVDA / TSLA / AMD / MU / AVGO / SMH / SOXX など値動きの激しい銘柄",
        f"  ・ETF など通常銘柄 : 損切り {max_loss}%（入力値そのまま）",
        f"  ・高ボラ銘柄       : 損切り {_hv:.2f}%（{max_loss}% × {_hv_mult:g}）",
        "",
        "理由: NVDA 等は日中の値動きが大きく、0.5% 損切りでは",
        "      普通のノイズで誤って損切りされてしまうため。",
        "",
        f"同時にポジションサイズを 1/{_hv_mult:g} に縮小するので、",
        "1 トレードあたりの想定最大損失額は ETF と同じ水準に保たれます。",
        "（損切り幅 2.5 倍 × サイズ 1/2.5 倍 = 損失額は変わらない）",
        "",
        "※ この調整はプログラムが自動で行います。設定不要です。",
        "※ 無効化したい場合は .env に STOCK_HIGHVOL_LOSS_MULT=0 を追加。",
    ])

    print()
    print("  【時間切れ決済（TIMEOUT_EXIT_MINUTES）】\n")
    print("  ニュースによる株価変動の鮮度は時間とともに緩やかになる場合が多いため、")
    print("  発注から〇〇分が経過しても保有中の場合に自動で決済します。\n")
    # ★ v1.39: 全期間集計（ニュース系 4,608件）の参考値を表示
    box("参考: 全期間集計での設定値ごとの成績（過去実績・成果は非保証）", [
        "10分設定: 2,473件  勝率51%  合計 +$5,261 ← 最良",
        "30分設定:   667件  勝率49%  合計 −$10,657（明確に劣後）",
        "60分設定:   342件  勝率52%  合計 +$1,551 / 15分設定: 110件 ほぼ±0",
        "時間切れ決済玉の平均: 最大含み益+0.096% → 決済+0.019%",
        "（＝10分の時点でニュースの鮮度はほぼ消えており、長く持つ利点は確認できず）",
    ])
    choices = [
        ("5",  " 5分（短期・ニュース直後のみ）"),
        ("10", "10分（標準型・全期間集計で最良）← まずここから"),
        ("30", "30分（ゆとりあり・過去集計では劣後）"),
        ("60", "60分（長め）"),
        ("0",  " 無効（時間切れ決済しない）"),
    ]
    print(f"  {dim('※ 番号のほか、数字を直接入力すれば任意の分数も設定できます（例: 15 / 範囲 0〜240・0=無効）。')}")
    cur_timeout = existing.get("TIMEOUT_EXIT_MINUTES", "10")
    # ★ v1.38: カスタム分数(例:15)も許容（0〜240分・0=無効）
    timeout = ask_choice("値を入力（Enter=現在値）", choices, default=cur_timeout,
                         custom_range=(0, 240))
    if timeout == "0":
        info("時間切れ決済は無効です。")
    else:
        ok(f"{timeout}分で時間切れ決済")

    timeout_label = "無効" if timeout == "0" else f"{timeout} 分"
    ok_box([
        ("MAX_LOSS_PCT",         f"{max_loss} %"),
        ("TIMEOUT_EXIT_MINUTES", timeout_label),
    ])
    next_step_pause()
    return {"MAX_LOSS_PCT": max_loss, "TIMEOUT_EXIT_MINUTES": timeout}

def _pct_to_percent_str(raw, default_percent_str):
    """★ v3.9.73: 既存 .env の %値を「1=1%」表記の文字列に正規化（半自動移行用）。
    旧小数(0<値<0.05)は ×100 してパーセント表記に変換。新表記(≥0.05)はそのまま。
    空/不正/0以下は default を返す。
    ★ v1.38 補足: しきい値 0.05 が安全な理由 — Wizard の新表記入力は custom_range の
    下限が 0.05 のため、0.05 未満の値を Wizard が新表記で書くことはない（＝0.05 未満は
    旧小数と断定できる）。変換が起きた場合は呼び出し側(STEP3)で内容を表示する。"""
    try:
        v = float(str(raw).strip())
    except (ValueError, TypeError):
        return default_percent_str
    if v <= 0:
        return default_percent_str
    pct = v if v >= 0.05 else v * 100.0   # 旧小数 → パーセントへ
    s = (f"{pct:.4f}").rstrip("0").rstrip(".")
    return s if s else default_percent_str


def step3_trailing(existing):
    header(3, TOTAL, "📈 STEP 3 ── トレイリングストップ")
    print("  利益が出たポジションを守るための自動追跡決済です。\n")
    print("  ① 発動しきい値: 投下額からこの%上昇したらトレール開始")
    print("  ② トレール幅:   最高値からこの%下落したら決済\n")
    box("例（BUDGET $10,000 の場合）", [
        "発動+0.22% → $10,022 に到達したらトレール開始",
        "トレール幅0.15% → 最高値から$15下落で決済",
    ])

    # ★ v3.9.73: 入力は「1=1%（パーセント数値）」に統一。旧 .env(小数 0.003 等)は
    # 読み込み時に ×100 して自動変換し、新表記を既定として提示する(半自動移行)。
    print(f"  {dim('※ 数値は『1 = 1%』表記です（例: 0.22 = 0.22%）。')}\n")
    # ★ v1.38: 標準を 0.30 → 0.22 に変更。全期間バックアップ集計（10,053件）の
    #   最大含み益ベース反実仮想で、0.22 は 全体+$4,152 / 建玉トレール+$2,546 /
    #   モメンタム+$3,958 の改善（0.30比・近似・成果非保証）。0.18 はさらに数字上
    #   良いが、確保利益が 0.03〜0.15% と手数料負け帯に入るため 0.22 を採用。
    trig_choices = [
        ("0.22", "0.22%（新標準・全期間実測で改善）← まずここから"),
        ("0.30", "0.30%（旧標準 v1.10〜v1.37）"),
        ("0.50", "0.50%（やや遅め）"),
        ("1.0",  "1.0%（旧 v3.9.45 以前の標準）"),
    ]
    _raw_trig = str(existing.get("TRAIL_TRIGGER_PCT", "") or "").strip()
    cur_trig = _pct_to_percent_str(_raw_trig, "0.22")
    # ★ v1.38: 旧小数表記から変換した場合は内容を明示（黙って×100しない）
    try:
        if _raw_trig and 0 < float(_raw_trig) < 0.05:
            info(f"旧表記 TRAIL_TRIGGER_PCT={_raw_trig} を {cur_trig}%（1=1%表記）として読み込みました。")
    except ValueError:
        pass
    # ★ v1.38: 旧標準 0.30 のままの方には新標準 0.22 を既定候補として提示
    #   （Enterで新標準へ移行・0.30を続けるなら [2]。カスタム値の方はそのまま維持）
    if cur_trig in ("0.30", "0.3"):
        print(f"  {yellow('※ 現在は旧標準 0.30% です。全期間の実測に基づく新標準 0.22% を既定候補にしています。')}")
        print(f"  {dim('   Enter で 0.22% に更新 / 0.30% を続ける場合は 0.30 を入力してください（成果は非保証）。')}")
        print()
        cur_trig = "0.22"
    print("  【① 発動しきい値】\n")
    trig = ask_choice("値を入力（例 0.25・Enter=現在値）", trig_choices, default=cur_trig, custom_range=(0.05, 5.0))
    ok(f"発動しきい値: +{float(trig):.2f}%")

    drop_choices = [
        ("0.15", "0.15%（標準・利益取りこぼし最小）← まずここから"),
        ("0.30", "0.30%（やや余裕あり）"),
        ("0.50", "0.50%（旧 v3.9.45 以前の標準）"),
        ("1.0",  "1.0%（大きな反転まで保持）"),
    ]
    _raw_drop = str(existing.get("TRAIL_DROP_PCT", "") or "").strip()
    cur_drop = _pct_to_percent_str(_raw_drop, "0.15")
    try:
        if _raw_drop and 0 < float(_raw_drop) < 0.05:
            info(f"旧表記 TRAIL_DROP_PCT={_raw_drop} を {cur_drop}%（1=1%表記）として読み込みました。")
    except ValueError:
        pass
    print("  【② トレール幅】\n")
    drop = ask_choice("値を入力（例 0.25・Enter=現在値）", drop_choices, default=cur_drop, custom_range=(0.05, 5.0))
    ok(f"トレール幅: {float(drop):.2f}%下落で決済")

    ok_box([
        ("TRAIL_TRIGGER_PCT", f"+{float(trig):.2f}%  でトレール開始"),
        ("TRAIL_DROP_PCT",    f"最高値から {float(drop):.2f}% 下落で決済"),
    ])
    next_step_pause()
    return {"TRAIL_TRIGGER_PCT": trig, "TRAIL_DROP_PCT": drop}

def step4_confidence(existing):
    header(4, TOTAL, "🤖 STEP 4 ── AIしきい値（ベース）")
    print("  AIが0.0〜1.0のスコアでニュースを評価します。\n")

    print("  【発注しきい値（STRONG_BUY_CONFIDENCE）】\n")
    box("目安", [
        "0.85  発注かなり少なめ：厳選した場面だけ",
        "0.75  発注少なめ：慎重に絞る",
        "0.70  標準：バランス重視  ← まずここから",
        "0.65  発注多め：反応は増えるが外れも増える",
    ])
    cur_conf = existing.get("STRONG_BUY_CONFIDENCE", "0.70")
    while True:
        val = ask("STRONG_BUY_CONFIDENCE（0.5〜1.0）", default=cur_conf)
        try:
            v = float(val)
            if 0.5 <= v <= 1.0:
                ok(f"発注しきい値: {v:.2f}")
                base_conf = f"{v:.2f}"
                break
        except ValueError:
            pass
        warn("0.5〜1.0 の数値で入力してください（例: 0.70）")

    print()
    print("  【パニック売りしきい値（PANIC_CONFIDENCE）】\n")
    print("  強いネガティブシグナル時にロングを即時全決済するしきい値です。\n")
    info("通常は発注しきい値と同じで問題ありません。Enterでスキップ。")
    cur_panic = existing.get("PANIC_CONFIDENCE", base_conf)
    while True:
        val = ask("PANIC_CONFIDENCE（Enterで発注しきい値と同じ）", default=cur_panic)
        try:
            v = float(val)
            if 0.5 <= v <= 1.0:
                ok(f"パニック売りしきい値: {v:.2f}")
                panic_conf = f"{v:.2f}"
                break
        except ValueError:
            pass
        warn("0.5〜1.0 の数値で入力してください")

    ok_box([
        ("STRONG_BUY_CONFIDENCE", f"{base_conf}  （RTH 通常発注しきい値）"),
        ("PANIC_CONFIDENCE",      f"{panic_conf}  （急変動時しきい値）"),
    ])
    next_step_pause()
    return {"STRONG_BUY_CONFIDENCE": base_conf, "PANIC_CONFIDENCE": panic_conf}

def step5_session(existing, base_conf):
    header(5, TOTAL, "⏰ STEP 5 ── 時間帯別トレード設定")
    base = float(base_conf)
    print(f"  RTH ベースしきい値（STEP 4）: {base_conf}\n")
    print("  各セッションの発注方針を選択します。")
    print("  数値が高いほど発注条件が厳しく、発注頻度が下がります。\n")
    # ★ v1.39: 「発注しない」の実際の動作を明記（Bot v3.9.6 実装済み）
    print(f"  {dim('※ [1] 発注しない を選んだセッション中は、発注だけでなくニュース取得・AI判定も')}")
    print(f"  {dim('   完全に停止します（Anthropic APIの消費ゼロ・次のセッションで自動再開）。')}\n")

    # ── 各セッションの設定値 ──────────────────────────────────────────────
    _sessions = [
        {
            "key":   "CONFIDENCE_PREMARKET",
            "label": "プリマーケット  04:00〜09:30 ET",
            "note":  "流動性: 中程度 ／ スプレッド: やや広め",
            "vals":  {
                "disabled":     _DISABLED_CONF,
                "conservative": f"{min(round(base + 0.13, 2), 0.99):.2f}",
                "standard":     f"{min(round(base + 0.07, 2), 0.98):.2f}",
                "aggressive":   f"{base:.2f}",
            },
            "default_mode": "disabled",
        },
        {
            "key":   "CONFIDENCE_AFTERHOURS",
            "label": "アフターアワーズ  16:00〜20:00 ET",
            "note":  "流動性: 低 ／ スプレッド: 広め",
            "vals":  {
                "disabled":     _DISABLED_CONF,
                "conservative": f"{min(round(base + 0.17, 2), 0.99):.2f}",
                "standard":     f"{min(round(base + 0.13, 2), 0.98):.2f}",
                "aggressive":   f"{min(round(base + 0.07, 2), 0.97):.2f}",
            },
            "default_mode": "disabled",
        },
        {
            "key":   "CONFIDENCE_OVERNIGHT",
            "label": "オーバーナイト  20:00〜翌04:00 ET",
            "note":  "流動性: 最低 ／ スプレッドかなり広い（不利）",
            "vals":  {
                "disabled":     _DISABLED_CONF,
                "conservative": f"{min(round(base + 0.20, 2), 0.99):.2f}",
                "standard":     f"{min(round(base + 0.15, 2), 0.98):.2f}",
                "aggressive":   f"{min(round(base + 0.10, 2), 0.97):.2f}",
            },
            "default_mode": "disabled",
        },
    ]

    def _detect_mode(cur_val, vals):
        """既存値からモードを推定する。プリセット外・非数値は 'custom'（維持可能）。

        ★ v1.30: 従来はカスタム値/ベース変更後の旧値/非数値で None を返し、
          Enter「維持」のつもりが defmode（発注しない=2.00）へ黙って置換されていた。
          非数値既存値では float() が未捕捉でウィザードがクラッシュしていた。"""
        if not cur_val or cur_val == "":
            return None
        if cur_val == _DISABLED_CONF:
            return "disabled"
        try:
            fv = float(cur_val)
        except (ValueError, TypeError):
            return "custom"   # 非数値でもクラッシュせず「維持」を選べるように
        for mode, v in vals.items():
            try:
                if abs(fv - float(v)) < 0.005:
                    return mode
            except (ValueError, TypeError):
                continue
        return "custom"  # プリセット外のカスタム値

    result = {}
    disabled_sessions = []  # 「発注しない」を選んだセッション名

    for sess in _sessions:
        key    = sess["key"]
        label  = sess["label"]
        note   = sess["note"]
        vals   = sess["vals"]
        defmode = sess["default_mode"]

        cur_val  = existing.get(key, "")
        cur_mode = _detect_mode(cur_val, vals) if cur_val else defmode

        print(f"  {cyan('─'*54)}")
        print(f"  {bold(label)}")
        print(f"  {dim(note)}\n")

        choices_display = [
            ("disabled",     f"発注しない          （このセッションは完全停止）"),
            ("conservative", f"慎重  {vals['conservative']}   重要ニュースのみ"),
            ("standard",     f"標準  {vals['standard']}   スプレッドを考慮した水準"),
            ("aggressive",   f"積極  {vals['aggressive']}   RTHと同じ条件で発注"),
        ]

        # 表示
        mode_keys = ["disabled", "conservative", "standard", "aggressive"]
        for i, (mkey, desc) in enumerate(choices_display, 1):
            marker = green("▶") if mkey == cur_mode else " "
            # 発注しないは赤で強調
            if mkey == "disabled":
                print(f"  {marker} [{i}] {red(desc.split('（')[0].strip())}  {dim('（' + desc.split('（')[1])}")
            else:
                print(f"  {marker} [{i}] {desc}")
        # ★ v1.30: プリセット外のカスタム値は Enter で維持できることを明示
        if cur_mode == "custom":
            print(f"  {green('▶')} [Enter] 現在のカスタム値 {cur_val} を維持")
        print()

        # 入力ループ
        while True:
            raw = ask("番号を選択（Enter=現在値を維持）", default="")
            if raw == "":
                # Enter: 現在値維持
                chosen_mode = cur_mode if cur_mode else defmode
                break
            if raw in ("1", "2", "3", "4"):
                chosen_mode = mode_keys[int(raw) - 1]
                break
            warn("1〜4 の番号を入力してください")

        short_name = label.split("  ")[0]
        # ★ v1.30: カスタム値の Enter 維持。従来はプリセット外の値が defmode
        #   （発注しない=2.00）へ黙って置換されていた。既存値をそのまま保存する。
        if chosen_mode == "custom":
            result[key] = str(cur_val)
            try:
                if float(cur_val) >= 2.0:
                    disabled_sessions.append(short_name)
                    ok(f"{short_name}: 発注しない（現在値 {cur_val} を維持）")
                else:
                    ok(f"{short_name}: カスタム値を維持（{cur_val}）")
            except (ValueError, TypeError):
                ok(f"{short_name}: 現在値を維持（{cur_val}）")
            print()
            continue
        result[key] = vals[chosen_mode]
        if chosen_mode == "disabled":
            ok(f"{short_name}: 発注しない")
            disabled_sessions.append(short_name)
        else:
            label_map = {
                "conservative": "慎重",
                "standard":     "標準",
                "aggressive":   "積極",
            }
            ok(f"{short_name}: {label_map[chosen_mode]}（{result[key]}）")
        print()

    # ── 移行前全決済 ────────────────────────────────────────────────────
    if disabled_sessions:
        print(f"  {red('⚡')} {bold('移行前全決済')}")
        print(f"  {dim('発注しない設定のセッションに切り替わる5分前に全ポジション決済します。')}")
        # ★ v1.39: 「5分前」は Bot 既定 (CLOSE_BEFORE_INACTIVE_MIN=5) と一致。変更方法を明記。
        print(f"  {dim('（既定は5分前。変えたい場合は .env に CLOSE_BEFORE_INACTIVE_MIN=15 のように 1〜60 で指定）')}\n")
        cur_close = existing.get("CLOSE_BEFORE_INACTIVE", "true").lower()
        close_yn = ask_yn("移行前全決済を有効にしますか？", default=(cur_close != "false"))
        result["CLOSE_BEFORE_INACTIVE"] = "true" if close_yn else "false"
        if close_yn:
            ok("移行前全決済: ON（セッション切り替え5分前に全決済）")
        else:
            info("移行前全決済: OFF（ポジションを保持したまま移行）")
    else:
        result["CLOSE_BEFORE_INACTIVE"] = existing.get("CLOSE_BEFORE_INACTIVE", "false")

    # RTHはベースと同じ（変更しない）
    result["CONFIDENCE_RTH"] = existing.get("CONFIDENCE_RTH", "")

    def _sess_disp(v):
        if not v or v == "":   return "ベースと同じ"
        try:
            return "発注しない" if float(v) >= 2.0 else v
        except ValueError:
            return v

    ok_box([
        ("プリマーケット",   _sess_disp(result.get("CONFIDENCE_PREMARKET", ""))),
        ("アフターアワーズ", _sess_disp(result.get("CONFIDENCE_AFTERHOURS", ""))),
        ("オーバーナイト",   _sess_disp(result.get("CONFIDENCE_OVERNIGHT", ""))),
        ("移行前全決済",
            ("ON" if result.get("CLOSE_BEFORE_INACTIVE") == "true" else "OFF")
            if disabled_sessions else "—（発注しないセッションなし）"),
    ])
    next_step_pause()
    return result

def _fmt_momentum_sides(raw):
    """MOMENTUM_ENABLED_SIDES を『SPY-売 / QQQ-売買 / IWM-売』形式に整形して返す。"""
    pairs = [p.strip().upper() for p in (raw or "").split(",") if ":" in p]
    bysym = {}
    for p in pairs:
        sym, side = p.split(":", 1)
        bysym.setdefault(sym, set()).add(side)
    if not bysym:
        return "（なし・モメンタム実発注なし）"
    order = ["SPY", "QQQ", "SMH", "IWM", "DRAM"]
    syms = [s for s in order if s in bysym] + [s for s in bysym if s not in order]
    out = []
    for sym in syms:
        s = bysym[sym]
        lbl = "売買" if ("BUY" in s and "SELL_SHORT" in s) else ("買" if "BUY" in s else "売")
        out.append(f"{sym}-{lbl}")
    return " / ".join(out)


def step6_symbols(existing):
    header(6, TOTAL, "📊 STEP 6 ── 売買銘柄の選択（ニュース駆動）")
    print("  ここで選ぶのは【ニュース駆動（AIニュース）】の対象ETFです。買い・空売りの両方に対応します。")
    print(f"  {dim('※ モメンタム戦略の実発注銘柄は STEP 13「モメンタム発注設定」の[2-c]で別に選びます（別系統）。')}")
    print(f"  {dim('  現在のモメンタム実発注: ' + _fmt_momentum_sides(existing.get('MOMENTUM_ENABLED_SIDES', '')))}\n")

    # ── プリセット選択 ────────────────────────────────────────────────────
    presets = [
        ("SPY",         "SPY のみ",          "値動きが比較的安定。リスクを抑えたい場合に。"),
        ("SPY,QQQ",     "SPY ＋ QQQ",        "S&P500とNASDAQをカバー。標準的な設定。"),
        ("SPY,QQQ,SMH", "SPY ＋ QQQ ＋ SMH", "半導体も加える。損益の振れ幅が大きくなります。"),
    ]

    cur_tickers = existing.get("TRIGGER_TICKERS", "SPY,QQQ")
    # 現在値からプリセットを推定
    cur_preset = "SPY,QQQ"  # fallback
    for key, _, __ in presets:
        if set(cur_tickers.split(",")) == set(key.split(",")):
            cur_preset = key
            break

    for i, (key, label, detail) in enumerate(presets, 1):
        marker = green("▶") if key == cur_preset else " "
        if key == "SPY,QQQ,SMH":
            print(f"  {marker} [{i}] {yellow(label)}  {dim(detail)}")
        else:
            print(f"  {marker} [{i}] {bold(label)}  {dim(detail)}")
    print()
    info("（Enter = 現在値を維持）")

    default_idx = next((str(i) for i, (k, _l, _d) in enumerate(presets, 1) if k == cur_preset), "2")
    while True:
        raw = ask("番号を選択", default=default_idx)
        if raw in ("1", "2", "3"):
            chosen_key = presets[int(raw) - 1][0]
            break
        warn("1〜3 の番号を入力してください")

    tickers_list = [t.strip() for t in chosen_key.split(",")]
    tickers_str  = ",".join(tickers_list)
    ok(f"メイン銘柄: {tickers_str}（各ロング ／ ショート）")
    print()

    # ── 個別株追加 ────────────────────────────────────────────────────────
    print(f"  {bold('【個別株の追加】')}  {dim('任意・ETF不可・個別株のみ')}")
    print(f"  {dim('Finnhubのその銘柄固有ニュースを30秒間隔で取得してAI判定・直接売買します。')}")
    print(f"  {dim('例: NVDA → NVIDIAの決算・自社ニュースが出たときだけ発注')}\n")
    print(f"  {red('⚠  ETFティッカーは設定できません（例: SPXL, SOXL など）')}\n")

    cur_stock = existing.get("STOCK_TICKERS", "")
    if cur_stock:
        print(f"  {dim(f'現在値: {cur_stock}')}\n")

    while True:
        stock_raw = ask(
            "個別株ティッカー（カンマ区切り / Enter=現在値を維持）",
            default=cur_stock,
            allow_clear=True,
        )
        if not stock_raw:
            stock_str = ""
            if cur_stock:
                info("個別株監視をクリアしました。")
            else:
                info("個別株追加: なし")
            break

        # ETFバリデーション
        input_list  = [t.strip().upper() for t in stock_raw.split(",") if t.strip()]
        etf_found   = [t for t in input_list if t in _KNOWN_ETFS]
        valid_stocks = [t for t in input_list if t not in _KNOWN_ETFS]

        if etf_found:
            warn(f"ETFが含まれています（設定不可）: {', '.join(etf_found)}")
            if valid_stocks:
                print(f"  {dim(f'個別株として有効: {chr(44).join(valid_stocks)}')}\n")
                use_valid = ask_yn(f"ETFを除いた {', '.join(valid_stocks)} のみで設定しますか？", default=True)
                if use_valid:
                    stock_str = ",".join(valid_stocks)
                    ok(f"個別銘柄監視: {stock_str}")
                    break
            # ETFのみ or キャンセル → 再入力
            continue
        else:
            stock_str = ",".join(valid_stocks)
            ok(f"個別銘柄監視: {stock_str}")
            break

    ok_box([
        ("プリセット",   tickers_str),
        ("個別株追加",   stock_str if stock_str else "なし"),
    ])
    next_step_pause()
    return {
        "TRIGGER_TICKERS":     tickers_str,
        "TRIGGER_TICKERS_STR": tickers_str,
        "STOCK_TICKERS":       stock_str,
    }

def step7_order_detail(existing):
    header(7, TOTAL, "⚙️  STEP 7 ── 発注詳細設定")
    print("  上級者向け設定です。Enterですべてデフォルト値でスキップできます。\n")
    result = {}

    print("  【指値バッファ（LIMIT_BUFFER_PCT）】\n")
    print("  発注時に気配値から何%離れた指値を出すかです。\n")
    # ★ v1.39: バッファの意味と新標準を説明。
    #   従来のWizard既定 1.0% は単一値で Bot 内蔵の「ETF 0.30% / 個別株 0.50%」の
    #   使い分け（v2.99.4）を上書きしてしまい、広すぎた。新標準はキーを未設定にして
    #   この使い分けをそのまま使う。
    box("バッファの意味", [
        "指値は「最悪ここまで許容する上限」です。通常は気配値付近で約定するため、",
        "広くしてもその分を毎回払うわけではありません。ただし急変時はバッファ上限",
        "まで滑って約定し得るため、広すぎる設定は不利です。",
        "狭すぎると急変時に未約定→1分キャンセルで機会を逃します（ORDER_CANCEL_MINUTES）。",
    ])
    print(f"  {dim('※ 数値は『1 = 1%』表記です（例: 0.5 = 0.5%）。番号のほか数値の直接入力も可（0.05〜5.0）。')}\n")
    buf_choices = [
        ("auto", "ETF 0.30% / 個別株 0.50%（銘柄タイプで使い分け・新標準）← まずここから"),
        ("0.30", "0.30% 全銘柄一律（タイト・急変時は未約定が増える可能性）"),
        ("0.50", "0.50% 全銘柄一律"),
        ("1.0",  "1.0% 全銘柄一律（旧デフォルト・広め）"),
    ]
    _raw_buf = str(existing.get("LIMIT_BUFFER_PCT", "") or "").strip()
    _cur_buf = _pct_to_percent_str(_raw_buf, "auto") if _raw_buf else "auto"
    # ★ v1.39: 旧デフォルト 1.0% のままの方には新標準「自動」を既定候補として提示
    #   （Enterで自動へ移行・1.0%を続けるなら [4]。カスタム値の方はそのまま維持）
    if _cur_buf in ("1", "1.0"):
        print(f"  {yellow('※ 現在は旧デフォルト 1.0% です。新標準「ETF 0.30% / 個別株 0.50%」を既定候補にしています。')}")
        print(f"  {dim('   Enter で新標準へ更新 / 1.0% を続ける場合は 1.0 を入力してください。')}")
        print()
        _cur_buf = "auto"
    buf = ask_choice("値を入力（Enter=現在値を維持）", buf_choices,
                     default=_cur_buf, custom_range=(0.05, 5.0))
    if buf == "auto":
        ok("指値バッファ: ETF 0.30% / 個別株 0.50%（銘柄タイプで使い分け）")
        result["LIMIT_BUFFER_PCT"] = ""   # 未設定＝Bot 内蔵の ETF 0.30% / 個別株 0.50% を使用
    else:
        ok(f"指値バッファ: {float(buf):.2f}%（全銘柄一律・ETF/個別株の使い分けなし）")
        result["LIMIT_BUFFER_PCT"] = buf

    print()
    print("  【未約定キャンセル時間（ORDER_CANCEL_MINUTES）】\n")
    print("  発注から指定分経過しても約定しない注文をキャンセルします。\n")
    cancel_choices = [
        ("1", " 1分（ニュース系・素早く撤退）← デフォルト"),
        ("2", " 2分（少し待つ）"),
        ("5", " 5分（ゆっくり約定を待つ）"),
    ]
    cancel = ask_choice("番号を選択（Enter=現在値を維持）", cancel_choices,
                        default=existing.get("ORDER_CANCEL_MINUTES", "1"))
    ok(f"未約定キャンセル: {cancel}分")
    result["ORDER_CANCEL_MINUTES"] = cancel

    # ★ v1.5 (v3.9.20): ピラミッディング設定を撤去。
    # 1,293 件の実運用記録で一度も発動していなかったため。
    # 発注金額は moomoo_trade_v1.py の calc_order_size() で
    # confidence に応じた「山型サイズ配分」が適用される:
    #   0.60-0.69: BUDGET × 30%  (弱シグナル)
    #   0.70-0.77: BUDGET × 60%  (主力帯)
    #   0.78-0.82: BUDGET × 100% (★スイートスポット)
    #   0.83以上:  BUDGET × 40%  (超強気・過剰反応リスク管理)
    print()
    print(f"  {dim('【発注サイズ】')}")
    print(f"  {dim('confidence に応じた「山型配分」が自動適用されます (v3.9.20):')}")
    print(f"  {dim('  0.60-0.69: 予算×30% (弱シグナル)')}")
    print(f"  {dim('  0.70-0.77: 予算×60% (主力帯)')}")
    print(f"  {dim('  0.78-0.82: 予算×100% ★スイートスポット')}")
    print(f"  {dim('  0.83以上:  予算×40% (超強気・過剰反応リスク管理)')}")
    print(f"  {dim('過去 1,293 件の分析で勝率と効率がピークとなる帯を最大化する設計です。')}")
    print()

    _buf_val = result.get("LIMIT_BUFFER_PCT", "")
    _buf_disp = (f"{float(_buf_val):.2f} %（全銘柄一律）" if _buf_val
                 else "ETF 0.30% / 個別株 0.50%（使い分け）")   # ★ v1.39
    ok_box([
        ("LIMIT_BUFFER_PCT",        _buf_disp),
        ("ORDER_CANCEL_MINUTES",    f"{result.get('ORDER_CANCEL_MINUTES','1')} 分"),
    ])
    next_step_pause()
    return result

def step8_anthropic(existing):
    header(8, TOTAL, "🔑 STEP 8 ── Anthropic APIキー（必須）")
    print("  Claude AIでニュースを判断するために必須です。\n")
    info("console.anthropic.com → API Keys → Create Key")
    cur = existing.get("ANTHROPIC_API_KEY", "")

    if cur:
        # 既存キーがある場合: マスク表示して維持 or 再入力を選択
        print(f"  現在のキー: {_mask_key(cur)}\n")
        keep = ask_yn("このキーを維持しますか？（N を入力すると再入力）", default=True)
        if keep:
            ok("Anthropic APIキー: 維持")
            ok_box([("ANTHROPIC_API_KEY", _mask_key(cur))])
            next_step_pause()
            return cur

    # 新規入力 or 再入力
    print(f"  {dim('APIキーは sk-ant-api03- から始まります。')}\n")
    while True:
        # ★ v1.3: getpass.getpass() を ask(secret=True) に統一（マスク表示対応）
        val = ask("ANTHROPIC_API_KEY", secret=True, default="").strip()
        if not val:
            if cur:
                info("変更をキャンセルし、既存のキーを維持します。")
                ok_box([("ANTHROPIC_API_KEY", _mask_key(cur))])
                next_step_pause()
                return cur
            warn("Anthropic APIキーは必須です。")
            continue
        if val.startswith("sk-ant-"):
            ok("Anthropic APIキー設定済み")
            ok_box([("ANTHROPIC_API_KEY", _mask_key(val))])
            next_step_pause()
            return val
        warn("APIキーは 'sk-ant-' から始まる形式です。コピー元を確認してください。")

def step9_alpaca(existing):
    header(9, TOTAL, "📡 STEP 9 ── Alpaca News API（任意）")
    print("  設定すると Benzinga のリアルタイムニュースが追加されます。")
    print("  設定しない場合は RSS のみで動作します。\n")
    box("取得方法", [
        "1. https://alpaca.markets でアカウント作成（無料）",
        "2. Paper Trading / Live どちらでもOK",
        "3. 「API Keys」メニューから Key ID と Secret Key を取得",
    ])

    result = {}

    cur_id  = existing.get("ALPACA_API_KEY_ID", "")
    cur_sec = existing.get("ALPACA_API_SECRET_KEY", "")

    # ★ v1.3: allow_clear=True でクリア機能を有効化（"-" 入力で空文字を返す）
    # ★ v1.8: secret=True でキー本体を画面に表示しない（漏洩防止）
    if cur_id:
        print(f"  現在の Key ID: {_mask_key(cur_id)}\n")
    val_id = ask("ALPACA_API_KEY_ID（Enter=維持）",
                 default=cur_id, secret=True, allow_clear=True)
    val_id = val_id.strip()
    if val_id:
        # 通常パス: 新規入力 or 既存値（Enter で維持）
        result["ALPACA_API_KEY_ID"] = val_id
        val_sec = ask("ALPACA_API_SECRET_KEY", secret=True, default=cur_sec)
        result["ALPACA_API_SECRET_KEY"] = val_sec.strip() or cur_sec
        ok("Alpaca APIキー 設定済み")
    elif cur_id:
        # ★ v1.3: 明示的にクリアされた（cur_id があったのに val_id が空 = "-" 入力）
        # ID クリア時はペアの SECRET も自動クリアする
        result["ALPACA_API_KEY_ID"]     = ""
        result["ALPACA_API_SECRET_KEY"] = ""
        info("Alpaca APIキーをクリアしました（RSS のみで動作します）")
    else:
        # 既存値なし & 入力なし → 何もしない
        result["ALPACA_API_KEY_ID"]     = ""
        result["ALPACA_API_SECRET_KEY"] = ""
        info("スキップしました。")

    ok_box([
        ("ALPACA_API_KEY_ID",     _mask_key(result["ALPACA_API_KEY_ID"])     if result["ALPACA_API_KEY_ID"]     else dim("未設定（任意）")),
        ("ALPACA_API_SECRET_KEY", _mask_key(result["ALPACA_API_SECRET_KEY"]) if result["ALPACA_API_SECRET_KEY"] else dim("未設定")),
    ])
    next_step_pause()
    return result


def step10_finnhub(existing):
    header(10, TOTAL, "📰 STEP 10 ── Finnhub API（ニュース）＋ Discord 通知（任意）")
    print("  Finnhub を設定するとリアルタイムニュースが追加されます。")
    print("  無料プランで利用可能。標準のニュースソースとして利用できます。\n")
    info("finnhub.io → 無料登録 → Dashboard に API Key が表示されます。")

    cur = existing.get("FINNHUB_API_KEY", "")
    # ★ v1.3: allow_clear=True でクリア機能を有効化
    # ★ v1.8: secret=True でキー本体を画面に表示しない（漏洩防止）
    if cur:
        print(f"  現在のキー: {_mask_key(cur)}\n")
    val = ask("FINNHUB_API_KEY（Enter=維持）",
              default=cur, secret=True, allow_clear=True)
    val = val.strip()

    if val:
        # 通常パス: 新規入力 or 既存値（Enter で維持）
        finnhub_key = val
        ok("Finnhub 設定済み")
    elif cur:
        # ★ v1.3: 明示クリア
        finnhub_key = ""
        info("Finnhub APIキーをクリアしました")
    else:
        # 既存値なし & 入力なし
        finnhub_key = ""
        info("スキップしました。")

    result = {"FINNHUB_API_KEY": finnhub_key}

    # ── Discord Webhook（任意・通知）──────────────────────
    # ★ v1.25: Discord をウィザードから設定可能に（従来の手動記入のみを廃止）。
    #          Webhook URL は機密扱い → secret 入力＋一部マスク表示。
    print()
    print("  " + cyan("── Discord 通知（任意）" + "─" * 28))
    print("  重大エラーや約定などの通知を Discord に送れます（設定は任意）。")
    info("Discordサーバー → サーバー設定 → 連携サービス → ウェブフック → "
         "「新しいウェブフック」→ ウェブフックURLをコピー。")

    dcur = existing.get("DISCORD_WEBHOOK_URL", "")
    if dcur:
        print(f"  現在のURL: {_mask_key(dcur)}\n")
    dval = ask("DISCORD_WEBHOOK_URL（Enter=維持）",
               default=dcur, secret=True, allow_clear=True)
    dval, _ = _sanitize_api_key(dval, "DISCORD_WEBHOOK_URL")

    if dval:
        # 形式が違っても保存はする（確認画面 step_review_warnings でも再チェックされる）
        if not _is_discord_webhook(dval):
            warn("URLの形式が正しくない可能性があります"
                 "（正しくは https://discord.com/api/webhooks/ で始まります）。"
                 "このまま保存しますが、後で確認してください。")
        discord_url = dval
        ok("Discord 通知 設定済み")
    elif dcur:
        discord_url = ""
        info("Discord Webhook をクリアしました")
    else:
        discord_url = ""
        info("Discord 通知はスキップしました。")

    result["DISCORD_WEBHOOK_URL"] = discord_url

    ok_box([
        ("FINNHUB_API_KEY", _mask_key(finnhub_key) if finnhub_key else dim("未設定（任意）")),
        ("DISCORD_WEBHOOK_URL", _mask_key(discord_url) if discord_url else dim("未設定（任意）")),
    ])
    next_step_pause()
    return result

# ── ★ v1.24: acc_id のマスク表示（画面共有/スクショでの口座ID流出を防ぐ）──
def _mask_acc(v):
    s = str(v or "").strip()
    if not s:
        return ""
    if len(s) <= 6:
        return "****"
    return s[:4] + "*" * 4 + s[-2:]


# ── ★ v1.27: OpenD の到達性を短時間で確認（SDK生成前のTCPプローブ）──
def _opend_port_open(host, port, timeout=2.0):
    """OpenD が host:port で待ち受けているかを短時間で確認する。

    OpenD 未起動のまま OpenSecTradeContext を生成すると、moomoo SDK が
    ECONNREFUSED で数回リトライ（conn=0(1)→(2)…）しながらログを吐き続け、
    その間にマスク入力プロンプトが始まって画面・入力が乱れる。これを避けるため、
    SDK に触れる前に素のソケットで到達性だけを即座に確認する。"""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


# ── ★ v1.24: 実口座(--live)用 acc_id の自動取得（OpenD起動時のみ・best-effort）──
def _detect_real_acc_ids(host, port):
    """OpenD から実口座(REAL)の acc_id 一覧を best-effort 取得。
    返り値: [(acc_id:int, acc_type:str), ...] / 失敗時は []（OpenD未起動・未ログイン等）。"""
    # ★ v1.27: OpenD 未起動なら SDK を生成せず即座に失敗（再試行ログの汚染・ハングを防ぐ）。
    if not _opend_port_open(host, port):
        return []
    # ★ v1.39: moomoo SDK の内部ログ（New connect ready / on_disconnect 等）は受講生に
    #   不要なため、取得中は logging を全面的に抑制する。close() 後の切断ログは別スレッド
    #   から少し遅れて出るため、復帰前に短い待ちを挟む。
    import logging as _logging
    import time as _time
    _logging.disable(_logging.CRITICAL)
    try:
        try:
            from moomoo import OpenSecTradeContext, TrdMarket, SecurityFirm, RET_OK  # type: ignore
        except Exception:
            from futu import OpenSecTradeContext, TrdMarket, SecurityFirm, RET_OK    # type: ignore
        ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.US,
                                  security_firm=SecurityFirm.FUTUJP,
                                  host=host, port=int(port))
        try:
            ret, data = ctx.get_acc_list()
        finally:
            try: ctx.close()
            except Exception: pass
        if ret != RET_OK:
            return []
        out = []
        for _, row in data.iterrows():
            try:
                if "REAL" in str(row.get("trd_env", "")):
                    out.append((int(row["acc_id"]), str(row.get("acc_type", ""))))
            except Exception:
                continue
        return out
    except Exception:
        return []
    finally:
        _time.sleep(0.4)                  # 遅延して届く on_disconnect ログを抑制窓内で吸収
        _logging.disable(_logging.NOTSET)


def _setup_real_acc_id(host, port, cur_acc):
    """実口座 acc_id を OpenD から自動取得して返す（数値文字列 or 既存値）。

    ★ v1.28: 手動入力は廃止。受講生は acc_id を手動で調べる手段を持たないため、
             取得は OpenD からの自動取得に一本化する。取得できない場合は
             「OpenD を起動して再試行」または「いまは設定しない（デモのみ／既存維持）」。
    （_detect_real_acc_ids は内部のTCPプローブで未起動時は即・無汚染で失敗する）"""
    while True:
        print()
        info("OpenD へ接続して実口座の一覧を取得しています…")
        accs = _detect_real_acc_ids(host, port)
        if accs:
            print()
            print(f"  {bold('実口座（REAL）が見つかりました：')}")
            for i, (aid, atype) in enumerate(accs, 1):
                print(f"    [{i}] acc_id={green(_mask_acc(aid))}  種別={atype}")
            print(f"    {dim('※ このBotは「信用取引（MARGIN）」の口座を選んでください。')}")
            # ★ v1.24: 選択ループ。MARGIN(信用)以外は警告＋再確認。
            while True:
                pick = ask("使用する口座の番号", default="1")
                try:
                    idx = int(pick) - 1
                except ValueError:
                    warn("番号で入力してください。"); continue
                if not (0 <= idx < len(accs)):
                    warn("一覧の範囲外の番号です。"); continue
                aid, atype = accs[idx]
                if "MARGIN" not in str(atype).upper():
                    print()
                    warn(f"⚠ 選んだ口座の種別は「{atype}」です（信用＝MARGIN ではありません）。")
                    warn("　このBotは『信用取引口座（米国株の信用・ショート）』を前提に設計されています。")
                    warn("　CASH（現物）や DERIVATIVES（デリバティブ）では正しく動作しない可能性があります。")
                    if not ask_yn("それでもこの口座を使いますか？", default=False):
                        info("別の口座を選び直してください。")
                        continue
                acc_id = str(aid)
                ok(f"自動取得：MOOMOO_ACC_ID = {_mask_acc(acc_id)} に設定（種別={atype}）")
                # ★ v1.31: 実口座利用時の BUDGET_USD 注意（余力超過による発注拒否の予防）
                info("実口座で使う場合、BUDGET_USD は口座の実際の信用余力の範囲内にしてください。")
                info("余力を超えていると、複数銘柄の同時保有時に『信用余力不足』で発注が拒否されます。")
                return acc_id

        # ── 取得失敗（OpenD未起動／実口座に未ログイン等）──
        print()
        warn("実口座の一覧を取得できませんでした（OpenD未起動／実口座に未ログイン等）。")
        info("OpenD を起動し、moomoo の実口座にログイン（「Connected」表示）してから再試行してください。")
        print(f"    {bold('[1]')} 再試行（OpenD を起動・実口座にログインしてから）")
        print(f"    {bold('[2]')} いまは設定しない（デモのみ／既存値を保持）")
        retry = ask("番号を選択", default="1")
        if retry == "2":
            info("実口座IDは設定しません（デモのみ／既存値があれば保持）。")
            return cur_acc
        # それ以外（"1" 含む）→ 再試行
        continue


def step11_connection(existing):
    header(11, TOTAL, "🔌 STEP 11 ── moomoo OpenD 接続設定")
    print("  通常はそのまま Enter 2回でOKです。\n")
    info("OpenD はローカルPC上で動作します（127.0.0.1:11111 がデフォルト）。")
    info("取引ロックが発生した場合は、moomooアプリで手動でアンロックしてください。")
    cur_host = existing.get("MOOMOO_HOST", "127.0.0.1")
    cur_port = existing.get("MOOMOO_PORT", "11111")
    host = ask("MOOMOO_HOST", default=cur_host) or cur_host
    # ★ v1.30: PORT を検証（数値・1〜65535）。無検証保存だとボット本体が
    #   モジュール読込時の int() で即トレースバック死するため、ここで弾く。
    while True:
        port = ask("MOOMOO_PORT", default=cur_port) or cur_port
        port = str(port).strip()
        if port.isdigit() and 1 <= int(port) <= 65535:
            break
        warn(f"MOOMOO_PORT が不正です（{port!r}）。1〜65535 の数値で入力してください（既定 11111）。")
    ok(f"接続先: {host}:{port}")

    # ── ★ v1.24: 実口座（--live）用 acc_id 設定。デモのみなら不要・スキップ可 ──
    print()
    print(f"  {bold('実口座（--live）で取引しますか？')}")
    print(f"  {dim('デモ（シミュレーション）だけで使う方は「いいえ」でOK（後でWizard再実行で設定できます）。')}")
    cur_acc = existing.get("MOOMOO_ACC_ID", "").strip()
    if cur_acc:
        info(f"現在の MOOMOO_ACC_ID: {_mask_acc(cur_acc)}（実口座IDは設定済み）")
    use_live = ask_yn("実口座を使う（MOOMOO_ACC_ID を設定する）", default=bool(cur_acc))
    if use_live:
        acc_id = _setup_real_acc_id(host, port, cur_acc)
    else:
        info("デモのみ。MOOMOO_ACC_ID は設定しません（--live は使えません／既存値があれば保持）。")
        acc_id = cur_acc

    ok_box([
        ("MOOMOO_HOST", host),
        ("MOOMOO_PORT", port),
        ("MOOMOO_ACC_ID", _mask_acc(acc_id) if acc_id else "（未設定＝デモのみ）"),
    ])
    next_step_pause()
    return {"MOOMOO_HOST": host, "MOOMOO_PORT": port, "MOOMOO_ACC_ID": acc_id}


def step_data_collect(existing):
    header(12, TOTAL, "📊 STEP 12 ── 取引データ収集への参加（任意）")

    print(f"  {bold('目的')}")
    print(f"  {dim('AIしきい値・時間帯・損切り幅などのルール改善に活用します。')}")
    print(f"  {dim('個人の成績評価には使用しません。')}")
    print()

    print(f"  {bold('送信されるデータ')}  {dim('（送信タイミングは項目により異なります）')}")
    for line in [
        "個別トレードの銘柄・約定価格・保有時間・損益（決済ごと）",
        "未発注シグナルの記録＝シャドー観察：「もし注文していたら」の理論損益（60分保有）・見送り理由（セッション中にまとめて送信）",
        "AI判定スコア・信頼度・ニュースカテゴリ・ニュースソース",
        "AI判定対象のニュース見出し（先頭1件・最大200字）",
        "Botバージョン・設定値（しきい値・ロット・損切りライン等）",
        "1日の集計：発注回数・確定損益・時間帯別勝率（1日1回・EODクローズ後）",
    ]:
        print(f"  {green('✓')} {dim(line)}")
    print()
    print(f"  {dim('※ 送信は少量ずつまとめて行い、集計サーバーの負荷を抑えています。')}")
    print(f"  {dim('※ 収集項目は改善に必要なものへ随時最適化されます（送受信の詳細はBotの変更履歴に記載）。')}")
    print()

    print(f"  {bold('送信されないデータ')}")
    for line in [
        "APIキー・口座番号・パスワード",
        "氏名・住所等の個人情報",
        "ニュース記事の本文全文",
    ]:
        print(f"  {red('✗')} {dim(line)}")
    print()

    print(f"  {dim('送信先: 講師・サポーターのみ閲覧 / 第三者提供なし')}")
    print(f"  {dim('取り消し: Wizardを再実行して「参加しない」を選択')}")
    print()
    print(f"  {yellow('参加は任意です。Botの動作に影響はありません。')}")
    print()

    cur_collect = existing.get("DATA_COLLECT", "").lower()
    cur_name    = existing.get("STUDENT_NAME", "")

    join = ask_yn("上記を確認しました。データ収集に参加しますか？",
                  default=(cur_collect == "true"))

    if join:
        print()
        print(f"  {dim('集計表に表示される名前を入力してください（ニックネーム可）。')}")
        name = ask("表示名", default=cur_name)
        if not name:
            name = cur_name or "匿名"
        print()
        ok(f"参加登録完了: {name}  （取り消しはWizardを再実行）")
        ok_box([("DATA_COLLECT", "参加する"), ("STUDENT_NAME", name)])
        next_step_pause()
        return {"DATA_COLLECT": "true", "STUDENT_NAME": name}
    else:
        print()
        info("参加しないを選択しました。データは送信されません。")
        ok_box([("DATA_COLLECT", "参加しない")])
        next_step_pause()
        return {"DATA_COLLECT": "false", "STUDENT_NAME": cur_name}

def step_momentum(existing, budget):
    """★ v3.9.25/v1.8: モメンタム発注設定。★ v1.21: 実発注の対象を決める重要STEPとして格上げ。

    [0] MOMENTUM_STRATEGY_PROFILE: 戦略プロファイル (select_v1=選抜[既定・v1.37〜] / standard=今まで通り) ★ v1.35
    [1] MOMENTUM_LEVEL          : シグナル発火頻度 (1=最厳格 〜 5=最緩和)
    [2] 動作モード               : シャドー観察のみ / 実発注も行う (既定: 実発注)
    [2-b] デモ口座のショート       : ON / OFF (既定: ON・v3.9.68)
    [2-c] 銘柄ごとの実発注サイド     : SPY/QQQ/SMH ごとに 買い/売り を個別選択 (IWM/DRAMはシャドー観察のみ)
    [3] MOMENTUM_RISK_LEVEL     : リスク許容度 (1回・1日の損失上限 + 急変動ガード)
    [4] MOMENTUM_MAX_PCT        : 1 回の最大発注額 (BUDGET の %)
    [5] MOMENTUM_STOP_LOSS_PCT  : モメンタム建玉の強制損切りライン (%) ★ v3.9.63
    [6] MOMENTUM_TRAIL_FROM_ENTRY: 損切りの方式 (建玉トレール[標準・既定] / 従来=固定) ★ v3.9.90

    その他の細かい設定 (銘柄・時間帯フィルタ等) は .env 直接編集で対応。
    """
    header(13, TOTAL, "⚡ STEP 13 ── モメンタム発注設定（実発注の対象を決める重要設定）")
    print(f"  {yellow('⚠ このSTEPで「実際に発注するか」「どの銘柄・方向を実発注するか」が決まります。')}")
    print(f"  {yellow('  Enter連打で飛ばさず、各項目を確認してください。')}")
    print()

    try:
        budget_val = float(budget)
    except (ValueError, TypeError):
        budget_val = 10000.0

    print(f"  {bold('概要')}")
    print(f"  {dim('ニュースが流れていなくても、価格の急変動（勢い）だけを根拠に売買')}")
    print(f"  {dim('タイミングを判定する機能です。')}")
    print()
    print(f"  {bold('発注対象（実発注は下の [2-c] で銘柄ごと・方向ごとに選べます）')}")
    print(f"  {dim('・SPY / QQQ / SMH … 実発注の対象。買い(ロング)・空売り(ショート)の両方に対応。')}")
    print(f"  {dim('  （デモ口座でもネッティング方式で空売りに対応します）')}")
    print(f"  {dim('・IWM / DRAM … シャドー観察のみ（実発注対象外。検証データを収集中）。')}")
    print()

    # ── [0] 戦略プロファイル ★ v1.35 / Bot v3.9.116 ──────────────────────
    print(f"  {bold('[0] 戦略プロファイル（実発注の絞り込み・任意）')}")
    print(f"  {dim('過去の全取引データの集計に基づく「絞り込み運転」を選べます。')}")
    # ★ v1.38: 既定は[2]選抜プロファイル。「Enter＝従来どおり」ではない点を正しく表記（Codexレビュー対応）
    print(f"  {dim('[1] 標準 を選ぶと、これまでと完全に同じ動作です（Enter＝既定の[2]選抜プロファイル）。')}")
    print()
    # ★ v1.37: 既定を「選抜プロファイル v1」に変更。過去集計で標準より相対的に成績が良好かつ、
    #   実発注が少なく1トレードのリスクも小さい（より保守的な）運転のため。未設定の新規は select_v1。
    #   （注）戦略全体はまだ黒字化していない。あくまで“標準よりマシ・低リスク”の位置づけで、利益は非保証。
    _cur_profile = str(existing.get("MOMENTUM_STRATEGY_PROFILE", "select_v1")).strip().lower()
    _cur_prof_mode = "1" if _cur_profile == "standard" else "2"
    print(f"  {green('▶') if _cur_prof_mode == '2' else ' '} [2] 選抜プロファイル v1（絞り込み運転・既定）")
    print( "        約5週間の全取引データ（実発注 4,266件＋シャドー観察のユニークシグナル 4,952件）")
    print( "        を集計し、標準より相対的に成績が良好だった条件だけに実発注を絞ります。")
    print( "        （＝実発注が少なく、1トレードのリスクも小さい保守的な運転。成績は変動し利益は保証しません）")
    print( "        絞り込みの内容（5つ）:")
    print( "          ① 方向    … 空売り（ショート）のみ実発注。買い（ロング）は記録のみ")
    print( "          ② 銘柄    … SPY を実発注から除外（対象は QQQ / SMH）")
    print( "          ③ 時間帯  … 米国東部時間 9・10・12・13時台のみ新規発注")
    print( "                       （11時台と14時以降は過去集計で損失が続いた時間帯のため見送り）")
    print( "          ④ 損切り  … 固定の損切りライン（建玉トレールは使わない）")
    print( "                       利益が伸びたときのトレール利確は今まで通り働きます")
    print( "          ⑤ 安全網  … 1日の損失が予算の1.5%に達したら、その日の新規発注を自動停止")
    print()
    print(f"  {green('▶') if _cur_prof_mode == '1' else ' '} [1] 標準（今まで通り）")
    print( "        プロファイルによる絞り込みなし。このSTEPの [1]〜[6] の設定がそのまま使われます。")
    print( "        （買い・売り両方や全時間帯で実発注するぶん、実発注は多く1トレードのリスクも相対的に大きめ）")
    print()
    print(f"  {dim('・見送ったシグナルもすべてシャドー記録に残るため、絞り込みの効果は毎週の集計で確認できます。')}")
    print(f"  {dim('・過去データの傾向に基づく設定であり、将来の成績を保証するものではありません。')}")
    print(f"  {dim('・[2]を選んだ場合、下の[2-c]銘柄サイド・[2-d]ロングレンジ・[6]損切り方式よりも、')}")
    print(f"  {dim('  プロファイルの絞り込みが優先されます（実発注のみ。シャドー記録は全件そのまま）。')}")
    print(f"  {dim('・いつでも Wizard を再実行して [1] 標準に戻せます。')}")
    print()
    profile_choices = [
        ("1", "標準（今まで通り）"),
        ("2", "選抜プロファイル v1（絞り込み運転）← 既定"),
    ]
    _prof_sel = ask_choice("番号を選択（Enter=現在値を維持）", profile_choices, default=_cur_prof_mode)
    strategy_profile = "select_v1" if _prof_sel == "2" else "standard"
    is_select_profile = (strategy_profile == "select_v1")
    ok("戦略プロファイル: " + ("選抜プロファイル v1（絞り込み運転）" if is_select_profile else "標準（今まで通り）"))
    print()

    # ── ★ v1.36: 選抜プロファイル選択時は詳細設定([1]〜[6])をスキップして次STEPへ ──
    # プロファイルが実発注の絞り込み（SHORTのみ・SPY除外・時間帯・固定損切り・日次1.5%）を
    # 内蔵するため、細かいモメンタム設定は尋ねず、他キーは現在値を維持する（シャドーは全記録）。
    if is_select_profile:
        _ds_cur     = str(existing.get("DEMO_SHORT_ENABLED", "true")).strip().lower()
        _demo_short = (_ds_cur != "false")
        _mom_stop_keep = _pct_to_percent_str(existing.get("MOMENTUM_STOP_LOSS_PCT", ""), "0.50")
        print(f"  {green('選抜プロファイル v1 を選択 → 詳細なモメンタム設定はスキップします。')}")
        print(f"  {dim('プロファイルが以下を自動適用します（実発注のみ・シャドー記録は全件そのまま）:')}")
        print(f"  {dim('  ・空売り(SHORT)のみ実発注（買いは記録のみ）')}")
        print(f"  {dim('  ・SPYは対象外（QQQ / SMH を実発注）')}")
        print(f"  {dim('  ・米国東部時間 9・10・12・13時台のみ新規発注')}")
        print(f"  {dim('  ・固定の損切りライン（建玉トレールは使わない）')}")
        print(f"  {dim('  ・1日の損失が予算の1.5%に達したら自動停止')}")
        # ★ v1.38: 新規（未設定）の場合は「現在値の維持」ではなく既定値の書き出しである旨を明記
        print(f"  {dim('  ※ 発火頻度・リスク・最大発注%・損切り幅は現在値を維持します')}")
        print(f"  {dim('    （未設定の新規は既定値: 発火Lv3 / リスクLv3 / 最大80% / 損切り0.50% を書き出します）。')}")
        print(f"  {dim('  ※ 標準（今まで通り）に戻すと、これらの詳細を個別に設定できます。')}")
        print()
        # ★ v1.38: スキップ時でも「実際に発注するか」だけは必ず確認する（Codexレビュー対応）。
        #   従来はスキップで既定 true のまま通過し、実発注の明示確認が行われなかった。
        print(f"  {bold('実発注の確認（重要）')}")
        print(f"  {dim('選抜プロファイルでも「実際に注文するか」はここで決まります。')}")
        _live_cur = str(existing.get("MOMENTUM_LIVE_TRADING", "true")).strip().lower()
        _live_mode_cur = "1" if _live_cur == "false" else "2"
        _live_choices = [
            ("1", "シャドー観察のみ   実発注なし・「もし注文していたら」を記録のみ"),
            ("2", "実発注も行う      実際に注文する（デモ口座→デモ発注 / 実口座→実発注）← 標準"),
        ]
        _live_sel = ask_choice("番号を選択（Enter=現在値）", _live_choices, default=_live_mode_cur)
        _is_live = (_live_sel == "2")
        if _is_live:
            print()
            print(f"  {yellow('⚠ 実発注モードです。実口座なら実資金が動きます（デモ口座ならデモ発注）。')}")
            if not ask_yn("実発注を有効にします。よろしいですか？", default=True):
                _is_live = False
                print()
                info("シャドー観察（記録のみ）に切り替えました。実発注は行いません。")
        print()
        ok("モメンタム設定: 選抜プロファイル v1（詳細設定はスキップ）/ "
           + ("実発注も行う" if _is_live else "シャドー観察のみ"))
        next_step_pause()
        return {
            "MOMENTUM_STRATEGY_PROFILE": "select_v1",
            "MOMENTUM_LEVEL":         existing.get("MOMENTUM_LEVEL", "3"),
            "MOMENTUM_RISK_LEVEL":    existing.get("MOMENTUM_RISK_LEVEL", "3"),
            "MOMENTUM_MAX_PCT":       existing.get("MOMENTUM_MAX_PCT", "80"),
            "MOMENTUM_STOP_LOSS_PCT": _mom_stop_keep,
            "MOMENTUM_STOP_PROFILE":  existing.get("MOMENTUM_STOP_PROFILE", "standard"),
            "MOMENTUM_LONG_MIN_SIGNAL_PCT": existing.get("MOMENTUM_LONG_MIN_SIGNAL_PCT", "0.70"),
            "MOMENTUM_LONG_MAX_SIGNAL_PCT": existing.get("MOMENTUM_LONG_MAX_SIGNAL_PCT", "0.80"),
            "MOMENTUM_TRAIL_FROM_ENTRY": existing.get("MOMENTUM_TRAIL_FROM_ENTRY", "true"),
            "MOMENTUM_SHADOW_ENABLED": "true",
            "MOMENTUM_LIVE_TRADING":   "true" if _is_live else "false",
            "DEMO_SHORT_ENABLED":      "true" if _demo_short else "false",
            "MOMENTUM_ENABLED_SIDES":  existing.get(
                "MOMENTUM_ENABLED_SIDES", "SPY:SELL_SHORT,QQQ:SELL_SHORT,SMH:SELL_SHORT"),
        }

    # ── [1] 発火頻度 ─────────────────────────────────────────────
    print(f"  {bold('[1] シグナル発火頻度 (MOMENTUM_LEVEL)')}")
    print(f"  {dim('どれだけ厳格にシグナルを取りに行くか')}")
    print()
    momentum_level_choices = [
        ("1", "最厳格  (1-2 件/日)  黄金シグナルだけ厳選"),
        ("2", "厳格    (2-3 件/日)  やや慎重"),
        ("3", "標準    (3-5 件/日) ← まずここから"),
        ("4", "緩和    (5-8 件/日)  件数優先"),
        ("5", "最緩和  (8-15 件/日) 学習・観察用"),
    ]
    cur_level = existing.get("MOMENTUM_LEVEL", "3")
    mom_level = ask_choice("番号を選択（Enter=現在値を維持）", momentum_level_choices,
                           default=cur_level)
    print()

    # ── [2] 動作モード (シャドー / 実発注) ─────────────────────────
    print(f"  {bold('[2] 動作モード')}")
    print(f"  {dim('シグナルが出たときに「記録だけ」か「実際に注文する」かを選びます')}")
    print()
    mode_choices = [
        ("1", "シャドー観察   実発注なし・「もし注文していたら」を記録のみ"),
        ("2", "実発注も行う   実際に注文する（デモ口座→デモ発注 / 実口座→実発注）← 標準"),
    ]
    # 既存設定から現在モードを推定 (MOMENTUM_LIVE_TRADING=true なら 2)
    # ★ v3.9.68: 既定を 2(実発注) に変更 (記載が無ければ実発注)
    cur_live = existing.get("MOMENTUM_LIVE_TRADING", "true").strip().lower()
    cur_mode = "1" if cur_live == "false" else "2"
    mode = ask_choice("番号を選択（Enter=現在値を維持）", mode_choices, default=cur_mode)
    is_live = (mode == "2")
    if is_live:
        print()
        print(f"  {yellow('⚠ 実発注モードです。実口座なら実資金が動きます（デモ口座ならデモ発注）。')}")
        # ★ v1.21 (点4): 実発注は誤設定の影響が大きいため、確認クッションを1つ入れる。
        _confirm = ask_yn("実発注を有効にします。よろしいですか？", default=True)
        if not _confirm:
            is_live = False
            print()
            info("シャドー観察（記録のみ）に切り替えました。実発注は行いません。")
    print()

    # ── [2-b] デモ口座のショート (ネッティング空売り) ★ v3.9.68 ──────────
    # デモはプレーン SELL で建て / BUY で決済。勝ち筋のショート側をデモでも実発注化できる。
    print(f"  {bold('[2-b] デモ口座のショート (空売り)')}")
    print(f"  {dim('デモ口座でも空売りを実発注するかを選びます（実口座は常に空売り可）。')}")
    print(f"  {dim('成績の良いショート側をデモでも検証でき、信用口座に近い成績を確認できます。')}")
    print()
    demo_short_choices = [
        ("1", "ON   デモでもショートを実発注する ← 標準"),
        ("2", "OFF  デモのショートは記録のみ（シャドー）"),
    ]
    cur_ds = existing.get("DEMO_SHORT_ENABLED", "true").strip().lower()
    cur_ds_mode = "2" if cur_ds == "false" else "1"
    ds_mode = ask_choice("番号を選択（Enter=現在値を維持）", demo_short_choices, default=cur_ds_mode)
    demo_short = (ds_mode == "1")
    print()

    # ── [2-c] 銘柄ごとの実発注サイド (買い/売り) ★ Wizard v1.15 ────────────────
    # 銘柄ごとに「買い(LONG)/売り(SHORT)」を個別に実発注対象へ。選んだ組合せだけが
    # 実発注され、他は観察(シャドー)のみ。IWM/DRAM はシャドー観察のみ(ここでは選べない)。
    print(f"  {bold('[2-c] 銘柄ごとの実発注サイド (買い/売り)')}")
    print(f"  {dim('銘柄ごとに、実際に発注する方向を選びます。選ばない方向は記録のみ。')}")
    print(f"  {dim('「両方」を選ぶと買い・売り両方のデータが取得できます。デモ口座でも空売りに対応します。')}")
    print(f"  {dim('（IWM / DRAM はシャドー観察のみ・実発注対象外のため、ここには出ません）')}")
    if is_select_profile:
        print(f"  {dim('※ 選抜プロファイル v1 選択中は、ここで選んだ組み合わせのうち「QQQ / SMH の売り」だけが実発注されます。')}")
    print()
    # 各銘柄の既定は「両方(1)」。IWM/DRAM はシャドー観察のみのため実発注選択肢から除外。
    _SIDE_SYMS = ["SPY", "QQQ", "SMH"]
    _std = {"SPY": "1", "QQQ": "1", "SMH": "1"}
    # 既存 env からの現在値推定
    cur_sides_set = set(s.strip().upper() for s in
                        existing.get("MOMENTUM_ENABLED_SIDES", "").split(",") if ":" in s)

    def _cur_mode_for(sym):
        has_buy = f"{sym}:BUY" in cur_sides_set
        has_sht = f"{sym}:SELL_SHORT" in cur_sides_set
        if has_buy and has_sht: return "1"
        if has_buy:             return "2"
        if has_sht:             return "3"
        if cur_sides_set:       return "4"   # env明示済みで当該銘柄なし＝なし
        return _std[sym]                      # env未設定＝既定（両方）

    # ★ v1.21 (点3): まず「標準セット一括 / 個別選択」で分岐。大半は1画面で抜けられる。
    setup_choices = [
        ("1", "標準セットでまとめて設定（SPY・QQQ = 買い+売り、SMH = 売りのみ）← まずここから"),
        ("2", "1銘柄ずつ方向を選ぶ（上級者向け）"),
    ]
    # ★ v1.42: 既存が標準セット以外のカスタムなら既定を[2]個別選択にし、Enterで上書きしない
    _std_sides_set = {f"{s}:{d}" for s in _SIDE_SYMS for d in ("BUY", "SELL_SHORT")} - {"SMH:BUY"}
    _setup_default = "2" if (cur_sides_set and cur_sides_set != _std_sides_set) else "1"
    _sm_hint = "現在の個別設定を維持" if _setup_default == "2" else "標準セット"
    setup_mode = ask_choice(f"番号を選択（Enter={_sm_hint}）", setup_choices, default=_setup_default)
    print()
    enabled_pairs = []
    if setup_mode == "1":
        for sym in _SIDE_SYMS:
            # ★ v1.45: SMH の買いは選択肢から外す（PAN 判断・2026-09-04）。
            #   モメンタム経由の買いは confidence 0.70 固定で、SMH の買いの関門 0.78 に
            #   届かないため、選んでも1件も実発注されない（設定と実態の食い違い）。
            if sym != "SMH":
                enabled_pairs.append(f"{sym}:BUY")
            enabled_pairs.append(f"{sym}:SELL_SHORT")
        ok("標準セットを適用: SPY・QQQ は買い+売り、SMH は売りのみを実発注対象にしました。")
        print()
    else:
        for sym in _SIDE_SYMS:
            side_choices = [
                ("1", "両方（買い + 売り）"),
                ("2", "買いのみ（LONG）"),
                ("3", "売りのみ（SHORT）"),
                ("4", "なし（観察のみ・発注しない）"),
            ]
            _d = _cur_mode_for(sym)
            if sym == "SMH":
                # ★ v1.45: SMH の買いはモメンタム経由では実発注に届かない（上の注記と同じ理由）
                side_choices = [
                    ("3", "売りのみ（SHORT）"),
                    ("4", "なし（観察のみ・発注しない）"),
                ]
                if _d in ("1", "2"):
                    _d = "3"
                print(f"  {bold(sym)}  {dim('※ SMH の買いはモメンタム経由では実発注されないため、選択肢にありません')}")
            else:
                print(f"  {bold(sym)}")
            m = ask_choice(f"  {sym} の実発注サイド（Enter=現在値・未設定は両方）", side_choices, default=_d)
            if m in ("1", "2"):
                enabled_pairs.append(f"{sym}:BUY")
            if m in ("1", "3"):
                enabled_pairs.append(f"{sym}:SELL_SHORT")
            print()
    enabled_sides = ",".join(enabled_pairs)
    # ★ v1.21 (点3): 1日の損失上限の目安をドル額で提示（%の羅列より実感が湧く）
    try:
        _cb_usd = budget_val * 0.03   # BUDGET比3%の自動停止（サーキットブレーカー上限）
        print(f"  {dim('1日の損失がBUDGETの約3%（≒ $' + format(_cb_usd, ',.0f') + '）に達するとモメンタムは自動停止します。')}")
        print(f"  {dim('（次の[3]リスク許容度で、これより小さい上限にも設定できます）')}")
        print()
    except Exception:
        pass
    if not enabled_sides:
        warn("実発注サイドが0件です（モメンタムは全て観察のみになります）。")
    _sides_disp = enabled_sides if enabled_sides else "（なし・観察のみ）"

    # ── ★ v1.34 [2-d] ロング発注のシグナル強度レンジ（5分モメンタム）─────────
    print(f"  {bold('[2-d] ロング発注のシグナル強度レンジ（5分モメンタム）')}")
    print(f"  {dim('買い(ロング)を実発注する5分モメンタムの範囲を選びます。ショートは対象外です。')}")
    if is_select_profile:
        print(f"  {dim('※ 選抜プロファイル v1 選択中はロングを実発注しないため、この設定は「標準」に戻したとき用です。')}")
    print(f"  {dim('参考（過去20日の観察・将来の成績を保証するものではありません）:')}")
    print(f"  {dim('  0.70%未満は平均リターンが低調／0.70〜1.50%はプラス寄り／1.50%超は反転しやすく低調でした。')}")
    print()
    long_range_choices = [
        ("1", "標準        0.70% 〜 0.80%（弱いシグナルを除外）"),
        ("2", "中程度以上  0.70% 〜 1.00%（上限を広げ強シグナルも発注）"),
        ("3", "強帯も許可  0.80% 〜 1.50%（強いシグナルに限定）"),
        ("4", "すべて      0.15% 〜 0.80%（従来）"),
        ("5", "ロングは発注しない（ショートのみ）"),
    ]
    _RANGE_MAP = {"1": ("0.70", "0.80"), "2": ("0.70", "1.00"),
                  "3": ("0.80", "1.50"), "4": ("0.15", "0.80")}
    _cur_lmin = existing.get("MOMENTUM_LONG_MIN_SIGNAL_PCT", "0.70").strip()
    _cur_lmax = existing.get("MOMENTUM_LONG_MAX_SIGNAL_PCT", "0.80").strip()
    _cur_long = next((k for k, (mn, mx) in _RANGE_MAP.items()
                      if mn == _cur_lmin and mx == _cur_lmax), "1")
    long_sel = ask_choice("番号を選択（Enter=既定=標準）", long_range_choices, default=_cur_long)
    if long_sel == "5":
        # ロング発注しない = 実発注サイドから BUY を除外（ショートのみ）
        enabled_pairs = [p for p in enabled_pairs if not p.upper().endswith(":BUY")]
        enabled_sides = ",".join(enabled_pairs)
        _sides_disp = enabled_sides if enabled_sides else "（なし・観察のみ）"
        long_min, long_max = "0.70", "0.80"
        info("ロングは実発注しません（ショートのみ）。買いはシャドー観察のみになります。")
    else:
        long_min, long_max = _RANGE_MAP.get(long_sel, ("0.70", "0.80"))
        ok(f"ロング発注レンジ: 5分モメンタム {long_min}% 〜 {long_max}%")
    print()

    # ── [3] リスク許容度 (損失上限のみ・投入%は [4] で別途設定) ──────
    print(f"  {bold('[3] リスク許容度 (MOMENTUM_RISK_LEVEL)')}")
    print(f"  {dim('1 回・1 日にどれだけ負けたら止めるか + 急変動時の停止幅')}")
    print()
    # ★ v1.38: 表示値を Bot 実プリセット(_MOMENTUM_RISK_PRESETS 現行値)に一致（Codexレビュー対応）。
    #   旧表示は1段緩い旧世代の値で、選択時に見た数字と実際の損失上限が食い違っていた。
    risk_level_choices = [
        ("1", "超慎重    1回-0.10% / 1日-0.25% / 急変動±0.50%"),
        ("2", "慎重      1回-0.15% / 1日-0.40% / 急変動±0.60%"),
        ("3", "標準      1回-0.20% / 1日-0.50% / 急変動±0.70%  ← まずここから"),
        ("4", "積極      1回-0.25% / 1日-0.75% / 急変動±0.85%"),
        ("5", "高リスク  1回-0.30% / 1日-1.00% / 急変動±1.00%"),
    ]
    cur_risk = existing.get("MOMENTUM_RISK_LEVEL", "3")
    risk_level = ask_choice("番号を選択（Enter=現在値を維持）", risk_level_choices,
                            default=cur_risk)
    print()

    # ── [4] 最大発注比率 (BUDGET の %) ────────────────────────────
    print(f"  {bold('[4] 最大発注比率 (MOMENTUM_MAX_PCT)')}")
    print(f"  {dim('BUDGET の何 % を「1 回の最大発注額」にするかを決めます。')}")
    print(f"  {dim('実際の発注額はシグナルの強さで自動配分されます（山型）:')}")
    print(f"  {dim('  弱いシグナル → 最大額の 50%  /  中 → 75%  /  最良帯 → 100%')}")
    # ★ v1.38: [2-d]の上限設定と整合（0.8%固定と読める旧表現を修正）
    print(f"  {dim('  強すぎるシグナルは発注しません（既定の上限 0.80%。[2-d]で上限を')}")
    print(f"  {dim('  1.00〜1.50% に広げた場合は、その設定が優先されます）。')}")
    print()
    print(f"  {bold('％の選び方ガイド')}")
    print(f"  {dim('・1 回 $5,000 未満の発注は手数料負けしやすい点にご注意ください。')}")
    print(f"  {dim('・BUDGET $10,000 前後の方: 80〜100% が目安（最大 $8,000〜$10,000）。')}")
    print(f"  {dim('・BUDGET $20,000 以上の方: 50〜70% でも $5,000 以上を確保できます。')}")
    print(f"  {dim('・BUDGET $5,000 以下の方: 100% でも手数料負けしやすい点にご注意を。')}")
    print()
    print(f"  {bold(f'あなたの BUDGET = ${budget_val:,.0f}')}  の場合の最大発注額:")
    for pct in (50, 60, 70, 80, 90, 100):
        amt = budget_val * pct / 100.0
        mark = green("  ← まずここから") if pct == 80 else ""
        fee = yellow("  ⚠ 手数料負けしやすい") if amt < 5000 else ""
        print(f"    {pct:3d}%  →  最大 ${amt:,.0f}{mark}{fee}")
    print()
    cur_max = existing.get("MOMENTUM_MAX_PCT", "80")
    while True:
        val = ask("最大発注比率 %（50〜100 の整数 / Enter=現在値）", default=cur_max)
        try:
            v = int(float(val))
            if 50 <= v <= 100:
                max_pct = str(v)
                break
        except (ValueError, TypeError):
            pass
        warn("50〜100 の整数で入力してください（例: 80）")
    _max_amt = budget_val * int(max_pct) / 100.0
    if _max_amt < 5000:
        warn(f"最大発注額 ${_max_amt:,.0f} は $5,000 未満です。手数料負けにご注意ください。")
    print()

    # ── [5] モメンタム損切りライン (MOMENTUM_STOP_LOSS_PCT) ─────────
    print(f"  {bold('[5] モメンタム損切りライン (MOMENTUM_STOP_LOSS_PCT)')}")
    print(f"  {dim('モメンタム建玉を「含み損 何 % で強制損切り」するかを決めます。')}")
    print(f"  {dim('数値が小さいほど早く損切り（傷は浅いが往来で刈られやすい）、')}")
    print(f"  {dim('大きいほど粘る（時間切れ60分まで保有しやすいが1回の損失は増加）。')}")
    print()
    print(f"  {dim('※ ニュース駆動トレードの損切り(MAX_LOSS_PCT)とは別系統です。')}")
    print(f"  {dim('  6/1実発注の検証では QQQ が 0.20〜0.31% で早期に刈られ、寄り高値掴み')}")
    print(f"  {dim('  の往来で小幅マイナスが連発しました。0.50%前後が標準の目安です。')}")
    print()
    print(f"  {dim('  0.30%  早い損切り（傷浅め・往来で刈られやすい）')}")
    print(f"  {green('  0.50%  標準（時間切れ60分まで粘りやすい）← まずここから')}")
    print(f"  {dim('  0.80%  粘る（1回の損失は増えるが伸ばせる）')}")
    print()
    cur_stop = existing.get("MOMENTUM_STOP_LOSS_PCT", "0.50")
    while True:
        val = ask("モメンタム損切り %（0.10〜5.0 / Enter=現在値）", default=cur_stop)
        try:
            v = float(val)
            if 0.10 <= v <= 5.0:
                mom_stop = (f"{v:.2f}").rstrip("0").rstrip(".")
                break
        except (ValueError, TypeError):
            pass
        warn("0.10〜5.0 の数値で入力してください（例: 0.50）")
    print()

    # ── ★ v1.34 [5b] 損切り幅プロファイル（ボラティリティ別・自動）─────────
    print(f"  {bold('[5b] 損切り幅プロファイル（ボラティリティ別・検証中）')}")
    print(f"  {dim('銘柄のボラに応じた損切り幅（基準値×銘柄別倍率）です。この選択が反映されるのは')}")
    print(f"  {dim('ニュース起点の建玉と一部のシャドー模擬で、比較用の計測列は全員共通（標準）で測ります。')}")
    print(f"  {yellow('※ 重要: 現在、この倍率はモメンタムの実発注には適用されません。')}")
    print(f"  {yellow('  実発注の損切りは [5] の基準値（全銘柄共通・既定0.50%）で動作します。')}")
    print(f"  {dim('  実発注への適用は、シャドー計測の結果を確認したうえで今後の版で判断します。')}")
    print()
    print(f"  {dim('  銘柄    区分        狭め    標準    広め   ※[5]が既定0.50%の場合の参考値')}")
    print(f"  {dim('  SMH     参考値      1.00%   1.50%   2.00%')}")
    print(f"  {dim('  QQQ     参考値      0.70%   1.00%   1.30%')}")
    print(f"  {dim('  SPY     参考値      0.50%   0.65%   0.85%')}")
    print(f"  {dim('  DRAM    参考値      0.70%   1.00%   1.30%')}")
    print(f"  {dim('  IWM     参考値      0.35%   0.50%   0.65%')}")
    print(f"  {dim('  ※ 根拠: SMHは60分の変動が最大、DRAMは短期(5分)の変動が最大')}")
    print()
    stop_profile_choices = [
        ("1", "狭め（早めに損切り／1回の損失は小さめ）"),
        ("2", "標準 ← 既定"),
        ("3", "広め（切られにくい／1回の損失は大きめ）"),
        ("4", "一律（全銘柄 基準%のまま・従来）"),
        ("5", "上級者：.env で個別指定（MOMENTUM_STOP_MULT_<銘柄>）"),
    ]
    _PROF_MAP = {"1": "narrow", "2": "standard", "3": "wide", "4": "flat", "5": "standard"}
    _cur_prof_val = existing.get("MOMENTUM_STOP_PROFILE", "standard").strip().lower()
    _cur_prof_key = next((k for k, v in _PROF_MAP.items() if v == _cur_prof_val and k != "5"), "2")
    prof_sel = ask_choice("番号を選択（Enter=既定=標準）", stop_profile_choices, default=_cur_prof_key)
    stop_profile = _PROF_MAP.get(prof_sel, "standard")
    if prof_sel == "5":
        info("上級者モード：.env に MOMENTUM_STOP_MULT_SMH=3.5 などで銘柄別に上書きできます（未指定は標準）。")
        info("※ この上書きが反映されるのはニュース起点の建玉と一部のシャドー模擬です（モメンタム実発注には効きません）。")
    _prof_name = {"narrow": "狭め", "standard": "標準", "wide": "広め", "flat": "一律"}.get(stop_profile, "標準")
    ok(f"損切り幅プロファイル: {_prof_name}")
    print()

    # ── [6] 損切りの方式 (MOMENTUM_TRAIL_FROM_ENTRY) ★ v1.22 / Bot v3.9.85 ─────
    _trig_disp = _pct_to_percent_str(existing.get("TRAIL_TRIGGER_PCT", ""), "0.22")  # ★ v1.38 新標準
    _drop_disp = _pct_to_percent_str(existing.get("TRAIL_DROP_PCT", ""), "0.15")
    # ★ v1.23 / Bot v3.9.90: 建玉トレールが既定（標準）に。未設定は true 扱い。
    _cur_tfe   = str(existing.get("MOMENTUM_TRAIL_FROM_ENTRY", "true")).strip().lower()
    _is_tfe    = (_cur_tfe != "false")   # 未設定/true は建玉トレール
    print(f"  {bold('[6] 損切りの方式 (MOMENTUM_TRAIL_FROM_ENTRY)')}")
    print(f"  {dim('モメンタム建玉の損失の抑え方を 2 つから選べます。')}")
    print()
    print(f"  {green('▶') if _is_tfe else ' '} [1] 建玉トレール方式（建てた瞬間からのトレールストップ・標準）")
    print(f"        建玉した瞬間から「損切り幅と同じ幅（{mom_stop}%）のトレール」をかけます。")
    print( "        含み益が出ると損切りラインも一緒に切り上がるため、")
    print( "        「一度伸びてから反落」したときの損失を小さくできます。")
    print(f"        トレール開始ライン（+{_trig_disp}%）に届くと、自動で通常の")
    print(f"        狭いトレール幅（{_drop_disp}%）へ切り替わります（利益は減らさず即切り額を小さくする狙い）。")
    print()
    print(f"  {green('▶') if not _is_tfe else ' '} [2] 従来方式：固定の損切りライン（★現在の検証対象）")
    print(f"        建値から -{mom_stop}% に達したら損切り（v3.9.89 以前の動作）。")
    print(f"        {dim('選抜プロファイル v1 と同じ出口。標準プロファイルでこれを選ぶと')}")
    print(f"        {dim('シートに「+flatstop」の印が付き、建玉トレール群との比較検証に使われます（Bot v3.9.128〜）。')}")
    print()
    print(f"  {dim('※ 標準の既定は [1] 建玉トレール。ただし建玉トレールは集計上の最大の出血源で、')}")
    print(f"  {dim('   [2] 固定損切りへ置換する効果を段階導入で検証中です（協力いただける方は [2] を選択）。')}")
    print(f"  {dim('※ 下方向へ一直線に動く場合は、[1] でも [2] と同じ損切り幅で守られます（不利になりません）。')}")
    print()
    if is_select_profile:
        print(f"  {yellow('※ 選抜プロファイル v1 を選択中は、実発注では常に [2] 固定の損切りラインが適用されます。')}")
        print(f"  {dim('   （ここでの選択は、プロファイルを「標準」に戻したときに使われます）')}")
        print()
    _tfe_default = "1" if _is_tfe else "2"
    while True:
        _sel = ask("番号を選択（Enter=現在値）", default=_tfe_default)
        if _sel in ("1", "2"):
            break
        warn("1 または 2 で入力してください")
    trail_from_entry = "true" if _sel == "1" else "false"
    _tfe_name = "建玉トレール（標準）" if trail_from_entry == "true" else "従来（固定）"
    ok(f"損切りの方式: {_tfe_name}")
    print()

    # ── 確認表示 ────────────────────────────────────────────
    level_name = {"1": "最厳格", "2": "厳格", "3": "標準", "4": "緩和", "5": "最緩和"}.get(mom_level, "標準")
    risk_name  = {"1": "超慎重", "2": "慎重", "3": "標準", "4": "積極", "5": "高リスク"}.get(risk_level, "標準")
    mode_name  = "実発注も行う" if is_live else "シャドー観察のみ"
    ds_name    = "ON（実発注）" if demo_short else "OFF（シャドー）"
    _profile_disp = ("選抜プロファイル v1（SHORTのみ・SPY除外・ET 9/10/12/13時台・固定損切り・日次1.5%停止）"
                     if is_select_profile else "標準（今まで通り・絞り込みなし）")
    ok(f"モメンタム設定: {mode_name} / 発火 Lv{mom_level}({level_name}) / "
       f"リスク Lv{risk_level}({risk_name}) / 最大 {max_pct}% / 損切り {mom_stop}% / デモ空売り {ds_name}")
    ok_box([
        ("戦略プロファイル",       _profile_disp),
        ("動作モード",            mode_name),
        ("デモ口座のショート",     ds_name),
        ("実発注対象サイド",       _sides_disp),
        ("MOMENTUM_LEVEL",       f"{mom_level} ({level_name})"),
        ("MOMENTUM_RISK_LEVEL",  f"{risk_level} ({risk_name})"),
        ("MOMENTUM_MAX_PCT",     f"{max_pct}%  (最大 ${_max_amt:,.0f})"),
        ("MOMENTUM_STOP_LOSS_PCT", f"{mom_stop}%  (モメンタム建玉の強制損切り・基準値)"),
        ("損切り幅プロファイル",     f"{_prof_name}  (モメンタム実発注には効きません・実発注は[5]の基準値)"),
        ("ロング発注レンジ",         (f"5分 {long_min}%〜{long_max}%" if long_sel != "5" else "発注しない（ショートのみ）")),
        ("MOMENTUM_TRAIL_FROM_ENTRY", f"{trail_from_entry}  (損切りの方式: {_tfe_name})"),
    ])
    next_step_pause()
    return {
        "MOMENTUM_STRATEGY_PROFILE": strategy_profile,   # ★ v1.35 戦略プロファイル (Bot v3.9.116)
        "MOMENTUM_LEVEL":         mom_level,
        "MOMENTUM_RISK_LEVEL":    risk_level,
        "MOMENTUM_MAX_PCT":       max_pct,
        "MOMENTUM_STOP_LOSS_PCT": mom_stop,
        "MOMENTUM_STOP_PROFILE":  stop_profile,          # ★ v1.34 ボラ別損切り幅プロファイル
        "MOMENTUM_LONG_MIN_SIGNAL_PCT": long_min,        # ★ v1.34 ロング下限(5分)
        "MOMENTUM_LONG_MAX_SIGNAL_PCT": long_max,        # ★ v1.34 ロング上限(5分)
        "MOMENTUM_TRAIL_FROM_ENTRY": trail_from_entry,
        # シャドー観察は常に有効 (実発注モードでも観察データは取得)
        "MOMENTUM_SHADOW_ENABLED": "true",
        "MOMENTUM_LIVE_TRADING":   "true" if is_live else "false",
        "DEMO_SHORT_ENABLED":      "true" if demo_short else "false",
        # ★ v3.9.70: 実発注対象サイドを Wizard で明示書き出し (DRAM は含めない=観察のみ)
        "MOMENTUM_ENABLED_SIDES":  enabled_sides,
    }


def step_alert_sound(existing):
    """★ v3.9.19: 上級者向け — 重大エラー時のアラート音設定 (デフォルト無効)。"""
    header(14, TOTAL, "🔔 STEP 14 ── 重大エラー時のアラート音（上級者向け・任意）")

    print(f"  {bold('概要')}")
    print(f"  {dim('Bot に重大なエラーが発生した瞬間に OS の音を鳴らして即座に気づける')}")
    print(f"  {dim('ようにします。デフォルトは「無効」です。')}")
    print()

    print(f"  {bold('音が鳴る 6 つの条件')}")
    for line in [
        "Anthropic API クレジット切れ検知（AI判定が全件失敗）",
        "moomoo SDK が古すぎる（起動拒否）",
        "OpenD に接続できない（起動拒否）",
        "取引ロック検出（unlock エラー・全発注停止）",
        "強制損切りの発注が全失敗（損失拡大リスク）",
        "ショートカバー全 position_id 発注失敗（損失拡大リスク）",
    ]:
        print(f"  {yellow('🔔')} {dim(line)}")
    print()

    print(f"  {bold('鳴らない条件')}  {dim('（誤検知・連発を避けるため）')}")
    for line in [
        "通常の損切り発動・トレイル発動・パニックセル発動",
        "Anthropic 529 Overloaded（既存リトライで吸収）",
        "[ETF影響ガード] 等の正常動作ログ",
    ]:
        print(f"  {green('✓')} {dim(line)}")
    print()

    print(f"  {bold('技術仕様')}")
    print(f"  {dim('・macOS: afplay /System/Library/Sounds/Sosumi.aiff')}")
    print(f"  {dim('・Windows: winsound.MessageBeep（標準ライブラリ）')}")
    print(f"  {dim('・Linux: paplay（PulseAudio 同梱）')}")
    print(f"  {dim('・SSH リモート / 音声デバイス無し環境では失敗しても無視')}")
    print(f"  {dim('・同一イベントは 60 秒以内の連発を抑制')}")
    print()

    cur_enable      = existing.get("ENABLE_ALERT_SOUND", "false").lower()
    cur_cooldown    = existing.get("ALERT_SOUND_COOLDOWN_SEC", "60")
    cur_quiet_hours = existing.get("ALERT_SOUND_QUIET_HOURS", "")
    cur_macos_file  = existing.get("ALERT_SOUND_FILE_MACOS", "/System/Library/Sounds/Sosumi.aiff")

    print(f"  {yellow('※ 標準的な使い方: PC前で監視できる時間帯のみ有効化、夜間は ALERT_SOUND_QUIET_HOURS で抑制')}")
    print()
    # ★ v1.8: 「はい」を選ぶとテスト音が鳴ることを事前に案内（音量注意）
    print(f"  {yellow('※「はい」を選ぶと、実際のアラート音が一度再生されます。音量にご注意ください。')}")
    print()
    enable = ask_yn("アラート音を有効化しますか？", default=(cur_enable == "true"))

    if not enable:
        print()
        info("アラート音を無効化しました。（デフォルト動作）")
        ok_box([("ENABLE_ALERT_SOUND", "false（音を鳴らさない）")])
        next_step_pause()
        return {
            "ENABLE_ALERT_SOUND":       "false",
            "ALERT_SOUND_COOLDOWN_SEC": cur_cooldown,
            "ALERT_SOUND_QUIET_HOURS":  cur_quiet_hours,
            "ALERT_SOUND_FILE_MACOS":   cur_macos_file,
        }

    # ── ★ v1.8: 有効化したら実際にテスト音を 1 回鳴らす ──
    print()
    print(f"  {dim('アラート音を再生します…')}")
    _played = _play_test_sound(cur_macos_file)
    if _played:
        ok("テスト音を再生しました。音が聞こえましたか？")
    else:
        warn("テスト音の再生に失敗しました（音声デバイス無し / リモート環境の可能性）。")
        info("実環境で音が鳴らない場合は、PC のスピーカー設定をご確認ください。")
    print()

    # ── 有効化 → 詳細設定 ──
    print()
    print(f"  {dim('夜間ミュート時間帯（JST、HH:MM-HH:MM 形式、日跨ぎ可）')}")
    print(f"  {dim('例: 23:00-06:00  （未入力で常時有効）')}")
    # ★ v1.38: HH:MM-HH:MM 形式を検証（不正形式は Bot 側で黙って「ミュートなし」扱いになるため）
    _QH_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d-([01]?\d|2[0-3]):[0-5]\d$")
    while True:
        quiet_hours = ask("夜間ミュート時間帯", default=cur_quiet_hours).strip()
        if not quiet_hours or _QH_RE.match(quiet_hours):
            break
        warn("HH:MM-HH:MM 形式で入力してください（例: 23:00-06:00 / 未入力=常時有効）")

    print()
    print(f"  {dim('連発抑制クールダウン（秒）。同一イベントはこの秒数以内は再生しない')}")
    cooldown = ask("クールダウン秒数", default=cur_cooldown)
    cooldown = cooldown.strip() or "60"
    try:
        _cd = int(cooldown)
        if _cd < 0:
            cooldown = "60"
    except ValueError:
        cooldown = "60"

    # ★ v1.8: macOS 音源パスの選択は Wizard から削除。
    # 既存値 (なければデフォルトの Sosumi) をそのまま使用する。
    # 音源を変えたい上級者は .env の ALERT_SOUND_FILE_MACOS を直接編集する。
    macos_file = cur_macos_file

    print()
    ok("アラート音を有効化しました。")
    ok_box([
        ("ENABLE_ALERT_SOUND",       "true（有効）"),
        ("ALERT_SOUND_COOLDOWN_SEC", f"{cooldown} 秒"),
        ("ALERT_SOUND_QUIET_HOURS",  quiet_hours or "（常時有効）"),
    ])
    next_step_pause()
    return {
        "ENABLE_ALERT_SOUND":       "true",
        "ALERT_SOUND_COOLDOWN_SEC": cooldown,
        "ALERT_SOUND_QUIET_HOURS":  quiet_hours,
        "ALERT_SOUND_FILE_MACOS":   macos_file,
    }


def _pad(text, width):
    """ANSIエスケープコードを除いた実表示幅でパディングする"""
    visible_len = len(re.sub(r'\033\[[0-9;]*m', '', text))
    return text + ' ' * max(0, width - visible_len)


# =============================================================================
# 設定レビュー・警告チェック
# =============================================================================

def _check_quoted(val):
    if not val:
        return False
    return (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"'))


# ★ v1.38: 警告レビュー画面で validate 未指定の数値キーに適用する既定バリデータ
#   （非数値の入力で MAX_LOSS_PCT 等が上書きされると Bot が起動を拒否するため）。
_NUMERIC_KEY_RANGES = {
    "MAX_LOSS_PCT":      (0.0, 10.0),
    "TRAIL_TRIGGER_PCT": (0.0, 5.0),
    "TRAIL_DROP_PCT":    (0.0, 5.0),
    "BUDGET_USD":        (0.0, 1_000_000_000.0),
    "STOCK_MAX_PCT":     (0.0, 100.0),
    "LIMIT_BUFFER_PCT":  (0.0, 10.0),
}

def _default_validator_for(key):
    """validate 未指定キーの既定検証。数値キーは範囲チェック、その他は None（無検証）。"""
    if key in _NUMERIC_KEY_RANGES:
        lo, hi = _NUMERIC_KEY_RANGES[key]
        return lambda v, lo=lo, hi=hi: lo < float(v) <= hi
    if key.endswith("_CONFIDENCE") or key.startswith("CONFIDENCE_"):
        # 0.5〜1.0、または「発注しない」sentinel 2.00 を許容
        return lambda v: (0.5 <= float(v) <= 1.0) or float(v) == 2.0
    return None

def _collect_warnings(config):
    warnings = []

    def _f(key, default=0.0):
        try:
            return float(config.get(key, "") or default)
        except (ValueError, TypeError):
            return default

    def _s(key, default=""):
        return (config.get(key) or default).strip()

    budget      = _f("BUDGET_USD", 10000)
    max_loss    = _f("MAX_LOSS_PCT", 0.5)
    trail_trig  = _f("TRAIL_TRIGGER_PCT", 0.30)
    trail_drop  = _f("TRAIL_DROP_PCT", 0.15)
    base_conf   = _f("STRONG_BUY_CONFIDENCE", 0.75)
    panic_conf  = _f("PANIC_CONFIDENCE", base_conf)
    earn_maxloss = _f("EARNINGS_MAX_LOSS_PCT", 0.0)
    stock_max   = _f("STOCK_MAX_PCT", 0.0)
    # ★ v3.9.73: B群は「1=1%」に統一。旧小数(0<値<0.05)が残っていれば%へ正規化して判定。
    if 0 < trail_trig < 0.05:  trail_trig *= 100
    if 0 < trail_drop < 0.05:  trail_drop *= 100
    if 0 < earn_maxloss < 0.05: earn_maxloss *= 100

    # ① クォートで囲まれたAPIキー
    for key in ["ANTHROPIC_API_KEY", "FINNHUB_API_KEY",
                "ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY", "DISCORD_WEBHOOK_URL"]:
        val = _s(key)
        if _check_quoted(val):
            warnings.append({
                "level": "error", "key": key,
                "message": [
                    key + " の値がクォート（引用符）で囲まれています。",
                    # ★ v1.8: キー本体を画面に出さずマスク表示（漏洩防止）
                    "  現在: " + _mask_key(val),
                    "  クォートを外して入力し直してください。",
                ],
                "prompt": key + " を再入力（クォートなし）",
                "validate": lambda v, k=key: not _check_quoted(v) and len(v) > 0,
            })

    # ② Anthropic APIキー形式
    anthropic_key = _s("ANTHROPIC_API_KEY")
    if anthropic_key and not anthropic_key.startswith("sk-ant-"):
        warnings.append({
            "level": "error", "key": "ANTHROPIC_API_KEY",
            "message": [
                "ANTHROPIC_API_KEY の形式が正しくない可能性があります。",
                "  正しいキーは sk-ant- で始まります。",
                "  現在の値: " + _mask_key(anthropic_key),
            ],
            "prompt": "ANTHROPIC_API_KEY を再入力",
            "validate": lambda v: v.startswith("sk-ant-"),
        })

    # ③ Finnhub形式
    finnhub_key = _s("FINNHUB_API_KEY")
    if finnhub_key and (len(finnhub_key) < 15 or not re.match(r'^[a-z0-9]+$', finnhub_key)):
        warnings.append({
            "level": "warning", "key": "FINNHUB_API_KEY",
            "message": [
                "FINNHUB_API_KEY の形式が通常と異なります。",
                "  正しいキーは英小文字・数字のみ・20文字前後です。",
                "  現在の値: " + _mask_key(finnhub_key),
            ],
            "prompt": "FINNHUB_API_KEY を再入力",
            "validate": lambda v: len(v) >= 15,
        })

    # ④ Alpaca Key ID
    alpaca_id = _s("ALPACA_API_KEY_ID")
    if alpaca_id and not alpaca_id.startswith("PK"):
        warnings.append({
            "level": "warning", "key": "ALPACA_API_KEY_ID",
            "message": [
                "ALPACA_API_KEY_ID の形式が通常と異なります。",
                "  正しいキーは PK で始まります。",
                "  現在の値: " + _mask_key(alpaca_id),
            ],
            "prompt": "ALPACA_API_KEY_ID を再入力",
            "validate": lambda v: v.startswith("PK"),
        })

    # ⑤ Discord Webhook URL
    discord_url = _s("DISCORD_WEBHOOK_URL")
    if discord_url and not _is_discord_webhook(discord_url):
        warnings.append({
            "level": "warning", "key": "DISCORD_WEBHOOK_URL",
            "message": [
                "DISCORD_WEBHOOK_URL の形式が正しくない可能性があります。",
                "  正しいURLは https://discord.com/api/webhooks/ で始まります。",
                "  ※ 入力値は上記の形式で始まっていません（URL末尾にトークンを含むため値は表示しません）。",
            ],
            "prompt": "DISCORD_WEBHOOK_URL を再入力",
            "validate": lambda v: _is_discord_webhook(v),
        })

    # ⑥ MAX_LOSS_PCT 単位誤り（%指定なのに10超は確実に誤り）
    if max_loss > 10:
        warnings.append({
            "level": "error", "key": "MAX_LOSS_PCT",
            "message": [
                "MAX_LOSS_PCT = " + str(max_loss) + " は大きすぎます。",
                "  この項目は %単位 で設定します（例: 0.50 = 0.5%）。",
                "  " + str(max_loss) + " と入力すると " + str(max_loss) + "% の損切りになります。",
                "  1回の最大損失: $" + f"{budget * max_loss / 100:,.0f}",
            ],
            "prompt": "MAX_LOSS_PCT を再入力（例: 0.50）",
            "validate": lambda v: 0 < float(v) <= 10,
        })

    # ⑦ TRAIL_TRIGGER_PCT 過大（v3.9.73: 「1 = 1%」表記。5%超は過大）
    if trail_trig > 5:
        warnings.append({
            "level": "error", "key": "TRAIL_TRIGGER_PCT",
            "message": [
                "TRAIL_TRIGGER_PCT = " + str(trail_trig) + " は大きすぎます。",
                "  この項目は「1 = 1%」で設定します（例: 0.30 = 0.30%）。",
                "  " + str(trail_trig) + " と入力すると " + f"{trail_trig:.2f}%" + " 上昇後にトレール開始です。",
            ],
            "prompt": "TRAIL_TRIGGER_PCT を再入力（例: 0.30）",
            "validate": lambda v: 0 < float(v) <= 5,
        })

    # ⑧ TRAIL_DROP_PCT 過大
    if trail_drop > 5:
        warnings.append({
            "level": "error", "key": "TRAIL_DROP_PCT",
            "message": [
                "TRAIL_DROP_PCT = " + str(trail_drop) + " は大きすぎます。",
                "  この項目は「1 = 1%」で設定します（例: 0.15 = 0.15%）。",
            ],
            "prompt": "TRAIL_DROP_PCT を再入力（例: 0.15）",
            "validate": lambda v: 0 < float(v) <= 5,
        })

    # ⑨ トレール論理矛盾（幅 >= 発動）
    if 0 < trail_drop >= trail_trig:
        warnings.append({
            "level": "warning", "key": "TRAIL_DROP_PCT",
            "message": [
                "トレール幅 >= 発動しきい値 になっています。",
                "  発動: +" + f"{trail_trig:.2f}%" + "  /  幅: " + f"{trail_drop:.2f}%",
                "  発動直後に即決済される恐れがあります。",
                "  標準設定: トレール幅 < 発動しきい値",
            ],
            "prompt": "TRAIL_DROP_PCT を再入力（例: 0.15）",
            "validate": lambda v: 0 < float(v) < trail_trig,
        })

    # ⑪ MAX_LOSS_PCT 極端値（広すぎ）
    if 3.0 < max_loss <= 10:
        loss_usd = budget * max_loss / 100
        warnings.append({
            "level": "warning", "key": "MAX_LOSS_PCT",
            "message": [
                "MAX_LOSS_PCT = " + f"{max_loss}%" + " は広めの損切りラインです。",
                "  1回あたり最大 $" + f"{loss_usd:,.0f}" + " の損失が発生します。",
                "  標準的な範囲は 0.30〜1.00% です。",
            ],
            "prompt": "MAX_LOSS_PCT を変更（Enterでスキップ）",
            "validate": None,
        })

    # ⑫ MAX_LOSS_PCT 極端値（狭すぎ）
    if 0 < max_loss < 0.1:
        warnings.append({
            "level": "warning", "key": "MAX_LOSS_PCT",
            "message": [
                "MAX_LOSS_PCT = " + f"{max_loss}%" + " はスプレッドより狭い可能性があります。",
                "  エントリー直後に損切りが連発するリスクがあります。",
                "  標準的な範囲: 0.30〜1.00%",
            ],
            "prompt": "MAX_LOSS_PCT を変更（Enterでスキップ）",
            "validate": None,
        })

    # ⑬ STRONG_BUY_CONFIDENCE 低すぎ
    if base_conf < 0.60:
        warnings.append({
            "level": "warning", "key": "STRONG_BUY_CONFIDENCE",
            "message": [
                "STRONG_BUY_CONFIDENCE = " + str(base_conf) + " は低すぎる可能性があります。",
                "  誤発注リスクが高まります。標準的な範囲: 0.65〜0.80",
            ],
            "prompt": "STRONG_BUY_CONFIDENCE を変更（Enterでスキップ）",
            "validate": None,
        })

    # ⑭ STRONG_BUY_CONFIDENCE 高すぎ
    if base_conf > 0.95:
        warnings.append({
            "level": "warning", "key": "STRONG_BUY_CONFIDENCE",
            "message": [
                "STRONG_BUY_CONFIDENCE = " + str(base_conf) + " は非常に高い設定です。",
                "  ほぼエントリーしない設定になります。標準的な範囲: 0.70〜0.85",
            ],
            "prompt": "STRONG_BUY_CONFIDENCE を変更（Enterでスキップ）",
            "validate": None,
        })

    # ⑮ PANIC_CONFIDENCE がベースより低い
    if 0 < panic_conf < base_conf:
        warnings.append({
            "level": "warning", "key": "PANIC_CONFIDENCE",
            "message": [
                "PANIC_CONFIDENCE (" + str(panic_conf) + ") がベース (" + str(base_conf) + ") より低い設定です。",
                "  パニック判定がベース判定より先に発動してしまいます。",
                "  標準設定: PANIC_CONFIDENCE >= STRONG_BUY_CONFIDENCE",
            ],
            "prompt": "PANIC_CONFIDENCE を変更（Enterでスキップ）",
            "validate": None,
        })

    # ⑯ 時間帯別Confidenceがベースより低い
    session_checks = [
        ("CONFIDENCE_PREMARKET",  "CONFIDENCE_PREMARKET",  "プリマーケット"),
        ("CONFIDENCE_AFTERHOURS", "CONFIDENCE_AFTERHOURS", "アフターアワーズ"),
        ("CONFIDENCE_OVERNIGHT",  "CONFIDENCE_OVERNIGHT",  "オーバーナイト"),
    ]
    for key, env_key, label in session_checks:
        raw = config.get(env_key, "")
        if raw:
            try:
                val = float(raw)
                if val < base_conf:
                    warnings.append({
                        "level": "warning", "key": key,
                        "message": [
                            key + " = " + str(val) + " がベース (" + str(base_conf) + ") より低い設定です。",
                            "  流動性の低い" + label + "でのリスクが高まります。",
                            "  標準設定: ベース以上",
                        ],
                        "prompt": key + " を変更（Enterでスキップ）",
                        "validate": None,
                    })
            except ValueError:
                pass

    # ⑰ EARNINGS_MAX_LOSS_PCT 過大（v3.9.73: 「1 = 1%」表記。50%超は過大）
    if earn_maxloss > 50:
        warnings.append({
            "level": "error", "key": "EARNINGS_MAX_LOSS_PCT",
            "message": [
                "EARNINGS_MAX_LOSS_PCT = " + str(earn_maxloss) + " は大きすぎます。",
                "  この項目は「1 = 1%」で設定します（例: 3 = 3%）。",
            ],
            "prompt": "EARNINGS_MAX_LOSS_PCT を再入力（例: 3）",
            "validate": lambda v: 0 <= float(v) <= 50,
        })

    # ⑱ BUDGET_USD が大きすぎる
    if budget > 100_000:
        warnings.append({
            "level": "warning", "key": "BUDGET_USD",
            "message": [
                "BUDGET_USD = $" + f"{budget:,.0f}" + " は非常に大きい設定です。",
                "  実口座では1回の取引で大きな損失が発生する可能性があります。",
                "  まずデモ口座で動作確認してから実口座をご検討ください。",
            ],
            "prompt": "BUDGET_USD を変更（Enterでスキップ）",
            "validate": None,
        })

    # ⑲ STOCK_MAX_PCT 単位誤り（1以下は%として小さすぎ）
    if 0 < stock_max <= 1.0:
        warnings.append({
            "level": "warning", "key": "STOCK_MAX_PCT",
            "message": [
                "STOCK_MAX_PCT = " + str(stock_max) + " は " + str(stock_max) + "% の設定です（$" + f"{budget * stock_max / 100:,.0f}" + "/銘柄）。",
                "  この項目は %単位 で設定します（例: 20 = 20%）。",
                "  $" + f"{budget * 20 / 100:,.0f}" + "/銘柄 なら 20 と入力してください。",
            ],
            "prompt": "STOCK_MAX_PCT を変更（例: 20）",
            "validate": None,
        })

    return warnings


def step_review_warnings(config):
    while True:
        warnings = _collect_warnings(config)
        errors = [w for w in warnings if w["level"] == "error"]
        warns  = [w for w in warnings if w["level"] == "warning"]
        all_issues = errors + warns

        print()
        print("  " + bold("══ ⚠️  設定チェック結果 ══════════════════════════════"))
        print()

        if not all_issues:
            print("  " + green("✅  問題は見つかりませんでした"))
            print()
            break

        parts = []
        if errors:
            parts.append(red("❌ エラー " + str(len(errors)) + "件"))
        if warns:
            parts.append(yellow("⚠️  警告 " + str(len(warns)) + "件"))
        print("  " + "  ".join(parts))
        print()

        for i, w in enumerate(all_issues, 1):
            icon = red("❌") if w["level"] == "error" else yellow("⚠️ ")
            print("  " + icon + " [" + str(i) + "] " + w["message"][0])
            for line in w["message"][1:]:
                print("        " + dim(line))
            print()

        print(dim("  " + "─" * 56))
        print()

        if errors:
            print("  " + red(bold("❌ エラーがあります。保存前に修正してください。")))
            print()

        if warns and not errors:
            print("  " + yellow("上記は注意事項です（意図的な設定なら問題ありません）。"))
            print()
            if ask_yn("このまま保存を続けますか？", default=False):
                break

        fixable = [w for w in all_issues if w.get("key")]
        if not fixable:
            break

        print("  修正する項目を選んでください " + dim("（0 = スキップして保存へ）") + "\n")
        for i, w in enumerate(fixable, 1):
            icon = red("[E]") if w["level"] == "error" else yellow("[W]")
            print("    " + icon + " [" + str(i) + "] " + w["key"])
        if not errors:
            print("        " + dim("[0] このまま保存する"))
        print()

        while True:
            raw = ask("番号を入力", default="")
            if not raw:
                continue
            if raw == "0" and not errors:
                return config
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(fixable):
                    break
            except ValueError:
                pass
            warn("1〜" + str(len(fixable)) + " の番号を入力してください")

        target = fixable[idx]
        key    = target["key"]
        cur    = config.get(key, "")

        print()
        # 機密キーはマスク表示、それ以外は通常表示
        if key in _SENSITIVE_KEYS:
            print("  現在の値: " + (_mask_key(cur) if cur else dim("（未設定）")))
        else:
            print("  現在の値: " + yellow(str(cur)))

        # 機密キーは ask(secret=True) でマスク表示入力
        is_secret = key in _SENSITIVE_KEYS
        if is_secret:
            # ★ v1.3: getpass.getpass() を ask(secret=True) に統一（マスク表示対応）
            new_val = ask(target["prompt"], secret=True, default="").strip()
        else:
            new_val = ask(target["prompt"], default="").strip()

        if new_val:
            validate = target.get("validate")
            if validate is None:
                # ★ v1.38: validate 未指定でも数値キーは既定の範囲チェックを適用
                validate = _default_validator_for(key)
            valid = True
            if validate:
                try:
                    valid = validate(new_val)
                except Exception:
                    valid = False
            if valid:
                config[key] = new_val
                display_val = _mask_key(new_val) if key in _SENSITIVE_KEYS else new_val
                ok(key + " を更新しました → " + display_val)
            else:
                warn("入力値が正しくありません。変更はスキップしました。")
        else:
            info("変更をスキップしました。")

    return config


def step_confirm(config):
    clear()
    print(f"\n  {bold('設定内容の確認')}\n")
    hr()
    print()
    timeout_val   = config.get("TIMEOUT_EXIT_MINUTES", "10")
    timeout_label = "無効" if timeout_val == "0" else f"{timeout_val}分"
    # ★ v3.9.73: 値は「1=1%」表記。旧小数(<0.05)が残っていれば×100で表示補正。
    def _disp_pct(v, dflt):
        try:
            x = float(config.get(v, dflt))
        except (ValueError, TypeError):
            x = float(dflt)
        return x * 100 if 0 < x < 0.05 else x
    trig_pct = _disp_pct("TRAIL_TRIGGER_PCT", "0.22")   # ★ v1.38 新標準
    drop_pct = _disp_pct("TRAIL_DROP_PCT", "0.15")
    # ★ v1.39: 未設定（空）＝ETF 0.30% / 個別株 0.50% を銘柄タイプで使い分け
    _buf_auto = not str(config.get("LIMIT_BUFFER_PCT", "") or "").strip()
    buf_pct  = None if _buf_auto else _disp_pct("LIMIT_BUFFER_PCT", "0.50")

    def _sess_label(val):
        """confidence値をラベルに変換"""
        if not val or val == "":
            return "ベースと同じ"
        try:
            f = float(val)
            if f >= 2.0:
                return "発注しない"
            return val
        except ValueError:
            return val

    pre   = config.get("CONFIDENCE_PREMARKET", "")
    after = config.get("CONFIDENCE_AFTERHOURS", "")
    ovn   = config.get("CONFIDENCE_OVERNIGHT", "")
    close_before = config.get("CLOSE_BEFORE_INACTIVE", "")

    def _any_session_disabled():
        """いずれかのセッションが「発注しない」(2.00) か確認する"""
        for k in ("CONFIDENCE_PREMARKET", "CONFIDENCE_AFTERHOURS", "CONFIDENCE_OVERNIGHT"):
            v = config.get(k, "")
            try:
                if v and float(v) >= 2.0:
                    return True
            except ValueError:
                pass
        return False

    any_disabled = _any_session_disabled()

    groups = [
        ("── 資金・リスク ─────────────────────────────", None, None),
        ("BUDGET_USD",            f"${float(config.get('BUDGET_USD','0')):,.0f}",     "予算"),
        ("MAX_LOSS_PCT",          f"{config.get('MAX_LOSS_PCT','')} %",               "損切りライン"),
        ("TIMEOUT_EXIT_MINUTES",  timeout_label,                                          "時間切れ決済"),
        # ★ v1.44: .1f だと 0.22%→"0.2%"・0.15%→"0.1%" と丸まり、設定した値と
        #   食い違って見える（本体のバナーと同じ不具合。STEP3 の入力画面は
        #   もともと .2f なので、同じ実行の中で表示が矛盾していた）。
        ("TRAIL_TRIGGER_PCT",     f"+{trig_pct:.2f}% でトレール開始",                    "トレール発動"),
        ("TRAIL_DROP_PCT",        f"最高値から {drop_pct:.2f}% 下落で決済",              "トレール幅"),
        ("── AIしきい値 ──────────────────────────────", None, None),
        ("STRONG_BUY_CONFIDENCE", config.get("STRONG_BUY_CONFIDENCE",""),                "ベース（RTH）"),
        ("PANIC_CONFIDENCE",      config.get("PANIC_CONFIDENCE",""),                     "パニック売り"),
        ("── 時間帯別トレード設定 ────────────────────", None, None),
        ("CONFIDENCE_PREMARKET",  _sess_label(pre),                                      "プリマーケット"),
        ("CONFIDENCE_AFTERHOURS", _sess_label(after),                                    "アフターアワーズ"),
        ("CONFIDENCE_OVERNIGHT",  _sess_label(ovn),                                      "オーバーナイト"),
        ("CLOSE_BEFORE_INACTIVE",
            ("ON" if close_before == "true" else "OFF") if any_disabled else "—（発注しないセッションなし）",
            "移行前全決済"),
        ("── 銘柄・発注詳細 ──────────────────────────", None, None),
        ("TRIGGER_TICKERS",       config.get("TRIGGER_TICKERS",""),                      "ニュース駆動の銘柄"),
        ("MOMENTUM実発注",        _fmt_momentum_sides(config.get("MOMENTUM_ENABLED_SIDES","")), "モメンタムの売買銘柄（別系統）"),
        ("STOCK_TICKERS",         config.get("STOCK_TICKERS","") or "なし",               "個別銘柄監視"),
        ("LIMIT_BUFFER_PCT",      ("ETF 0.30% / 個別株 0.50%" if buf_pct is None else f"{buf_pct:.2f}%（一律）"), "指値バッファ"),
        ("ORDER_CANCEL_MINUTES",  f"{config.get('ORDER_CANCEL_MINUTES','1')}分",     "未約定キャンセル"),
        ("発注サイズ",            "confに応じて発注額を自動配分（山型）",                  "v3.9.20"),
        ("── APIキー ─────────────────────────────────", None, None),
        ("ANTHROPIC_API_KEY",     "✅ 設定済み" if config.get("ANTHROPIC_API_KEY") else "❌ 未設定", ""),
        ("ALPACA_API_KEY_ID",     "✅ 設定済み" if config.get("ALPACA_API_KEY_ID") else "— 未設定（任意）", ""),
        ("FINNHUB_API_KEY",       "✅ 設定済み" if config.get("FINNHUB_API_KEY") else "— 未設定（任意）", ""),
        ("DISCORD_WEBHOOK_URL",    "✅ 設定済み" if config.get("DISCORD_WEBHOOK_URL") else "— 未設定（任意）通知なしで動作", ""),
        ("── moomoo接続 ──────────────────────────────", None, None),
        ("MOOMOO_HOST/PORT",      f"{config.get('MOOMOO_HOST')}:{config.get('MOOMOO_PORT')}", ""),
    ]
    for key, val, note in groups:
        if val is None:
            print(f"\n  {dim(key)}")
        else:
            note_str = f"  {dim(note)}" if note else ""
            print(f"    {_pad(blue(key), 42)} {green(str(val))}{note_str}")
    print()
    # 保存確認は main() 内の step_review_warnings() の後で実施
    return True


# Wizardが明示的に管理するキー一覧
_WIZARD_MANAGED_KEYS = {
    "BUDGET_USD", "MAX_LOSS_PCT", "TIMEOUT_EXIT_MINUTES",
    "TRAIL_TRIGGER_PCT", "TRAIL_DROP_PCT",
    "STRONG_BUY_CONFIDENCE", "PANIC_CONFIDENCE",
    "CONFIDENCE_RTH", "CONFIDENCE_PREMARKET", "CONFIDENCE_AFTERHOURS", "CONFIDENCE_OVERNIGHT",
    "CLOSE_BEFORE_INACTIVE",
    "TRIGGER_TICKERS", "STOCK_TICKERS",
    "LIMIT_BUFFER_PCT", "ORDER_CANCEL_MINUTES",
    # v1.5 (v3.9.20): PYRAMID_* は撤去 (山型サイズ配分に置き換え)
    "ANTHROPIC_API_KEY", "DISCORD_WEBHOOK_URL",
    "FINNHUB_API_KEY",
    "ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY",
    "MOOMOO_HOST", "MOOMOO_PORT", "MOOMOO_RSA_KEY", "MOOMOO_ACC_ID",
    "DATA_COLLECT", "STUDENT_NAME",
    # v1.6 (v3.9.25): モメンタム発注設定 / v1.8: 動作モード + 最大発注比率
    # v1.11 (v3.9.63): MOMENTUM_STOP_LOSS_PCT (モメンタム建玉の強制損切り)
    "MOMENTUM_LEVEL", "MOMENTUM_RISK_LEVEL", "MOMENTUM_MAX_PCT",
    "MOMENTUM_STOP_LOSS_PCT",
    # v1.34 (v3.9.114): 損切り幅プロファイル（ボラ別）＋ロング発注レンジ（5分・下限/上限）
    "MOMENTUM_STOP_PROFILE",
    "MOMENTUM_LONG_MIN_SIGNAL_PCT", "MOMENTUM_LONG_MAX_SIGNAL_PCT",
    # v1.22 (v3.9.85) で追加 → v1.23 (v3.9.90) から既定 true=建玉トレールが標準
    "MOMENTUM_TRAIL_FROM_ENTRY",
    # v1.38: 発注前の個別株トレンドチェック（新標準 ±0.3/±0.9。旧 ±0.7/±1.5 は発火せず実質無効だった）
    "STOCK_DOWNTREND_15M_PCT", "STOCK_DOWNTREND_60M_PCT",
    "STOCK_UPTREND_15M_PCT", "STOCK_UPTREND_60M_PCT",
    # v1.35 (v3.9.116): 戦略プロファイル (standard / select_v1)
    "MOMENTUM_STRATEGY_PROFILE",
    "MOMENTUM_SHADOW_ENABLED", "MOMENTUM_LIVE_TRADING",
    # v1.12 (v3.9.65): デモ・ネッティング空売り (上級者向け・.env 直接編集)
    "DEMO_SHORT_ENABLED", "REAL_SHORT_ENABLED",
    # v1.14 (v3.9.70): 実発注対象サイドを Wizard で明示
    "MOMENTUM_ENABLED_SIDES",
    # v1.4 (v3.9.19): アラート音設定
    "ENABLE_ALERT_SOUND", "ALERT_SOUND_COOLDOWN_SEC",
    "ALERT_SOUND_QUIET_HOURS", "ALERT_SOUND_FILE_MACOS",
    "WIZARD_COMPLETED",
}


def _get_wizard_value(key, config):
    """Wizardが書き出す値を返す（キー別の特殊処理を含む）。"""
    if key == "TRIGGER_TICKERS":
        return config.get("TRIGGER_TICKERS_STR", config.get("TRIGGER_TICKERS", "SPY,QQQ"))
    if key == "WIZARD_COMPLETED":
        return "true"
    if key == "PANIC_CONFIDENCE":
        base = config.get("STRONG_BUY_CONFIDENCE", "0.70")  # ★ v1.38: STEP4 の既定 0.70 に統一
        return config.get("PANIC_CONFIDENCE", base)
    return config.get(key, "")


def _build_env_lines_merged(config):
    """
    既存の .env をベースに、Wizardが管理するキーだけ値を差し替えて返す。
    - コメント行・空行・非管理キー: そのまま維持
    - Wizardが管理するキー: 新しい値に書き換え
    - 既存ファイルに存在しないWizardキー: 末尾に追記
    - .env が存在しない場合: 従来の _build_env_lines で新規生成
    - 生成日時コメントは更新
    """
    if not os.path.exists(ENV_PATH):
        return _build_env_lines(config)

    with open(ENV_PATH, encoding="utf-8") as f:
        raw_lines = f.readlines()

    result = []
    written_keys = set()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for raw in raw_lines:
        line = raw.rstrip("\n").rstrip("\r")

        # 生成日時コメントは更新
        if line.startswith("# 生成日時:"):
            result.append("# 生成日時: " + now_str)
            continue

        # 空行・コメント行はそのまま
        if not line.strip() or line.strip().startswith("#"):
            result.append(line)
            continue

        # KEY=value 行の解析
        if "=" in line and not line.strip().startswith("#"):
            key, _, _ = line.partition("=")
            key = key.strip()

            if key in _WIZARD_MANAGED_KEYS:
                new_val = _get_wizard_value(key, config)
                result.append(key + "=" + new_val)
                written_keys.add(key)
            else:
                # 非管理キー: そのまま
                result.append(line)
        else:
            result.append(line)

    # 既存ファイルになかったWizardキーを末尾に追記
    missing = [k for k in _WIZARD_MANAGED_KEYS if k not in written_keys and _get_wizard_value(k, config)]
    if missing:
        result.append("")
        result.append("# ── Wizardによる追加設定 ──────────────────────────────")
        for key in sorted(missing):
            result.append(key + "=" + _get_wizard_value(key, config))

    return result

def _build_env_lines(config):
    tickers = config.get("TRIGGER_TICKERS_STR", config.get("TRIGGER_TICKERS", "SPY,QQQ"))
    base_conf = config.get("STRONG_BUY_CONFIDENCE", "0.70")
    return [
        "# ══════════════════════════════════════════════════",
        "# moomoo_trade_v1.py 設定ファイル",
        f"# 生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# ══════════════════════════════════════════════════",
        "",
        "# ── 資金管理 ────────────────────────────────────",
        f"BUDGET_USD={config.get('BUDGET_USD', '10000')}",
        f"MAX_LOSS_PCT={config.get('MAX_LOSS_PCT', '0.30')}",
        f"TIMEOUT_EXIT_MINUTES={config.get('TIMEOUT_EXIT_MINUTES', '10')}",
        "",
        "# ── トレイリングストップ ─────────────────────────",
        "#   発動 0.22% は v1.38 新標準（全期間集計の反実仮想で旧0.30%より改善・近似・非保証）",
        f"TRAIL_TRIGGER_PCT={config.get('TRAIL_TRIGGER_PCT', '0.22')}",
        f"TRAIL_DROP_PCT={config.get('TRAIL_DROP_PCT', '0.15')}",
        "",
        "# ── 発注前の個別株トレンドチェック (v1.38 新標準) ──────",
        "#   ニュース駆動の個別株について、直近15分/60分の騰落がこの閾値を超えて",
        "#   逆風のときは新規発注を見送る（LONG=下落時 / SHORT=上昇時にブロック）。",
        "#   旧標準 ±0.7/±1.5 は全期間でほぼ発火せず実質無効だったため、",
        "#   実測に基づき ±0.3/±0.9 に変更（15分実測: 新ブロック帯の実損益はマイナス）。",
        f"STOCK_DOWNTREND_15M_PCT={config.get('STOCK_DOWNTREND_15M_PCT', '-0.3')}",
        f"STOCK_DOWNTREND_60M_PCT={config.get('STOCK_DOWNTREND_60M_PCT', '-0.9')}",
        f"STOCK_UPTREND_15M_PCT={config.get('STOCK_UPTREND_15M_PCT', '0.3')}",
        f"STOCK_UPTREND_60M_PCT={config.get('STOCK_UPTREND_60M_PCT', '0.9')}",
        "",
        "# ── AI判定しきい値 ──────────────────────────────",
        f"STRONG_BUY_CONFIDENCE={base_conf}",
        f"PANIC_CONFIDENCE={config.get('PANIC_CONFIDENCE', base_conf)}",
        "",
        "# ── 時間帯別しきい値（空欄=ベースと同じ / 2.00=発注しない）──",
        f"CONFIDENCE_RTH={config.get('CONFIDENCE_RTH', '')}",
        f"CONFIDENCE_PREMARKET={config.get('CONFIDENCE_PREMARKET', '')}",
        f"CONFIDENCE_AFTERHOURS={config.get('CONFIDENCE_AFTERHOURS', '')}",
        f"CONFIDENCE_OVERNIGHT={config.get('CONFIDENCE_OVERNIGHT', '')}",
        f"CLOSE_BEFORE_INACTIVE={config.get('CLOSE_BEFORE_INACTIVE', 'false')}",
        "",
        "# ── 売買銘柄 ────────────────────────────────────",
        f"TRIGGER_TICKERS={tickers}",
        f"STOCK_TICKERS={config.get('STOCK_TICKERS', '')}",
        "",
        "# ── 発注詳細 ────────────────────────────────────",
        "#   指値バッファ: 空＝ETF 0.30% / 個別株 0.50% を銘柄タイプで使い分け（v1.39 新標準）",
        f"LIMIT_BUFFER_PCT={config.get('LIMIT_BUFFER_PCT', '')}",
        f"ORDER_CANCEL_MINUTES={config.get('ORDER_CANCEL_MINUTES', '1')}",
        "# 発注サイズ: confidence の山型配分で自動決定 (v3.9.20 以降)",
        "#   0.60-0.69: 予算×30% / 0.70-0.77: 予算×60%",
        "#   0.78-0.82: 予算×100% (★スイートスポット) / 0.83以上: 予算×40%",
        "",
        "# ── Anthropic API（必須）────────────────────────",
        f"ANTHROPIC_API_KEY={config.get('ANTHROPIC_API_KEY', '')}",
        "",
        "# ── Discord Webhook（任意・通知）────────────────",
        f"DISCORD_WEBHOOK_URL={config.get('DISCORD_WEBHOOK_URL', '')}",
        "",
        "# ── 外部ニュース API（任意）──────────────────────",
        f"FINNHUB_API_KEY={config.get('FINNHUB_API_KEY', '')}",
        "",
        "# ── Alpaca News API（任意・Benzingaリアルタイム）─",
        f"ALPACA_API_KEY_ID={config.get('ALPACA_API_KEY_ID', '')}",
        f"ALPACA_API_SECRET_KEY={config.get('ALPACA_API_SECRET_KEY', '')}",
        "",
        "# ── moomoo OpenD 接続 ───────────────────────────",
        f"MOOMOO_HOST={config.get('MOOMOO_HOST', '127.0.0.1')}",
        f"MOOMOO_PORT={config.get('MOOMOO_PORT', '11111')}",
        f"MOOMOO_RSA_KEY={config.get('MOOMOO_RSA_KEY', '')}",
        f"MOOMOO_ACC_ID={config.get('MOOMOO_ACC_ID', '')}",
        "",
        "",
        "# ── データ収集（任意）──────────────────────────────",
        "# 送信先URLはBot本体に組込み済み。参加/不参加の切替のみ.envで管理。",
        f"DATA_COLLECT={config.get('DATA_COLLECT', 'false')}",
        f"STUDENT_NAME={config.get('STUDENT_NAME', '')}",
        "",
        "# ── デモ口座のショート (Wizard [2-b] で選択・v3.9.68) ──────────",
        "#   true: デモ口座でもショートを実発注 (ネッティング: SELL で建て / BUY で決済)。",
        "#   false: デモのショートは記録のみ (シャドー)。既定 true。",
        f"DEMO_SHORT_ENABLED={config.get('DEMO_SHORT_ENABLED', 'true')}",
        "# ── 実口座のショート (v3.9.69・上級者向け) ──────────",
        "#   true: 実口座でも空売りする (既定)。false: 実口座は買い専用",
        "#   (ニュース駆動・モメンタムの SHORT を全て停止しシャドー記録のみ)。",
        f"REAL_SHORT_ENABLED={config.get('REAL_SHORT_ENABLED', 'true')}",
        "",
        "# ── モメンタム発注設定 (v3.9.25 から、Wizard で選択) ──",
        "#   MOMENTUM_LEVEL       シグナル発火頻度 (1=最厳格 〜 5=最緩和)",
        "#   MOMENTUM_RISK_LEVEL  リスク許容度 (1=超慎重 〜 5=高リスク)",
        "#   MOMENTUM_MAX_PCT     1 回の最大発注額 (BUDGET の %)。シグナル強度で",
        "#                        50/75/100% に山型配分される (強シグナルは発注なし)",
        "#   MOMENTUM_SHADOW_ENABLED  シャドー観察 (true=観察する)",
        "#   MOMENTUM_LIVE_TRADING    実発注 (true=実際に注文・false=シャドーのみ)",
        "#   MOMENTUM_ENABLED_SIDES   実発注対象サイド (Wizard [2-c] で選択・ここに記載)",
        "#                            記載した銘柄:方向のみ実発注。DRAM は観察のみ(非実発注)。",
        "#   MOMENTUM_TRAIL_FROM_ENTRY  損切りの方式 (true=建玉トレール[標準・既定 v1.23〜] /",
        "#                              false=従来の固定損切り・Wizard [6] で選択)",
        "#   MOMENTUM_STRATEGY_PROFILE  戦略プロファイル (select_v1=選抜プロファイル v1[既定 v1.37〜] /",
        "#                              standard=今まで通り・Wizard [0] で選択。",
        "#                              select_v1: SHORTのみ/SPY除外/ET 9・10・12・13時台のみ",
        "#                              実発注/固定損切り/日次損失1.5%停止。シャドー記録は全件継続)",
        "#   MOMENTUM_STOP_LOSS_PCT     モメンタム建玉の強制損切りライン (% ・Wizard [5] で設定)",
        "#   MOMENTUM_STOP_PROFILE      損切り幅プロファイル (モメンタム実発注には効かない・Wizard [5b])",
        "#   MOMENTUM_LONG_MIN/MAX_SIGNAL_PCT  ロング発注の5分モメンタムレンジ (Wizard [2-d] で選択)",
        "# 上級者向けの個別設定 (.env 直接編集・任意):",
        "#   MOMENTUM_SIZE_MULTIPLIER_* (銘柄別サイズ調整)",
        "#   MOMENTUM_REVERSE_EXIT (下記参照)",
        "#   (時間帯フィルタ MOMENTUM_RTH_* は v3.9.41 で廃案 — 旧 .env の値は無視される)",
        f"MOMENTUM_LEVEL={config.get('MOMENTUM_LEVEL', '3')}",
        f"MOMENTUM_RISK_LEVEL={config.get('MOMENTUM_RISK_LEVEL', '3')}",
        f"MOMENTUM_MAX_PCT={config.get('MOMENTUM_MAX_PCT', '80')}",
        f"MOMENTUM_STOP_LOSS_PCT={config.get('MOMENTUM_STOP_LOSS_PCT', '0.50')}",
        f"MOMENTUM_STOP_PROFILE={config.get('MOMENTUM_STOP_PROFILE', 'standard')}",
        f"MOMENTUM_LONG_MIN_SIGNAL_PCT={config.get('MOMENTUM_LONG_MIN_SIGNAL_PCT', '0.70')}",
        f"MOMENTUM_LONG_MAX_SIGNAL_PCT={config.get('MOMENTUM_LONG_MAX_SIGNAL_PCT', '0.80')}",
        f"MOMENTUM_TRAIL_FROM_ENTRY={config.get('MOMENTUM_TRAIL_FROM_ENTRY', 'true')}",
        # ★ v1.38: フォールバックも Wizard 既定の select_v1 に統一（経路による既定の食い違い解消）
        f"MOMENTUM_STRATEGY_PROFILE={config.get('MOMENTUM_STRATEGY_PROFILE', 'select_v1')}",
        f"MOMENTUM_ENABLED_SIDES={config.get('MOMENTUM_ENABLED_SIDES', 'SPY:BUY,SPY:SELL_SHORT,QQQ:BUY,QQQ:SELL_SHORT,SMH:SELL_SHORT')}",
        f"MOMENTUM_SHADOW_ENABLED={config.get('MOMENTUM_SHADOW_ENABLED', 'true')}",
        f"MOMENTUM_LIVE_TRADING={config.get('MOMENTUM_LIVE_TRADING', 'false')}",
        "# ── 反対シグナルでの転換 (上級者向け・v3.9.89) ──────────",
        "#   false: 保有中に反対シグナルが出ても転換せず見送る (既定・実データで転換は勝率が低いため)",
        "#   true : 従来どおり反対シグナルで強制転換する",
        f"MOMENTUM_REVERSE_EXIT={config.get('MOMENTUM_REVERSE_EXIT', 'false')}",
        "",
        "# ── アラート音 (v3.9.19 から、上級者向け・任意) ──",
        f"ENABLE_ALERT_SOUND={config.get('ENABLE_ALERT_SOUND', 'false')}",
        f"ALERT_SOUND_COOLDOWN_SEC={config.get('ALERT_SOUND_COOLDOWN_SEC', '60')}",
        f"ALERT_SOUND_QUIET_HOURS={config.get('ALERT_SOUND_QUIET_HOURS', '')}",
        f"ALERT_SOUND_FILE_MACOS={config.get('ALERT_SOUND_FILE_MACOS', '/System/Library/Sounds/Sosumi.aiff')}",
        "",
        "# ── ウィザード完了マーク（削除しないでください）──",
        "WIZARD_COMPLETED=true",
    ]

def step_save(config):
    clear()
    print(f"\n  {bold('保存・完了')}\n")
    hr()
    print()
    _backup_env()
    # 既存の.envにある項目でconfigに未設定のものを引き継ぐ
    # （Wizardで扱わない項目が消えないようにする）
    _existing = _load_existing_env()
    for _k, _v in _existing.items():
        if _k not in config:
            config[_k] = _v
    # ★ v1.38: 発注前の個別株トレンドチェック新標準（未設定の場合のみ書き出す。
    #   手動で設定済みの値は上の merge で config に入っているため上書きしない）。
    #   旧 ±0.7/±1.5 は全期間でほぼ発火せず実質無効 → 実測に基づき ±0.3/±0.9 へ。
    _trend_defaults = (
        ("STOCK_DOWNTREND_15M_PCT", "-0.3"),
        ("STOCK_DOWNTREND_60M_PCT", "-0.9"),
        ("STOCK_UPTREND_15M_PCT",   "0.3"),
        ("STOCK_UPTREND_60M_PCT",   "0.9"),
    )
    _trend_added = [k for k, _ in _trend_defaults if not str(config.get(k, "")).strip()]
    for _k, _dv in _trend_defaults:
        if not str(config.get(_k, "")).strip():
            config[_k] = _dv
    if _trend_added:
        info("v1.38 新標準: 発注前トレンドチェック ±0.3%(15分)/±0.9%(60分) を書き出します"
             "（実測に基づく変更・手動設定済みの値は維持されます）。")
    # ★ v1.9 (Bot v3.9.42 連動): 機密キー / Webhook URL を保存前にサニタイズ。
    # コピペで混入したスマートクォート / 全角スペース / 日本語コメント等の
    # 非 ASCII 文字を除去する。ANTHROPIC_API_KEY が汚染されたまま保存される
    # と httpx が ASCII エンコードで失敗し AI 呼出が全件死ぬ。
    _SANITIZE_KEYS = (
        "ANTHROPIC_API_KEY", "FINNHUB_API_KEY",
        "ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY",
        "DISCORD_WEBHOOK_URL",
    )
    for _key in _SANITIZE_KEYS:
        if _key in config and config[_key]:
            _clean, _dropped = _sanitize_api_key(config[_key], _key)
            if _dropped > 0:
                config[_key] = _clean
    lines = _build_env_lines_merged(config)
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    success(f".env を保存しました: {ENV_PATH}")
    print()
    hr()
    print()
    # OS別にpythonコマンド名を切り替え（Windowsは"python"、Mac/Linuxは"python3"）
    _py_cmd = "python" if os.name == "nt" else "python3"
    _live_cmd = f"{_py_cmd} moomoo_trade_v1.py --live"
    _demo_cmd = f"{_py_cmd} moomoo_trade_v1.py"
    # デモ行を実口座行と同じ長さにパディングして矢印を揃える
    _demo_padded = _demo_cmd.ljust(len(_live_cmd))
    print(f"  {bold('起動コマンド')}\n")
    print(f"  {cyan(_live_cmd)}  ← 実口座\n")
    print(f"  {cyan(_demo_padded)}  ← デモ口座\n")
    print(f"  {bold('起動前チェックリスト')}\n")
    for c in [
        ".env ファイルを moomoo_trade_v1.py と同じフォルダに保存した",
        "moomoo アプリが起動し、実口座にログインしている",
        "OpenD が起動している（ポート 11111）",
        "取引ロックが発生した場合は moomoo アプリで手動でアンロックしてください",
    ]:
        print(f"  {green('□')} {c}")
    print()

def main():
    existing = _load_existing_env()

    # ── 統一起動画面 ────────────────────────────────────────────────────
    clear()
    print(f"\n  {bold('⚙  アルゴ取引プログラム  セットアップウィザード')}")
    print(f"  {dim('setup_wizard.py  ' + WIZARD_VERSION + '  ｜  全 ' + str(TOTAL) + ' STEP')}\n")
    hr()
    print()

    if existing:
        print(f"  {green('✓')}  {green('既存の .env を検出しました')}")
        print(f"  {bold('現在の設定を引き継ぎながら変更できます。')}")
    else:
        print(f"  {yellow('!')}  初回セットアップです。")
        print(f"  {bold('.env ファイルを新規作成します。')}")

    print(f"  {dim('変更しない項目は Enter でスキップできます。')}\n")

    step_labels = [
        " 1  BUDGET        発注上限額",
        " 2  RISK          損切り・リスク管理",
        " 3  TRAILING      トレイリングストップ",
        " 4  AI THRESHOLD  AIしきい値（ベース・RTH）",
        " 5  SESSION       時間帯別トレード設定",
        " 6  SYMBOLS       銘柄選択",
        " 7  ORDER         発注詳細",
        " 8  ANTHROPIC     Claude APIキー",
        " 9  ALPACA        Alpaca News API",
        "10  FINNHUB       Finnhub（ニュース）＋ Discord通知（任意）",
        "11  MOOMOO        moomoo OpenD 接続",
        "12  DATA COLLECT  取引データ収集への参加（任意）",
        "13  MOMENTUM      モメンタム発注設定（実発注の対象を決める重要設定）",
        "14  ALERT SOUND   重大エラー時のアラート音（任意）",
    ]
    for lbl in step_labels:
        print(f"  {dim(lbl)}")
    print()
    hr()
    print()
    try:
        input(f"  {dim('Enter キーで STEP 1 から開始...')}")
    except (KeyboardInterrupt, EOFError):
        print("\n\n  " + yellow("キャンセルしました。"))
        sys.exit(0)

    # ─────────────────────────────────────────────────────────────
    # ★ v1.26: ステップを「戻る」対応のループ方式に変更。
    #   - 各ステップは直前までの入力値(state)を `existing` 引数として受け取り、
    #     再入力時は前回値が既定値として表示される（やり直しが容易）。
    #   - 各ステップ末尾の next_step_pause() で 'b' を入力すると _GoBack を送出し、
    #     ひとつ前のステップへ戻る（先頭STEPでは戻る選択肢を出さない）。
    #   - ステップ間の依存（予算・ベース自信度）は state から都度参照。
    # ─────────────────────────────────────────────────────────────
    global _WIZARD_CAN_GO_BACK

    def _step1(s):  return {"BUDGET_USD": step1_budget(s)}
    def _step2(s):  return step2_risk(s, s.get("BUDGET_USD", 0))
    def _step3(s):  return step3_trailing(s)
    def _step4(s):  return step4_confidence(s)
    def _step5(s):  return step5_session(s, s.get("STRONG_BUY_CONFIDENCE", ""))
    def _step6(s):  return step6_symbols(s)
    def _step7(s):  return step7_order_detail(s)
    def _step8(s):  return {"ANTHROPIC_API_KEY": step8_anthropic(s)}
    def _step9(s):  return step9_alpaca(s)
    def _step10(s): return step10_finnhub(s)
    def _step11(s):
        r = step11_connection(s)
        r["MOOMOO_RSA_KEY"] = s.get("MOOMOO_RSA_KEY", "")
        return r
    def _step12(s): return step_data_collect(s)
    def _step13(s): return step_momentum(s, s.get("BUDGET_USD", 0))
    def _step14(s): return step_alert_sound(s)

    _steps = [_step1, _step2, _step3, _step4, _step5, _step6, _step7,
              _step8, _step9, _step10, _step11, _step12, _step13, _step14]

    state = dict(existing)   # 直前までの入力値（既定値の供給元）
    try:
        i = 0
        while i < len(_steps):
            _WIZARD_CAN_GO_BACK = (i > 0)
            try:
                result = _steps[i](state)
            except _GoBack:
                i = max(0, i - 1)
                continue
            state.update(result or {})
            i += 1
        _WIZARD_CAN_GO_BACK = False

        config = state
        step_confirm(config)
        config = step_review_warnings(config)
        print()
        if ask_yn(".env ファイルを保存しますか？", default=True):
            step_save(config)
        else:
            print()
            warn("保存をキャンセルしました。ウィザードを再度実行してください。")
    except (KeyboardInterrupt, EOFError):
        print("\n\n  " + yellow("キャンセルしました。"))
        sys.exit(0)

if __name__ == "__main__":
    main()

