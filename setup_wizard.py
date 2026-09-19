"""
setup_wizard.py
===============
moomoo_trade_v1.py 用 .env セットアップウィザード（完全版）
最新バージョン: v1.52  最終更新日: 2026-09-15

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
# v1.52 2026-09-15  STEP 14 冒頭の「SPY / QQQ / SMH … 実発注の対象。買い・空売りの両方に対応」を、選抜のときは
#   「監視の対象。実発注する銘柄と方向はプロファイルが絞り込む」と書く（選抜 v2 では SPY と SMH の買いは実発注しない・認定サポーターの報告）。
# v1.51 2026-09-14  選抜を選んだ人向けの案内を出し分けた（認定サポーターの隔離確認の報告・売買条件と保存値は変えない）。
#   ①STEP 7: ニュース選抜が有効なら、ここで選ぶのはそのニュース取引に使う ETF 構成で、選び直しても選抜は解除されないと書く。
#     個別株の欄では、個別株ニュースによる発注はニュース選抜の絞り込みの対象外だと再掲する。
#   ②STEP 7 と STEP 14 の冒頭が、選抜のときも「[2-c] で選ぶ」と案内していた（選抜では [2-c] を尋ねない）。選抜のときは
#     STEP 1 のプロファイルが絞り込むこと、細かく変えるなら STEP 1 でカスタマイズ設定を選ぶことを書く。
#   ③v2 の途中表示「いまの設定で実発注されるサイド」は実発注の確認より前に出るため、実発注オフでも出ていた。
#     「実発注する場合の対象サイド」とし、いまが実発注オフならそう添える。
#   ④v2 の1日の損失上限を「予算の 1.5%」とだけ書いていた。v1 と同じく、リスク許容度の上限（既定 0.5%）と
#     プロファイルの上限（1.5%）を重ねてかけ、先に当たった方で止まると書く（.env の説明も同じ）。
#   ⑤v2 の説明は、変化率の値が取れないときは強さの条件を省いて判定する、と Bot の動きと逆に書いていた。Bot は
#     5分・15分の変化率が取れない銘柄をその回は判定せず見送る（詳細レビューの指摘）。
# v1.50 2026-09-13  モメンタムの選抜プロファイル v2 を STEP 1 で選べるようにした（PAN 指示・Bot v3.9.194 の select_v2）。
#   ①STEP 1 に [3] 選抜プロファイル v2（検証中）を追加し、初めて設定する方の既定を v2 にした。v1 は引き続き選べる。
#   ②v1.49 までは v2 の .env で Enter を押すと黙って v1 に戻っていた。STEP 1 は現在値 select_v2 を [2] と表示し、
#     STEP 14 は選抜なら常に select_v1 を書き戻していたため。いまの値をそのまま保つ。
#   ③v2 は買いも実発注の対象にするが、Wizard の既定の発注サイドに QQQ の買いが無く、v2 に切り替えても買いが
#     届かなかった。v2 の既定は Bot の既定サイドから SMH の買いを外したものにし、既存の設定に QQQ の買いが無いときは
#     自動で加え、加えたことを画面にはっきり出す（PAN 指示）。
#   ④確認画面・.env の説明・STEP 4／6 の選抜判定・実発注サイドの表示を v2 に対応。
# v1.49 2026-09-11  認定サポーターの v1.48 レビュー反映。
#   ①最重要: (Y/N) の欄が全角の「Ｎ」「Ｙ」を既定値として素通りさせていた。日本語入力のまま Ｎ と打つと
#     聞き直しにならず既定の側で進むため、「実発注を有効にします」「OVN取引機能の実売買を有効にします」で
#     止めたつもりが有効のまま保存されうる。NFKC で全角を直し、読めない入力は聞き直す（Enter だけが既定値）。
#   ②「ひとつ前に戻る: b」で全角の「ｂ」が効かず、そのまま次の STEP へ進んでいた（_is_back で NFKC）。
#   ③v1.48 の取りこぼし。最大発注比率・モメンタム損切り・夜間ミュート時間帯の3つに validate が無く、
#     現在値が範囲外だと「Enter=現在値」と出ているのに Enter で進めないループが残っていた。
#   ④同じ金額の欄なのに、STEP 2 の BUDGET_USD だけ $10000 や全角を弾いていた（STEP 15 は通る）。
#     OVN 側の正規化（_normalize_amount）に揃えた。
# v1.48 2026-09-08  認定サポーター4名の v1.47 レビュー反映。
#   ①最重要: .env の読み取りを Bot（python-dotenv）と同じ規則に揃える（_read_env_value）。値のクォートと
#     「空白＋#」以降の行末コメントを落とし、export 接頭辞も外す。これを読まずにいたため、手編集の .env で
#     Bot と Wizard が同じ行を違う値として読み、9キーは Enter で先へ進めず、3キーは黙って別の値で保存されていた
#     （OVN_MODE→shadow / NEWS_STRATEGY_PROFILE→standard / TRIGGER_TICKERS の SMH 脱落）。
#   ②現在値が検証を通らないときは既定として出さない（ask に validate）。Enter の無限ループを断つ。
#   ③STEP7: 読めない TRIGGER_TICKERS のとき Enter が通っていた（v1.47 の穴）。番号選択を必須にし、
#     「未設定なので」→「読み取れなかったので」。個別株欄は全角・全角/半角セミコロン・読点・空白区切りも受ける。
#   ④STEP12: MARGIN を既定にし、CASH を断ったあとは MARGIN が現在値になる（同じ警告の繰り返しを断つ）。
#     OpenD がポートだけ開いて無応答のときに口座取得が戻らない件は、別スレッドで待って見切る。
#   ⑤確認画面: OVN の条件を日本語に（normal→標準）。桁揃えを表示幅で数える（全角ラベルの行のずれ）。
#   ⑥STEP6: 「OVN は別枠」の注記を、RTH 以外に値がある人の分岐にも出す。STEP14 の重複説明を1行に。
# v1.47 2026-09-08  認定サポーター2名の v1.46 レビュー反映。
#   ①STEP7: 既存の TRIGGER_TICKERS がプリセットと一致しない（例 QQQ,SMH・順序違い）とき、Enter で SPY,QQQ に
#     置き換わっていた → 現在値をそのまま（順序も）維持する選択肢を出し、Enter はそれを選ぶ。プリセットは番号で明示。
#   ②STEP1: 説明ブロックの並びをメニューと同じ [1]→[2] に。B の呼び名を統一。「1トレードのリスクが小さい」の断定をやめる。
#   ③既定の印を「← 既定」に統一（「← まずここから」「← デフォルト」「（既定）」を廃止）。毎画面の先頭に
#     「▶ = 現在の設定（Enter でそのまま）／← 既定 = 初めて設定するときの標準値」の凡例（レビュー Codex）。
#   ④STEP15: 設問番号を Q1〜Q6 に（選択肢の [1][2] と区別）。止め方に「次回起動から効く・建玉は即決済しない」、
#     予約は約定を保証しない、QQQ 保有日の見送りを別枠の説明の近くに。Q6 の見出しに既定（持ち越す）。
#   ⑤STEP1/6/15: 通常の時間帯設定と OVN は別枠であることを明記。移行前全決済の「5分前」は現在値（CLOSE_BEFORE_INACTIVE_MIN）。
#   ⑥STEP4/確認画面: トレール幅の説明を買い・空売り両方に（極値からの戻り）。時間切れの「〇〇分」を現在値に。
#   ⑦受講生向け画面の版数（v3.9.45 / v3.9.20）を消す。最終画面はデモの起動を先に。
# v1.46 2026-09-06  戦略プロファイルを STEP1 に・OVN取引機能・時間帯は「発注しない」が標準（Bot v3.9.193 連動・PAN 指示）。
#   ①STEP1「戦略プロファイル」を新設。モメンタム（MOMENTUM_STRATEGY_PROFILE）とニュース選抜 v1
#     （NEWS_STRATEGY_PROFILE: 新規エントリーを TECH/SEMI_STRONG かつ RTH に限る・決済は止めない）をまとめて選ぶ。
#     プロファイルが優先する項目は以降に出さない: 両方が選抜なら STEP6 の時間帯は RTH 以外を「発注しない」で自動
#     （既存で RTH 以外に値がある人には尋ねる）、STEP14 のモメンタム詳細は従来どおりスキップ。全 STEP を +1（16 STEP）。
#   ②STEP6 の標準は「発注しない」（【標準】表記・旧「標準」の水準は「通常」に改名）。
#   ③STEP15「OVN取引機能（夜間持ち越し・任意）」を新設（アラート音は STEP16 へ）。既定は「使う」。OVN_ENABLED / OVN_MODE /
#     OVN_BUDGET_USD / OVN_VIX_LEVEL / OVN_SKIP_LONG_HOLIDAY / OVN_SKIP_WEEKEND を対話で設定。実売買は Y/N で確認。
#     金額は必須（b で「使わない」に戻れる）。QQQ 1株に届かない金額では買わないことを明記。
#   ④書き出し（新規/差し替え）・確認画面・設定チェック（prompt/validate/normalize つき）に上記キーを追加。
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
#                   - 値の選択肢マーカーは「← 既定」に統一
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
import unicodedata  # v1.48: 個別株ティッカーの全角→半角の正規化
import atexit  # v1.48: 応答しない OpenD を見切ったあとに終了できなくなるのを防ぐ


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
    # v1.47（配布前レビュー Codex）: 「▶」は現在の設定、「← 既定」は初めて設定するときの標準値。
    #   既存の設定が別の選択肢だと ▶ と ← 既定 が別の行に付くので、意味の違いを毎画面の先頭で示す。
    print(f"  {dim('▶ = 現在の設定（Enter でそのまま）　← 既定 = 初めて設定するときの標準値')}")
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


def ask(prompt, default="", secret=False, allow_clear=False, validate=None):
    # ★ v1.48: 現在値が検証を通らないときは既定として出さない（Enter を押し続けても
    #   同じ問いに戻り続ける、という報告への対応。出口を「入力するだけ」にする）。
    if default and validate is not None:
        try:
            _ok = bool(validate(default))
        except Exception:
            _ok = False
        if not _ok:
            print(f"  {yellow('!')} {dim(f'現在の値「{default}」はこの項目では使えないため、Enter では進めません。入力してください。')}")
            default = ""
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

def _num_in_range(v, lo, hi, allow_comma=False, integer_only=False, exclude_lo=False):
    """★ v1.48: ask(validate=) 用。数値として読めて範囲内なら True。

    配布前レビュー（Codex）: ここの条件は、その問いの後段の検証と同じでなければならない。
    緩いと壊れた既定を残してしまい（Enter の繰り返し）、厳しいと通るはずの現在値を落とす。
    """
    t = str(v).strip()
    if allow_comma:
        t = t.replace(",", "")
    if integer_only and not t.isdigit():
        return False
    try:
        f = float(t)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(f):
        return False
    return (lo < f if exclude_lo else lo <= f) and f <= hi


def _int_trunc_in_range(v, lo, hi):
    """★ v1.49: ask(validate=) 用。小数を切り捨てた整数が範囲内なら True。

    後段の検査（int(float(val)) が lo〜hi）と同じ条件にしてある。緩いと壊れた
    現在値を既定として出してしまい、厳しいと通るはずの現在値を落とす。"""
    try:
        _i = int(float(str(v).strip()))
    except (TypeError, ValueError, OverflowError):
        return False
    return lo <= _i <= hi


def ask_yn(prompt, default=True):
    # ★ v1.21 (点5b): 日本語「はい/いいえ」も受け付ける。従来は「いいえ」が True(=はい)
    #   扱いになる不具合があった（N/NO 以外は全て True だったため）。
    # ★ v1.49: 全角の「Ｎ」「Ｙ」が既定値として素通りしていた（認定サポーターの報告）。
    #   日本語入力のまま Ｎ と打つと、聞き直しにならず既定の側で先へ進む。
    #   「実発注を有効にします」「OVN取引機能の実売買を有効にします」も同じ入口なので、
    #   止めたつもりで有効のまま保存されうる。NFKC で全角を直し、読めない入力は聞き直す。
    #   Enter（空入力）だけが既定値の意味。
    # ★ v1.49（配布前レビュー Claude 別人格）: default="" を渡すと ask の [現在: Y] が出なくなり、
    #   「実発注を有効にします」で Enter がどちらに倒れるかが画面から消える。ヒントに入れる。
    hint = f"(Y/N・Enter={'Y' if default else 'N'})"
    while True:
        raw = ask(f"{prompt} {dim(hint)}", default="")
        s = unicodedata.normalize("NFKC", str(raw or "")).strip().lower()
        if s == "":
            return default
        if s in ("n", "no", "いいえ", "no.", "いや", "しない"):
            return False
        if s in ("y", "yes", "はい", "する", "ok"):
            return True
        warn(f"Y か N で入力してください（Enter だけなら {'Y' if default else 'N'}）")

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
    # ★ v1.48（配布前レビュー Claude 別人格）: ask 側と作法を揃える。既定が選択肢にも範囲にも
    #   当てはまらないなら「Enter で維持できる」と見せない（見せると Enter が空回りする）。
    _default_ok = bool(default) and (matched or (
        custom_range is not None and _num_in_range(default, custom_range[0], custom_range[1])))
    if default and not _default_ok:
        print(f"  {yellow('!')} {dim(f'現在の値「{default}」はこの項目では使えないため、Enter では進めません。入力してください。')}")
        default = ""
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


def _is_back(raw):
    """★ v1.49: 「戻る」指示かどうか。全角の「ｂ」でも戻れるようにする（認定サポーターの報告）。"""
    return unicodedata.normalize("NFKC", str(raw or "")).strip().lower() in _BACK_TOKENS


def next_step_pause():
    """次のSTEPへ進む前にEnterを待つ。'b' 入力で前のステップへ戻る（v1.26）。"""
    if _WIZARD_CAN_GO_BACK:
        prompt = f"  {dim('次の STEP へ進む: Enter ／ ひとつ前に戻る: b を入力 + Enter : ')}"
    else:
        prompt = f"  {dim('次の STEP へ進む場合は Enter : ')}"
    try:
        ans = input(prompt)
    except (KeyboardInterrupt, EOFError):
        print("\n\n  " + yellow("キャンセルしました。"))
        sys.exit(0)
    if _WIZARD_CAN_GO_BACK and _is_back(ans):
        raise _GoBack()
    print()

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def _read_env_value(v):
    """★ v1.48: Bot が使う python-dotenv と同じ規則で値を読む（認定サポーターの掃引報告）。

    Bot は load_dotenv() で読むので、クォートで囲まれていれば外し、囲まれていなければ
    「空白＋#」以降を落とす。Wizard がここを揃えていなかったため、手で編集した .env で
    Bot と Wizard が同じ行を違う値として読み、Enter で進めない／黙って別の値が保存される、
    という食い違いが起きていた（OVN_MODE→shadow・NEWS_STRATEGY_PROFILE→standard など）。"""
    v = (v or "").strip()
    if v[:1] in ("\"", "'"):
        # 引用符で始まる値は、閉じ引用符までが値。その後ろ（コメント等）は無視する。
        _q = v[0]
        _end = v.find(_q, 1)
        if _end == -1:
            return None                       # 閉じない引用符 → dotenv はこの行を読み捨てる
        _rest = v[_end + 1:].strip()
        if _rest and not _rest.startswith("#"):
            return None                       # 閉じたあとに続きがある → dotenv はこの行を読み捨てる
        return v[1:_end]
    m = re.search(r"\s#", v)
    return v[:m.start()].rstrip() if m else v


def _load_existing_env():
    if not os.path.exists(ENV_PATH):
        return {}
    values = {}
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k = k.strip()
                if k.startswith("export "):          # export KEY=value も dotenv は KEY として読む
                    k = k[len("export "):].strip()
                _val = _read_env_value(v)
                if _val is None:
                    continue                         # dotenv が読み捨てる行は Wizard も未設定として扱う
                values[k] = _val
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

TOTAL = 16   # ★ v1.46: 14→16（戦略プロファイルを STEP1 に・OVN取引機能を STEP15 に新設・アラート音は16へ）

# 既知ETFリスト（STOCK_TICKERS入力時のバリデーション用）
# ★ v1.38: 版数は必ずここを更新する（起動バナー・ヘッダ表示で共用。取り残し防止）
WIZARD_VERSION = "v1.53"

_KNOWN_ETFS = {
    "SPY", "QQQ", "SMH", "SPXL", "SPXS", "TQQQ", "SQQQ", "SOXL", "SOXS",
    "IWM", "DIA", "GLD", "SLV", "TLT", "VTI", "VOO", "VEA", "VWO", "AGG",
    "LQD", "HYG", "XLF", "XLK", "XLE", "XLV", "XLI", "XLB", "XLRE",
    "EEM", "FXI", "EWJ", "GDX", "ARKK", "XBI", "IBB", "UVXY", "VXX",
    "SOXX", "MCHI", "KWEB", "SQQQ", "UPRO", "SPXU",
}

# 発注しない設定の sentinel 値（AI confidence は 0.0〜1.0 なので 2.0 は絶対に超えない）
_DISABLED_CONF = "2.00"

# ★ v1.50: モメンタムの戦略プロファイルの名前と判定を1か所にまとめる（v2 の追加で分岐が6か所に増えたため）。
_MOM_PROFILE_LABELS = {
    "standard":  "カスタマイズ設定（今まで通り）",
    "select_v1": "選抜プロファイル v1（絞り込み運転）",
    "select_v2": "選抜プロファイル v2（絞り込み運転・検証中）",
}
# v2 の既定サイドは Bot の既定（_DEFAULT_ENABLED_SIDES）から SMH の買いだけ外したもの。
# v2 は実行時に SMH の買いを外すので、入れておいても v2 では発注されないが、あとで [1] カスタマイズ設定に
# 切り替えたときにこの値が残ると SMH の買いが有効になる（v3.9.192 で標準セットから外した判断と食い違う）。
_V2_DEFAULT_SIDES = "SPY:SELL_SHORT,QQQ:SELL_SHORT,QQQ:BUY,SMH:SELL_SHORT"


def _mom_profile_label(profile):
    return _MOM_PROFILE_LABELS.get(str(profile or "").strip().lower(), _MOM_PROFILE_LABELS["standard"])


def _is_mom_select(profile):
    return str(profile or "").strip().lower() in ("select_v1", "select_v2")


_MOM_SIDE_WORDS = ("BUY", "SELL_SHORT")


def _mom_side_pairs(raw):
    """★ v1.53: Bot が受け付ける綴りだけを取り出す（Bot の判定は完全一致）。

    `SPY: BUY` や `SPY:SHORT` は Bot では実発注の対象にならないのに、Wizard の
    確認画面は実発注のサイドとして出していた（Bot v3.9.203 の配布前レビュー）。
    とくに `SPY: SELL_SHORT`（コロンの後に空白）は空売りの注記の判定にも当たらず、
    空売りを止めている口座で「実発注される」と読める表示になっていた。
    """
    out = []
    for p in (raw or "").split(","):
        p = p.strip().upper()
        if ":" in p and p.split(":", 1)[-1] in _MOM_SIDE_WORDS:
            out.append(p)
    return out


def _effective_select_v2_sides(raw):
    """★ v1.50: 選抜プロファイル v2 の絞り込み後に残る実発注サイド（Bot の _momentum_effective_live_sides と同じ式:
    SPY を外し、SMH の買いを外す）。"""
    pairs = _mom_side_pairs(raw)
    return ",".join(p for p in pairs if not p.startswith("SPY:") and p != "SMH:BUY")


def _short_gate_note(config, sides_str):
    """★ v1.50: 口座ごとの空売りの許可を実発注サイドの表示に反映する（Bot の _momentum_effective_live_sides と同じ関門）。
    配布前レビュー（Claude 別人格）: 表示に空売りが出ていても、許可が false の口座では Bot は空売りを発注しない。"""
    if ":SELL_SHORT" not in str(sides_str or "").upper():
        return ""
    off = []
    if not _bot_reads_true(config, "DEMO_SHORT_ENABLED"):
        off.append("デモ口座")
    if not _bot_reads_true(config, "REAL_SHORT_ENABLED"):
        off.append("実口座")
    # 口座を限って書く。「空売りは発注されません」だけだと、もう片方の口座でも出ないように読める。
    _acc = "・".join(off)
    return ("（" + _acc + "では空売りを無効にしているため、" + _acc + "では空売りは発注されません）") if off else ""


def step_profiles(existing):
    """★ v1.46: 戦略プロファイルを最初に決める。ここで「選抜」を選ぶと、プロファイルが優先する
    項目（STEP 6 の時間帯・STEP 14 のモメンタム詳細）は以降の STEP に出ない。"""
    header(1, TOTAL, "🎯 STEP 1 ── 戦略プロファイル（実発注の絞り込み・最初に決める設定）")
    print(f"  {bold('概要')}")
    print(f"  {dim('過去の全取引データの集計に基づく「絞り込み運転」を、モメンタムとニュースのそれぞれで選びます。')}")
    print(f"  {dim('選抜を選ぶと、プロファイルが優先する項目（時間帯・モメンタムの詳細設定）は以降の STEP に出ません。')}")
    print()
    # ── [0] モメンタムの戦略プロファイル ★ v1.35 / Bot v3.9.116（v1.46 で STEP 1 へ移動）──
    print(f"  {bold('A. モメンタムの戦略プロファイル（実発注の絞り込み）')}")
    print(f"  {dim('過去の全取引データの集計に基づく「絞り込み運転」を選べます。')}")
    # ★ v1.38: 既定は[2]選抜プロファイル。「Enter＝従来どおり」ではない点を正しく表記（Codexレビュー対応）
    print(f"  {dim('[1] カスタマイズ設定 を選ぶと、これまでと同じく STEP 14 で細かく決めます。')}")
    print(f"  {dim('Enter を押すと ▶ の付いている項目（現在の設定）がそのまま使われます。初回は [3] が既定です。')}")
    print()
    # ★ v1.37: 既定を「選抜プロファイル v1」に変更。過去集計で標準より相対的に成績が良好かつ、
    #   実発注が少なく1トレードのリスクも小さい（より保守的な）運転のため。未設定の新規は select_v1（v1.50 で新規の既定は v2 に変更）。
    #   （注）戦略全体はまだ黒字化していない。あくまで“標準よりマシ・低リスク”の位置づけで、利益は非保証。
    # ★ v1.50: 初めて設定する方の既定は v2（PAN 指示）。いまの値が standard / v1 / v2 ならそのまま保つ。
    #   配布前レビュー（Codex / Gemini）: キーが無い既存の .env は Bot の既定 standard で動いている。
    #   そこへ v2 を既定として出すと Enter だけで黙って v2 に切り替わるので、ニュース選抜と同じく分ける。
    _raw_profile = str(existing.get("MOMENTUM_STRATEGY_PROFILE", "")).strip().lower()
    if _raw_profile in ("standard", "select_v1", "select_v2"):
        _cur_profile = _raw_profile
    else:
        _cur_profile = "select_v2" if not existing else "standard"
    _cur_prof_mode = {"standard": "1", "select_v1": "2", "select_v2": "3"}[_cur_profile]
    print(f"  {green('▶') if _cur_prof_mode == '1' else ' '} [1] カスタマイズ設定（今まで通り）")
    print( "        プロファイルによる絞り込みなし。STEP 14 の [1]〜[6] で自分で決めた設定がそのまま使われます。")
    print( "        （方向・銘柄・時間帯・金額の絞り込みを自分で決めます）")
    print(f"  {green('▶') if _cur_prof_mode == '2' else ' '} [2] 選抜プロファイル v1（絞り込み運転）")
    print( "        約5週間の全取引データ（実発注 4,266件＋シャドー観察のユニークシグナル 4,952件）")
    print( "        を集計し、カスタマイズ設定（絞り込みなし）より相対的に成績が良好だった条件だけに実発注を絞ります。")
    print( "        （＝実発注の候補を条件で絞る運転。1回の損失の大きさは発注額・値動き・損切りで決まり、成績は保証しません）")
    print( "        絞り込みの内容（5つ）:")
    print( "          ① 方向    … 空売り（ショート）のみ実発注。買い（ロング）は記録のみ")
    print( "          ② 銘柄    … SPY を実発注から除外（対象は QQQ / SMH）")
    print( "          ③ 時間帯  … 米国東部時間 9・10・12・13時台のみ新規発注")
    print( "                       （11時台と14時以降は過去集計で損失が続いた時間帯のため見送り）")
    print( "          ④ 損切り  … 固定の損切りライン（建玉トレールは使わない）")
    print( "                       利益が伸びたときのトレール利確は今まで通り働きます")
    print( "          ⑤ 安全網  … 1日の損失が上限（リスク許容度・既定なら予算の 0.5%）に達したら、その日の新規発注を自動停止")
    print( "                       （プロファイルは予算の 1.5% の上限も重ねてかけます。先に当たった方で止まります）")
    print(f"  {green('▶') if _cur_prof_mode == '3' else ' '} [3] 選抜プロファイル v2（絞り込み運転・検証中）← 既定")
    print( "        8〜9月の観察ログと実取引を集計し直して、v1 の絞り込みを組み直したものです。")
    print( "        （まだ検証中の仮説です。成績は保証しません）")
    print( "        v1 との違い（5つ）:")
    print( "          ① 方向    … 買い（ロング）も実発注の対象にします")
    print( "          ② 時間帯  … 売りは米国東部時間 9・12時台、買いは 9〜11時台に新規発注")
    print( "          ③ 強さ    … 5分・15分の変化率が Level 2 の基準に届かないときは実発注しない")
    print( "                       （変化率の値が取れない銘柄は、その回は判定せずに見送ります。")
    print( "                        発火頻度 MOMENTUM_LEVEL を Level 2 より厳しくしているときは、そちらが効きます）")
    print( "          ④ 相場    … 直近60分で QQQ が +0.15% より上げているときは売りを見送り")
    print( "                       （QQQ の値が取れないときは、見送りません）")
    print( "          ⑤ 銘柄    … SPY と SMH の買いは実発注から除外（対象は QQQ の売買と SMH の売り）")
    print( "        固定の損切りラインと1日の損失上限は v1 と同じです。損失上限は、リスク許容度の上限（既定なら予算の 0.5%）と")
    print( "        プロファイルの上限（.env で別の値を指定していなければ予算の 1.5%）を重ねてかけ、先に当たった方で止まります。")
    print()
    print(f"  {dim('・見送ったシグナルもすべてシャドー記録に残るため、絞り込みの効果は毎週の集計で確認できます。')}")
    print(f"  {dim('・過去データの傾向に基づく設定であり、将来の成績を保証するものではありません。')}")
    print(f"  {dim('・[2]・[3]を選んだ場合、STEP 14 の [2-c]銘柄サイド・[2-d]ロングレンジ・[6]損切り方式よりも、')}")
    print(f"  {dim('  プロファイルの絞り込みが優先されます（実発注のみ。シャドー記録は全件そのまま）。')}")
    print(f"  {dim('・いつでも Wizard を再実行して [1] カスタマイズ設定に戻せます。')}")
    print()
    profile_choices = [
        ("1", "カスタマイズ設定（今まで通り）"),
        ("2", "選抜プロファイル v1（絞り込み運転）"),
        ("3", "選抜プロファイル v2（絞り込み運転・検証中）← 既定"),
    ]
    _prof_sel = ask_choice("番号を選択（Enter=現在値を維持）", profile_choices, default=_cur_prof_mode)
    strategy_profile = {"1": "standard", "2": "select_v1", "3": "select_v2"}.get(_prof_sel, "select_v2")
    ok("戦略プロファイル: " + _mom_profile_label(strategy_profile))
    print()

    # ── [0-b] ニュース選抜プロファイル v1 ★ v1.46 / Bot v3.9.169 ──
    news_profile = _ask_news_profile(existing)
    print()
    ok_box([
        ("MOMENTUM_STRATEGY_PROFILE", _mom_profile_label(strategy_profile)),
        ("NEWS_STRATEGY_PROFILE",     "ニュース選抜 v1（TECH / SEMI_STRONG・RTH のみ新規建て）" if news_profile == "select_v1" else "カスタマイズ設定（今まで通り）"),
    ])
    next_step_pause()
    return {"MOMENTUM_STRATEGY_PROFILE": strategy_profile, "NEWS_STRATEGY_PROFILE": news_profile}


def step1_budget(existing):
    header(2, TOTAL, "💰 STEP 2 ── 予算（BUDGET_USD）")
    print("  最大投資上限額（ドル）を設定します。\n")
    box("目安", [
        "$10,000 未満だと、1回の発注額が小さくなり手数料負けのリスクが大きくなります。",
        "（金額はご自身の資金計画に合わせて設定してください）",
        "実口座（02_Real で起動）で使う場合は、口座の実際の信用余力の範囲内に設定してください。",
        "余力を超えると、複数銘柄の同時保有時に発注が拒否されます（信用余力不足）。",
    ])
    cur = existing.get("BUDGET_USD") or "10000"          # ★ v1.48: KEY= の空値でも既定に落とす
    while True:
        # ★ v1.49: 同じ金額の欄なのに、STEP 15（OVN）は $800 が通るのにここは $10000 を弾いていた
        #   （認定サポーターの報告）。$ と全角とカンマの扱いを OVN 側（_normalize_amount）に揃える。
        val = ask("BUDGET_USD（ドル・$ やカンマ・全角も可）", default=cur,
                  validate=_ovn_budget_ok)
        try:
            v = float(_normalize_amount(val))
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
    header(3, TOTAL, "🛡 STEP 3 ── リスク管理")
    budget_val = float(budget)

    print("  【損切りライン（MAX_LOSS_PCT）】\n")
    print("  ポジション評価額が元値からこの%下落したら自動で損切りします。\n")
    box("目安", [
        "0.30%  標準型（タイト・小さな損失で素早く撤退）← 既定",
        "0.50%  ゆとりあり（以前の標準）",
        "1.00%  ゆるめ（切られにくいが、1回の損失は大きくなる）",
    ])
    cur_loss = existing.get("MAX_LOSS_PCT") or "0.30"
    while True:
        val = ask("MAX_LOSS_PCT（%）", default=cur_loss, validate=lambda _v: _num_in_range(_v, 0, 10, exclude_lo=True))
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
    _cur_to = str(existing.get("TIMEOUT_EXIT_MINUTES", "") or "10").strip()
    if _cur_to == "0":
        print("  発注から一定の分数が経過しても保有中の場合に自動で決済します（現在の設定は「無効」＝時間切れ決済しない）。\n")
    else:
        print(f"  発注から {_cur_to} 分（現在の設定）が経過しても保有中の場合に自動で決済します。\n")
    # ★ v1.39: 全期間集計（ニュース系 4,608件）の参考値を表示
    box("参考: 全期間集計での設定値ごとの成績（過去実績・成果は非保証）", [
        "10分設定: 2,473件  勝率51%  合計 +$5,261 ← 最良",
        "30分設定:   667件  勝率49%  合計 −$10,657（明確に劣後）",
        "60分設定:   342件  勝率52%  合計 +$1,551",
        "15分設定:   110件  ほぼ±0",
        "時間切れ決済玉の平均: 最大含み益+0.096% → 決済+0.019%",
        "（＝10分の時点でニュースの鮮度はほぼ消えており、長く持つ利点は確認できず）",
    ])
    choices = [
        ("5",  " 5分（短期・ニュース直後のみ）"),
        ("10", "10分（標準型・全期間集計で最良）← 既定"),
        ("30", "30分（ゆとりあり・過去集計では劣後）"),
        ("60", "60分（長め）"),
        ("0",  " 無効（時間切れ決済しない）"),
    ]
    print(f"  {dim('※ 番号のほか、数字を直接入力すれば任意の分数も設定できます（例: 15 / 範囲 0〜240・0=無効）。')}")
    cur_timeout = existing.get("TIMEOUT_EXIT_MINUTES") or "10"
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
    header(4, TOTAL, "📈 STEP 4 ── トレイリングストップ")
    print("  利益が出たポジションを守るための自動追跡決済です。\n")
    if _is_mom_select(existing.get("MOMENTUM_STRATEGY_PROFILE", "select_v2")):
        # ★ v1.46: 選抜プロファイルのモメンタム建玉は固定の損切りで、この設定は使われない（ニュース連動の建玉には使われる）
        print(f"  {dim('※ STEP 1 の選抜プロファイルが置き換えるのは損切り側（建玉トレール→固定の損切りライン）だけです。')}")
        print(f"  {dim('   ここで決める利確トレールは、ニュース連動・モメンタムの両方の建玉に効きます。')}\n")
    print("  ① 発動しきい値: 建値から有利な方向にこの%動いたらトレール開始")
    print("  ② トレール幅:   有利な方向の極値（買いは最高値・空売りは最安値）からこの%戻ったら決済\n")
    box("例（BUDGET $10,000 の場合）", [
        "発動+0.22% → $10,022 に到達したらトレール開始",
        "トレール幅0.15% → 買いなら最高値から$15下落、空売りなら最安値から$15上昇で決済",
    ])

    # ★ v3.9.73: 入力は「1=1%（パーセント数値）」に統一。旧 .env(小数 0.003 等)は
    # 読み込み時に ×100 して自動変換し、新表記を既定として提示する(半自動移行)。
    print(f"  {dim('※ 数値は『1 = 1%』表記です（例: 0.22 = 0.22%）。')}\n")
    # ★ v1.38: 標準を 0.30 → 0.22 に変更。全期間バックアップ集計（10,053件）の
    #   最大含み益ベース反実仮想で、0.22 は 全体+$4,152 / 建玉トレール+$2,546 /
    #   モメンタム+$3,958 の改善（0.30比・近似・成果非保証）。0.18 はさらに数字上
    #   良いが、確保利益が 0.03〜0.15% と手数料負け帯に入るため 0.22 を採用。
    trig_choices = [
        ("0.22", "0.22%（新標準・全期間実測で改善）← 既定"),
        ("0.30", "0.30%（旧標準 v1.10〜v1.37）"),
        ("0.50", "0.50%（やや遅め）"),
        ("1.0",  "1.0%（以前の標準）"),
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
        ("0.15", "0.15%（標準・利益取りこぼし最小）← 既定"),
        ("0.30", "0.30%（やや余裕あり）"),
        ("0.50", "0.50%（以前の標準）"),
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
    ok(f"トレール幅: 極値から {float(drop):.2f}% 戻りで決済（買いは最高値・空売りは最安値）")

    ok_box([
        ("TRAIL_TRIGGER_PCT", f"+{float(trig):.2f}%  でトレール開始"),
        ("TRAIL_DROP_PCT",    f"極値から {float(drop):.2f}% 戻りで決済（買いは最高値・空売りは最安値）"),
    ])
    next_step_pause()
    return {"TRAIL_TRIGGER_PCT": trig, "TRAIL_DROP_PCT": drop}

def step4_confidence(existing):
    header(5, TOTAL, "🤖 STEP 5 ── AIしきい値（ベース）")
    print("  AIが0.0〜1.0のスコアでニュースを評価します。\n")

    print("  【発注しきい値（STRONG_BUY_CONFIDENCE）】\n")
    box("目安", [
        "0.85  発注かなり少なめ：厳選した場面だけ",
        "0.75  発注少なめ：慎重に絞る",
        "0.70  標準：バランス重視  ← 既定",
        "0.65  発注多め：反応は増えるが外れも増える",
    ])
    cur_conf = existing.get("STRONG_BUY_CONFIDENCE") or "0.70"
    while True:
        val = ask("STRONG_BUY_CONFIDENCE（0.5〜1.0）", default=cur_conf, validate=lambda _v: _num_in_range(_v, 0.5, 1.0))
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
    cur_panic = existing.get("PANIC_CONFIDENCE") or base_conf
    while True:
        val = ask("PANIC_CONFIDENCE（Enter=現在値を維持・未設定なら発注しきい値と同じ）", default=cur_panic,
                  validate=lambda _v: _num_in_range(_v, 0.5, 1.0))
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

def _close_before_min(existing):
    """CLOSE_BEFORE_INACTIVE_MIN の表示用。Bot は 1〜60 の整数以外を 5 として動く（配布前レビュー Claude 別人格）。"""
    raw = str(existing.get("CLOSE_BEFORE_INACTIVE_MIN", "") or "").strip()
    if not raw:
        return "5", ""
    try:
        v = int(float(raw))
    except ValueError:
        v = None
    if v is None or not (1 <= v <= 60):
        return "5", f"（.env の値 {raw} は範囲外のため Bot は 5 分として動きます）"
    return str(v), ""


def step5_session(existing, base_conf):
    header(6, TOTAL, "⏰ STEP 6 ── 時間帯別トレード設定")
    base = float(base_conf)
    # ★ v1.46: モメンタムとニュースの両方が選抜プロファイルなら、新規建ては RTH だけ（プロファイルが
    #   優先）なので、RTH 以外の時間帯は「発注しない」を自動で書き、この STEP は尋ねない（PAN 指示）。
    _mom_sel  = _is_mom_select(existing.get("MOMENTUM_STRATEGY_PROFILE", "select_v2"))   # ★ v1.50: v2 も同じ扱い
    _news_sel = str(existing.get("NEWS_STRATEGY_PROFILE", "")).strip().lower() == "select_v1"
    _prev_saved = existing.get("_SESSION_PREV") or {}
    def _sess_val(k):
        _v = str(existing.get(k, "") or "")
        if isinstance(_prev_saved, dict) and _v == _DISABLED_CONF and k in _prev_saved:
            _v = str(_prev_saved.get(k, "") or "")
        return _v
    _has_live_session = any(
        _sess_val(k) not in ("", _DISABLED_CONF)
        for k in ("CONFIDENCE_PREMARKET", "CONFIDENCE_AFTERHOURS", "CONFIDENCE_OVERNIGHT"))
    if _mom_sel and _news_sel and _has_live_session:
        # 配布前レビュー（Claude 別人格）: モメンタムの選抜は ET 9時台を含むので 9:00〜9:29 のプリマーケットに
        #   発注しうる。既存で RTH 以外に値がある人の設定を黙って「発注しない」に変えない（尋ねる）。
        print(f"  {yellow('選抜プロファイルを選んでいますが、RTH 以外の時間帯に設定値があるため、そのまま維持するか確認します。')}")
        print(f"  {dim('（標準は「発注しない」です。Enter で現在値を維持できます）')}")
        print(f"  {dim('STEP 15 の OVN取引機能は別枠で、この設定では止まりません。')}")
        print()
    if _news_sel and not _mom_sel:
        print(f"  {dim('※ ニュース選抜プロファイルでは、ニュース連動の新規建ては通常取引時間（RTH）だけです。')}")
        print(f"  {dim('   ここの設定は、それ以外の時間帯にモメンタムを動かすか（発注しない＝その時間帯は止まる）に効きます。')}\n")
    if _mom_sel and _news_sel and not _has_live_session:
        print(f"  {green('選抜プロファイル（モメンタム・ニュースとも）を選択 → 時間帯の設定はプロファイルが優先します。')}")
        print(f"  {dim('新規建ては通常取引時間（RTH）だけなので、プリマーケット／アフターアワーズ／オーバーナイトは')}")
        print(f"  {dim('「発注しない」（標準）を自動で書き出します。その時間帯はニュース取得・AI判定も止まります。')}")
        print(f"  {dim('STEP 15 の OVN取引機能は別枠で、この設定では止まりません。')}")
        print()
        # 配布前レビュー（Gemini）: 自動で「発注しない」を書いたあと「戻る」で標準に変えたとき、
        #   元の時間帯設定が既定に出るよう、上書き前の値を state に退避する（.env には書かれない）。
        _prev = _prev_saved or {
            k: existing.get(k, "") for k in ("CONFIDENCE_PREMARKET", "CONFIDENCE_AFTERHOURS", "CONFIDENCE_OVERNIGHT")
        }
        _r = {
            "CONFIDENCE_PREMARKET":  _DISABLED_CONF,
            "CONFIDENCE_AFTERHOURS": _DISABLED_CONF,
            "CONFIDENCE_OVERNIGHT":  _DISABLED_CONF,
            "CLOSE_BEFORE_INACTIVE": ("false" if str(existing.get("CLOSE_BEFORE_INACTIVE", "true")).strip().lower() == "false" else "true"),
            "CONFIDENCE_RTH":        existing.get("CONFIDENCE_RTH", ""),
            "_SESSION_PREV":         _prev,
        }
        if _r["CLOSE_BEFORE_INACTIVE"] != "true":
            warn("移行前全決済が OFF です。RTH 以外が「発注しない」だと、16:00 以降の建玉は翌朝まで Bot が監視しません。")
        ok_box([
            ("プリマーケット",   "発注しない（標準・自動）"),
            ("アフターアワーズ", "発注しない（標準・自動）"),
            ("オーバーナイト",   "発注しない（標準・自動）"),
            ("移行前全決済",     "ON" if _r["CLOSE_BEFORE_INACTIVE"] == "true" else "OFF（16:00 以降の建玉は翌朝まで無監視）"),
        ])
        next_step_pause()
        return _r
    print(f"  RTH ベースしきい値（STEP 5）: {base_conf}\n")
    print("  各セッションの発注方針を選択します。標準は「発注しない」です（RTH 以外は流動性が薄く不利なため）。")
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
        # 自動スキップで上書きした値なら、退避してあった元の値を既定に戻す
        _prev_vals = existing.get("_SESSION_PREV") or {}
        if isinstance(_prev_vals, dict) and cur_val == _DISABLED_CONF and key in _prev_vals:
            cur_val = _prev_vals.get(key, "") or ""
        cur_mode = _detect_mode(cur_val, vals) if cur_val else defmode

        print(f"  {cyan('─'*54)}")
        print(f"  {bold(label)}")
        print(f"  {dim(note)}\n")

        choices_display = [
            ("disabled",     f"発注しない【標準】  （このセッションは完全停止）"),
            ("conservative", f"慎重  {vals['conservative']}   重要ニュースのみ"),
            ("standard",     f"通常  {vals['standard']}   スプレッドを考慮した水準"),
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
                "standard":     "通常",
                "aggressive":   "積極",
            }
            ok(f"{short_name}: {label_map[chosen_mode]}（{result[key]}）")
        print()

    # ── 移行前全決済 ────────────────────────────────────────────────────
    if disabled_sessions:
        print(f"  {red('⚡')} {bold('移行前全決済')}")
        _cbm, _cbm_note = _close_before_min(existing)
        print(f"  {dim(f'発注しない設定のセッションに切り替わる {_cbm} 分前（現在の設定）に全ポジション決済します。{_cbm_note}')}")
        print(f"  {dim('（Bot の既定は5分前。変えたい場合は .env に CLOSE_BEFORE_INACTIVE_MIN=15 のように 1〜60 で指定）')}\n")
        cur_close = existing.get("CLOSE_BEFORE_INACTIVE", "true").lower()
        close_yn = ask_yn("移行前全決済を有効にしますか？", default=(cur_close != "false"))
        result["CLOSE_BEFORE_INACTIVE"] = "true" if close_yn else "false"
        if close_yn:
            ok(f"移行前全決済: ON（セッション切り替え {_cbm} 分前に全決済）")
        else:
            info("移行前全決済: OFF（ポジションを保持したまま移行）")
    else:
        result["CLOSE_BEFORE_INACTIVE"] = existing.get("CLOSE_BEFORE_INACTIVE", "false")

    # RTHはベースと同じ（変更しない）
    result["CONFIDENCE_RTH"] = existing.get("CONFIDENCE_RTH", "")
    result["_SESSION_PREV"] = {}   # 尋ねた回の値が正。退避は捨てる（.env には書かれない）

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

def _effective_select_sides(raw):
    """★ v1.46: 選抜プロファイルが絞り込んだ後に残る実発注サイド（Bot の _momentum_effective_live_sides と同じ式:
    空売りだけ・SPY は外す）。"""
    pairs = _mom_side_pairs(raw)
    return ",".join(p for p in pairs if p.endswith(":SELL_SHORT") and not p.startswith("SPY:"))


def _bot_reads_true(config, key, default="true"):
    """Bot と同じ読み方で真偽を返す。Bot は 'true' のときだけ有効とし、0 / no / off / 空欄は無効になる。
    Wizard が「'false' のときだけ無効」と読むと、Bot がシャドー運転している .env を Enter だけで実発注に変えてしまう。"""
    return str(config.get(key, default)).strip().lower() == "true"


def _fmt_momentum_live(config):
    """★ v1.46: 確認画面の「MOMENTUM実発注」。実発注しない／選抜の絞り込み後／カスタマイズの生値。"""
    if not _bot_reads_true(config, "MOMENTUM_LIVE_TRADING"):
        return "実発注しない（シャドー観察のみ・記録だけ）"
    raw = config.get("MOMENTUM_ENABLED_SIDES", "")
    _prof = str(config.get("MOMENTUM_STRATEGY_PROFILE", "select_v2")).strip().lower()
    if _prof == "select_v1":
        eff = _effective_select_sides(raw)
        if not eff:
            return "（選抜の絞り込み後、実発注の対象なし。STEP 14 の設定に QQQ / SMH の空売りがありません）"
        return _fmt_momentum_sides(eff) + "（選抜プロファイルが空売りだけに絞り込み・買いと SPY は記録のみ）" + _short_gate_note(config, eff)
    if _prof == "select_v2":
        eff = _effective_select_v2_sides(raw)
        if not eff:
            return "（選抜 v2 の絞り込み後、実発注の対象なし。QQQ の売買・SMH の売りがどれも設定にありません）"
        return _fmt_momentum_sides(eff) + "（選抜プロファイル v2 が絞り込み・SPY と SMH の買いは記録のみ）" + _short_gate_note(config, eff)
    # ★ v1.53: 空売りの注記も、Bot が受け付ける綴りだけを見る（`SPY: SELL_SHORT` は
    #   Bot では空売りとして扱われないので、注記の対象にもしない）。
    _raw_eff = ",".join(_mom_side_pairs(raw))
    return _fmt_momentum_sides(_raw_eff) + _short_gate_note(config, _raw_eff)


def _fmt_account(config):
    """★ v1.46: 確認画面に「実口座かデモか」を出す。"""
    acc = str(config.get("MOOMOO_ACC_ID", "") or "").strip()
    if not acc:
        return "デモのみ（実口座は未設定）"
    return f"実口座 ***{acc[-4:]} を設定済み"


def _fmt_momentum_sides(raw):
    """MOMENTUM_ENABLED_SIDES を『SPY-売 / QQQ-売買 / IWM-売』形式に整形して返す。"""
    pairs = _mom_side_pairs(raw)   # ★ v1.53: Bot が受け付けない綴りは出さない
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
    header(7, TOTAL, "📊 STEP 7 ── 売買銘柄の選択（ニュース駆動）")
    print("  ここで選ぶのは【ニュース駆動（AIニュース）】の対象ETFです。買い・空売りの両方に対応します。")
    if _is_mom_select(existing.get("MOMENTUM_STRATEGY_PROFILE", "select_v2")):
        # 選抜では STEP 14 の [2-c] を尋ねない。無い入力欄へ案内しない（認定サポーターの報告）。
        print(f"  {dim('※ モメンタム戦略の実発注は、STEP 1 で選んだ選抜プロファイルが絞り込みます（ここで選ぶ銘柄とは別系統）。')}")
        print(f"  {dim('  銘柄・方向を細かく変えたいときは、STEP 1 でカスタマイズ設定を選んでください。')}")
    else:
        print(f"  {dim('※ モメンタム戦略の実発注銘柄は STEP 14「モメンタム発注設定」の[2-c]で別に選びます（別系統）。')}")
    print(f"  {dim('  現在のモメンタム実発注: ' + (_fmt_momentum_live(existing) if existing.get('MOMENTUM_ENABLED_SIDES') else '（STEP 14 で決めます）'))}\n")

    _news_sel = str(existing.get("NEWS_STRATEGY_PROFILE", "standard")).strip().lower() == "select_v1"
    if _news_sel:
        # 選抜を決めた後も銘柄を選ぶ理由を書く（認定サポーターの報告）。ニュース選抜が絞るのはカテゴリと時間帯で、
        # 銘柄構成はここで決める。STEP 7 はニュース選抜の値を書き換えない。
        print(f"  {green('ニュース選抜 v1 が有効です。')}{dim('新規の取引は、TECH / SEMI_STRONG のニュースと通常取引時間に絞られます（STEP 1 と同じ）。')}")
        print(f"  {dim('  ここでは、そのニュース取引に使う ETF の構成を選びます。選び直しても、ニュース選抜は解除されません。')}\n")

    # ── プリセット選択 ────────────────────────────────────────────────────
    presets = [
        ("SPY",         "SPY のみ",          "値動きが比較的安定。リスクを抑えたい場合に。"),
        ("SPY,QQQ",     "SPY ＋ QQQ",        "S&P500とNASDAQをカバー。標準的な設定。"),
        ("SPY,QQQ,SMH", "SPY ＋ QQQ ＋ SMH", "半導体も加える。損益の振れ幅が大きくなります。"),
    ]

    cur_tickers = ",".join(t.strip().upper() for t in str(existing.get("TRIGGER_TICKERS", "") or "").split(",") if t.strip())
    # ★ v1.47（認定サポーターの再現報告）: 現在値がプリセットと一致しない（QQQ,SMH や順序違い）とき、
    #   Enter で SPY,QQQ に置き換わっていた。先頭が MACRO・2番目が TECH の対応先なので順序も意味を持つ。
    #   現在値そのもの（順序も）を維持する選択肢を出し、Enter はそれを選ぶ。プリセットは番号で明示する。
    cur_preset = None
    for key, _, __ in presets:
        if cur_tickers == key:          # 順序も含めて一致したときだけプリセット扱い
            cur_preset = key
            break
    _is_custom = bool(cur_tickers) and cur_preset is None
    # 壊れた現在値（カンマ区切りでない・ティッカーの形でない）は維持の対象にせず、番号選択に倒す（レビュー Claude 別人格）
    _unreadable = False
    if _is_custom and not all(re.fullmatch(r"[A-Z][A-Z0-9.]{0,5}", t) for t in cur_tickers.split(",")):
        warn(f"現在の TRIGGER_TICKERS「{existing.get('TRIGGER_TICKERS', '')}」はカンマ区切りのティッカーとして読めないため、番号で選び直してください。")
        _is_custom = False
        _unreadable = True          # ★ v1.48: 値はある。Enter で既定に流さず番号を必須にする
        cur_tickers = ""

    for i, (key, label, detail) in enumerate(presets, 1):
        marker = green("▶") if key == cur_preset else " "
        if key == "SPY,QQQ,SMH":
            print(f"  {marker} [{i}] {yellow(label)}  {dim(detail)}")
        else:
            print(f"  {marker} [{i}] {bold(label)}  {dim(detail)}")
    if _is_custom:
        print(f"  {green('▶')} [Enter] 現在の設定 {bold(cur_tickers)} をそのまま維持（順序も変えません）")
    elif _unreadable:
        print(f"  {yellow('!')} {dim('現在の設定は読み取れなかったので、[1]〜[3] の番号を入力してください（Enter では進めません）。')}")
    elif not cur_tickers:
        print(f"  {green('▶')} [Enter] 未設定なので [2] SPY ＋ QQQ を使います")
    print()
    print(f"  {dim('※ 先頭の銘柄がマクロ系ニュースの発注先、2番目がテック系ニュースの発注先になります。')}")
    if _unreadable:
        info("（番号を入力してください）")
    else:
        info("（Enter = 現在値を維持）" if cur_tickers else "（Enter = [2] SPY ＋ QQQ）")

    if _is_custom or _unreadable:
        default_idx = ""
    else:
        default_idx = next((str(i) for i, (k, _l, _d) in enumerate(presets, 1) if k == cur_preset), "2")
    while True:
        raw = ask("番号を選択", default=default_idx)
        if _is_custom and not raw:
            chosen_key = cur_tickers
            break
        if raw in ("1", "2", "3"):
            chosen_key = presets[int(raw) - 1][0]
            break
        warn("1〜3 の番号を入力してください" + ("（Enter で現在の設定を維持）" if _is_custom else ""))

    tickers_list = [t.strip() for t in chosen_key.split(",")]
    tickers_str  = ",".join(tickers_list)
    ok(f"メイン銘柄: {tickers_str}（各ロング ／ ショート）")
    print()

    # ── 個別株追加 ────────────────────────────────────────────────────────
    print(f"  {bold('【個別株の追加】')}  {dim('任意・ETF不可・個別株のみ')}")
    print(f"  {dim('Finnhubのその銘柄固有ニュースを30秒間隔で取得してAI判定・直接売買します。')}")
    print(f"  {dim('例: NVDA → NVIDIAの決算・自社ニュースが出たときだけ発注')}\n")
    print(f"  {red('⚠  ETFティッカーは設定できません（例: SPXL, SOXL など）')}\n")
    if _news_sel:
        print(f"  {yellow('※ 個別株のニュース（決算・自社ニュース）による発注は、ニュース選抜 v1 の絞り込みの対象外です。')}\n")

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

        # ★ v1.48: 全角の「ＮＶＤＡ」やセミコロン・読点・空白区切りも受ける（認定サポーターの報告）。
        #   Bot は STOCK_TICKERS をカンマで分けて大文字にするだけなので、ここで同じ形に直しておく。
        input_list  = [t.strip().upper() for t in _split_tickers(stock_raw) if t.strip()]
        # ★ v1.48（配布前レビュー Claude 別人格）: 区切りを広げたぶん、ティッカーでない語が
        #   複数銘柄に化けやすい。形が合わないものは落として画面に出す。
        _bad = [t for t in input_list if not re.fullmatch(r"[A-Z][A-Z0-9.]{0,5}", t)]
        if _bad:
            warn("ティッカーとして読めない語は外します: " + ", ".join(_bad))
            input_list = [t for t in input_list if t not in _bad]
            if not input_list:
                warn("有効なティッカーがありません。半角英字で入力してください（例: NVDA,TSLA）")
                continue
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
    header(8, TOTAL, "⚙️  STEP 8 ── 発注詳細設定")
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
        ("auto", "ETF 0.30% / 個別株 0.50%（銘柄タイプで使い分け・新標準）← 既定"),
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
        ("1", " 1分（ニュース系・素早く撤退）← 既定"),
        ("2", " 2分（少し待つ）"),
        ("5", " 5分（ゆっくり約定を待つ）"),
    ]
    cancel = ask_choice("番号を選択（Enter=現在値を維持）", cancel_choices,
                        default=existing.get("ORDER_CANCEL_MINUTES") or "1")
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
    print(f"  {dim('AI の確信度に応じた「山型配分」が自動適用されます:')}")
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
    header(9, TOTAL, "🔑 STEP 9 ── Anthropic APIキー（必須）")
    print("  Claude AIでニュースを判断するために必須です。\n")
    info("console.anthropic.com → API Keys → Create Key")
    info("あらかじめクレジット（前払い）を購入しておいてください。残高がゼロだと AI 判定が全件失敗します。")
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
    header(10, TOTAL, "📡 STEP 10 ── Alpaca News API（任意）")
    print("  設定すると Benzinga のリアルタイムニュースが追加されます。")
    print("  設定しない場合は RSS のみで動作します。\n")
    box("取得方法", [
        "1. https://alpaca.markets でアカウント作成（無料）",
        "2. 無料の Paper Trading（模擬取引）口座で十分です（Live は不要）",
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
    header(11, TOTAL, "📰 STEP 11 ── Finnhub API（ニュース）＋ Discord 通知（任意）")
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
    # ★ v1.48: ポートは開くが応答しない OpenD（起動済みだが未ログイン・固まっている）では
    #   SDK が接続確立まで待ち続け、画面が無言のまま止まる（認定サポーターの計測で150秒でも戻らず）。
    #   別スレッドに置いて見切り、戻らなければ「取得できませんでした」の画面に倒す。
    import threading as _threading
    global _ACC_PROBE_ABANDONED, _ACC_PROBE_THREAD
    if _acc_probe_stuck():
        # 配布前レビュー（Gemini・Claude 別人格）: 見切ったスレッドは SDK の接続処理を握ったまま残る。
        #   増やさないよう、前回のスレッドが動いている間は即座に失敗にする（終わっていれば再挑戦できる）。
        return []
    _box = {}
    _th = _threading.Thread(target=lambda: _box.setdefault("v", _detect_real_acc_ids_blocking(host, port)),
                            daemon=True)
    _ACC_PROBE_THREAD = _th
    _th.start()
    _th.join(_DETECT_ACC_TIMEOUT_SEC)
    if _th.is_alive():
        _ACC_PROBE_ABANDONED = True
        # 配布前レビュー（Codex）: 取得本体は logging をプロセス全体で止めてから SDK に入る。
        #   見切るとその finally に到達しないので、ここで戻しておく（以降のログが消えたままになる）。
        import logging as _logging
        _logging.disable(_logging.NOTSET)
        # 配布前レビュー（Claude 別人格）: 全面抑制を戻すと、残ったスレッドの SDK ログが
        #   このあとの画面（マスク入力・確認画面）に割り込む。SDK のロガーだけ黙らせる。
        for _name in ("moomoo", "futu"):
            _lg = _logging.getLogger(_name)
            _lg.setLevel(_logging.CRITICAL); _lg.propagate = False; _lg.disabled = True
        return []
    return _box.get("v", [])


_DETECT_ACC_TIMEOUT_SEC = 20.0
_ACC_PROBE_ABANDONED = False
_ACC_PROBE_THREAD = None
_WIZARD_FINISHED_OK = False


def _acc_probe_stuck():
    """★ v1.48: 見切った口座取得スレッドがまだ SDK を握ったままか。"""
    return bool(_ACC_PROBE_THREAD is not None and _ACC_PROBE_THREAD.is_alive())


def _exit_now_if_probe_abandoned():
    """★ v1.48 配布前レビュー（Gemini）: 応答しない OpenD に接続したまま残ったスレッドがあると、
    SDK の後片付け（atexit）で終了できなくなることがある。保存も表示も終わったあとなので、
    出力を流し切ってからプロセスを落とす。"""
    if not (_ACC_PROBE_ABANDONED and _WIZARD_FINISHED_OK):
        return                                   # 途中終了や検査プロセスでは終了コードを触らない
    try:
        sys.stdout.flush(); sys.stderr.flush()
    except Exception:
        pass
    os._exit(0)


atexit.register(_exit_now_if_probe_abandoned)


def _detect_real_acc_ids_blocking(host, port):
    """OpenD から実口座一覧を取る本体（呼び出し側で見切るのでここは待ち続けてよい）。"""
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
            # ★ v1.48: 既定は MARGIN の番号にする（従来は常に [1]。CASH が [1] だと、断っても
            #   また [1] が現在値になり、Enter を押し続けると同じ警告を繰り返していた）。
            _margin_idx = next((str(i) for i, (_a, _t) in enumerate(accs, 1)
                                if "MARGIN" in str(_t).upper()), "")
            # ★ v1.48（配布前レビュー Claude 別人格）: いま .env にある口座があればそれが現在値。
            #   Enter で実口座IDが黙って別の口座に変わってはいけない。無ければ MARGIN を薦める。
            _cur_idx = next((str(i) for i, (_a, _t) in enumerate(accs, 1) if str(_a) == str(cur_acc).strip()), "")
            _pick_default = _cur_idx or _margin_idx or "1"
            if _margin_idx and not _cur_idx:
                print(f"    {dim('（Enter で [' + _margin_idx + '] の MARGIN 口座を選びます）')}")
            elif _cur_idx:
                print(f"    {dim('（Enter で現在の設定 [' + _cur_idx + '] を維持します）')}")
            # ★ v1.24: 選択ループ。MARGIN(信用)以外は警告＋再確認。
            while True:
                pick = ask("使用する口座の番号", default=_pick_default)
                try:
                    idx = int(pick) - 1
                except ValueError:
                    warn("番号で入力してください。"); continue
                if not (0 <= idx < len(accs)):
                    warn("一覧の範囲外の番号です。"); continue
                aid, atype = accs[idx]
                if "MARGIN" not in str(atype).upper():
                    print()
                    warn(f"⚠ 選んだ口座の種別は「{atype}」です（信用口座＝MARGIN ではありません）。")
                    warn("　このBotは『信用取引口座（MARGIN・米国株の信用取引と空売りができる口座）』を前提に設計されています。")
                    warn("　現物口座（CASH）や先物・オプション用の口座（DERIVATIVES）では、空売りの注文が通らないなど正しく動きません。")
                    if not ask_yn("それでもこの口座を使いますか？", default=False):
                        if _margin_idx and _margin_idx != str(idx + 1):
                            _pick_default = _margin_idx
                            info(f"別の口座を選び直してください（Enter で [{_margin_idx}] の MARGIN 口座を選びます）。")
                        else:
                            _pick_default = ""      # MARGIN が無い一覧では番号の入力を求める
                            info("別の口座を選び直してください（番号を入力してください）。")
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
        if _acc_probe_stuck():
            # ★ v1.48（配布前レビュー Claude 別人格）: 応答しない OpenD を見切ったあとは、
            #   同じ画面で再試行しても必ず失敗する。案内を変えて、ここで空回りさせない。
            warn("OpenD がポートを開いたまま応答しません（未ログイン・起動途中・固まっている等）。")
            info("いったん Wizard を終了し、moomoo アプリと OpenD を起動し直して「Connected」を確認してから、")
            info("もう一度 Wizard を実行してください。ここでは実口座IDを設定できません。")
            print(f"    {bold('[2]')} いまは設定しない（デモ口座だけで動かす／既存の値があれば保持）")
            ask("Enter で次に進みます", default="2")
            info("実口座IDは設定しません（デモのみ／既存値があれば保持）。")
            return cur_acc
        info("OpenD を起動し、moomoo の実口座にログイン（「Connected」表示）してから再試行してください。")
        print(f"    {bold('[1]')} 再試行（OpenD を起動・実口座にログインしてから）")
        print(f"    {bold('[2]')} いまは設定しない（デモ口座だけで動かす／既存の値があれば保持）")
        print(f"         {dim('※ 実口座は 02_Real（Windows は Start-Bot-Real）で起動したときだけ使われます。01_Demo で起動すればお金は動きません。')}")
        retry = ask("番号を選択", default="1")
        if retry == "2":
            info("実口座IDは設定しません（デモのみ／既存値があれば保持）。")
            return cur_acc
        # それ以外（"1" 含む）→ 再試行
        continue


def step11_connection(existing):
    header(12, TOTAL, "🔌 STEP 12 ── moomoo OpenD 接続設定")
    print("  デモだけで使う方は、そのまま Enter 3回でOKです（接続先2つ＋実口座 N）。\n")
    info("OpenD はローカルPC上で動作します（127.0.0.1:11111 がデフォルト）。")
    info("取引ロックが発生した場合は、moomooアプリで手動でアンロックしてください。")
    cur_host = existing.get("MOOMOO_HOST") or "127.0.0.1"
    cur_port = existing.get("MOOMOO_PORT") or "11111"
    host = ask("MOOMOO_HOST", default=cur_host) or cur_host
    # ★ v1.30: PORT を検証（数値・1〜65535）。無検証保存だとボット本体が
    #   モジュール読込時の int() で即トレースバック死するため、ここで弾く。
    while True:
        port = ask("MOOMOO_PORT", default=cur_port,
                   validate=lambda _v: _num_in_range(_v, 1, 65535, integer_only=True))
        port = str(port).strip()
        if port.isdigit() and 1 <= int(port) <= 65535:
            break
        warn(f"MOOMOO_PORT が不正です（{port!r}）。1〜65535 の数値で入力してください（既定 11111）。")
    ok(f"接続先: {host}:{port}")

    # ── ★ v1.24: 実口座（02_Real / --live）用 acc_id 設定。デモのみなら不要・スキップ可 ──
    print()
    print(f"  {bold('実口座（02_Real で起動）で取引しますか？')}")
    print(f"  {dim('デモ（シミュレーション）だけで使う方は「いいえ」でOK（後でWizard再実行で設定できます）。')}")
    cur_acc = existing.get("MOOMOO_ACC_ID", "").strip()
    if cur_acc:
        info(f"現在の MOOMOO_ACC_ID: {_mask_acc(cur_acc)}（実口座IDは設定済み）")
    use_live = ask_yn("実口座を使う（MOOMOO_ACC_ID を設定する）", default=bool(cur_acc))
    if use_live:
        acc_id = _setup_real_acc_id(host, port, cur_acc)
    else:
        info("デモのみ。実口座IDは設定しません（02_Real での起動はできません／既存値があれば保持）。")
        acc_id = cur_acc

    ok_box([
        ("MOOMOO_HOST", host),
        ("MOOMOO_PORT", port),
        ("MOOMOO_ACC_ID", _mask_acc(acc_id) if acc_id else "（未設定＝デモのみ）"),
    ])
    next_step_pause()
    return {"MOOMOO_HOST": host, "MOOMOO_PORT": port, "MOOMOO_ACC_ID": acc_id}


def step_data_collect(existing):
    header(13, TOTAL, "📊 STEP 13 ── 取引データ収集への参加（任意）")

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

    戦略プロファイル (MOMENTUM_STRATEGY_PROFILE / NEWS_STRATEGY_PROFILE) は ★ v1.46 から STEP 1 で選ぶ。
    ここでは選んだ結果を読み、選抜なら [1]〜[6] を尋ねずに実発注の Y/N だけ確認する。
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
    header(14, TOTAL, "⚡ STEP 14 ── モメンタム発注設定（実発注の対象を決める重要設定）")
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
    if _is_mom_select(existing.get("MOMENTUM_STRATEGY_PROFILE", "select_v2")):
        # 選抜では [2-c] を尋ねない。無い入力欄へ案内しない（認定サポーターの報告）。
        print(f"  {bold('発注対象（選抜プロファイルでは、STEP 1 で選んだプロファイルが実発注の対象を絞り込みます）')}")
    else:
        print(f"  {bold('発注対象（実発注は下の [2-c] で銘柄ごと・方向ごとに選べます）')}")
    if _is_mom_select(existing.get("MOMENTUM_STRATEGY_PROFILE", "select_v2")):
        # 選抜 v2 は SPY と SMH の買いを、v1 は買いと SPY を実発注しない。一般説明のまま「両方に対応」と書かない（認定サポーターの報告）。
        print(f"  {dim('・SPY / QQQ / SMH … 監視の対象。実発注する銘柄と方向は、STEP 1 のプロファイルが絞り込みます（下に表示）。')}")
    else:
        print(f"  {dim('・SPY / QQQ / SMH … 実発注の対象。買い(ロング)・空売り(ショート)の両方に対応。')}")
    print(f"  {dim('  （デモ口座でもネッティング方式で空売りに対応します）')}")
    print(f"  {dim('・IWM / DRAM … シャドー観察のみ（実発注対象外。検証データを収集中）。')}")
    print()

    # ★ v1.46: 戦略プロファイルは STEP 1 で選ぶ。ここでは選んだ結果を読むだけ。
    strategy_profile = str(existing.get("MOMENTUM_STRATEGY_PROFILE", "select_v2")).strip().lower()
    if strategy_profile not in ("standard", "select_v1", "select_v2"):
        strategy_profile = "select_v2"
    is_select_profile = _is_mom_select(strategy_profile)
    news_profile = str(existing.get("NEWS_STRATEGY_PROFILE", "standard")).strip().lower()
    if news_profile not in ("standard", "select_v1"):
        news_profile = "standard"
    print(f"  {dim('戦略プロファイル（STEP 1 で選択）: ' + _mom_profile_label(strategy_profile))}")
    print()

    # ── ★ v1.36: 選抜プロファイル選択時は詳細設定([1]〜[6])をスキップして次STEPへ ──
    # プロファイルが実発注の絞り込み（SHORTのみ・SPY除外・時間帯・固定損切り・日次1.5%）を
    # 内蔵するため、細かいモメンタム設定は尋ねず、他キーは現在値を維持する（シャドーは全記録）。
    if is_select_profile:
        _demo_short = _bot_reads_true(existing, "DEMO_SHORT_ENABLED")
        _mom_stop_keep = _pct_to_percent_str(existing.get("MOMENTUM_STOP_LOSS_PCT", ""), "0.50")
        print(f"  {green(_mom_profile_label(strategy_profile) + ' を選択 → 詳細なモメンタム設定はスキップします。')}")
        print(f"  {dim('プロファイルが以下を自動適用します（実発注のみ・シャドー記録は全件そのまま）:')}")
        if strategy_profile == "select_v2":
            print(f"  {dim('  ・買いは QQQ だけ（米国東部時間 9〜11時台）、売りは QQQ / SMH（9・12時台）')}")
            print(f"  {dim('  ・SPY と SMH の買いは対象外')}")
            print(f"  {dim('  ・5分・15分の変化率が Level 2 の基準に届かないときは実発注しない（値が取れない銘柄はその回は見送る）')}")
            print(f"  {dim('    発火頻度の設定が Level 2 より厳しいときは、そちらが効きます')}")
            print(f"  {dim('  ・直近60分で QQQ が +0.15% より上げているときは売りを見送り（値が取れないときは見送らない）')}")
        else:
            print(f"  {dim('  ・空売り(SHORT)のみ実発注（買いは記録のみ）')}")
            print(f"  {dim('  ・SPYは対象外（QQQ / SMH を実発注）')}")
            print(f"  {dim('  ・米国東部時間 9・10・12・13時台のみ新規発注')}")
        print(f"  {dim('  ・固定の損切りライン（建玉トレールは使わない）')}")
        print(f"  {dim('  ・1日の損失が上限（リスク許容度・既定なら予算の 0.5%）に達したら自動停止')}")
        print(f"  {dim('    プロファイルの上限（既定なら予算の 1.5%）も重ねてかけ、先に当たった方で止まります')}")
        # ★ v1.50: 発注サイド。v1 は従来の既定のまま。v2 は買いが肝なので、既定は Bot の既定サイドから
        #   SMH の買いを外したもの（_V2_DEFAULT_SIDES）にし、既存の設定に QQQ の買いが無ければ自動で加えて、そう表示する。
        _sides_default = (_V2_DEFAULT_SIDES if strategy_profile == "select_v2"
                          else "SPY:SELL_SHORT,QQQ:SELL_SHORT,SMH:SELL_SHORT")
        _sides_keep = existing.get("MOMENTUM_ENABLED_SIDES", _sides_default)
        if strategy_profile == "select_v2":
            _pairs_now = {p.strip().upper() for p in str(_sides_keep or "").split(",") if ":" in p}
            # 発注サイドを「なし」（観察のみ）にしている人には、本人が選んだものなので QQQ の買いを足さない。
            # 「なし」は空欄だけではない。Bot は「:」を含む組だけを拾うので、none や ,,, も発注サイドなしになり、
            # IWM だけのような値も SPY / QQQ / SMH の実発注は無い。キーがあってこの3銘柄の組が1つも無ければ「なし」とみなす。
            _sides_chosen_empty = ("MOMENTUM_ENABLED_SIDES" in existing
                                   and not any(p.split(":", 1)[0] in ("SPY", "QQQ", "SMH") for p in _pairs_now))
            if _sides_chosen_empty:
                print()
                print(f"  {dim('  発注サイドが「なし」（観察のみ）の設定なので、QQQ の買いは加えません。')}")
                print(f"  {dim('  v2 の買いを実発注するには、STEP 1 でカスタマイズ設定を選び、発注サイドを選び直してください。')}")
            elif "QQQ:BUY" not in _pairs_now:
                # PAN 指示（2026-09-13）: v2 は買いが肝なので、QQQ の買いは尋ねずに加え、加えたことをはっきり出す。
                _sides_keep = ",".join([p.strip() for p in str(_sides_keep or "").split(",") if p.strip()] + ["QQQ:BUY"])
                print()
                print(f"  {yellow('選抜プロファイル v2 は買いも実発注の対象にするため、発注サイドに QQQ の買いを加えました。')}")
                print(f"  {dim('  実発注を行う設定なら、QQQ の買いの注文も出るようになります（v2 をやめれば外せます）。')}")
            _eff_now = _effective_select_v2_sides(_sides_keep)
            # 実発注するかは、この後の「実発注の確認」で決まる。オフの人に「実発注される」と言い切らない。
            _live_note = "" if _bot_reads_true(existing, "MOMENTUM_LIVE_TRADING") else "（いまは実発注オフ・記録のみ。下で変えられます）"
            print(f"  {dim('  ・実発注する場合の対象サイド: ' + (_fmt_momentum_sides(_eff_now) if _eff_now else 'なし') + _short_gate_note(existing, _eff_now) + _live_note)}")
        # ★ v1.46（配布前レビュー）: プロファイルが決めない数字は実発注に効くので、金額つきで見せる
        _lv_keep   = str(existing.get("MOMENTUM_LEVEL", "3"))
        _rk_keep   = str(existing.get("MOMENTUM_RISK_LEVEL", "3"))
        _mx_keep   = str(existing.get("MOMENTUM_MAX_PCT", "80"))
        try:
            _mx_usd = budget_val * float(_mx_keep) / 100.0
        except (ValueError, TypeError):
            _mx_usd = 0.0
        print()
        print(f"  {bold('プロファイルが決めないもの（実発注に効きます・いまの値）')}")
        print(f"  {dim(f'  ・1回の最大発注額: 予算の {_mx_keep}%（約 ${_mx_usd:,.0f}）')}")
        print(f"  {dim(f'  ・固定の損切りライン: {_mom_stop_keep}%')}")
        print(f"  {dim(f'  ・シグナルの発火頻度 Lv{_lv_keep} / リスク許容度 Lv{_rk_keep}（1日の損失上限）')}")
        print(f"  {dim('  ※ 変えたいときは STEP 1 でカスタマイズ設定（今まで通り）を選ぶと、ここで個別に設定できます。')}")
        print()
        # ★ v1.38: スキップ時でも「実際に発注するか」だけは必ず確認する（Codexレビュー対応）。
        #   従来はスキップで既定 true のまま通過し、実発注の明示確認が行われなかった。
        print(f"  {bold('実発注の確認（重要）')}")
        print(f"  {dim('選抜プロファイルでも「実際に注文するか」はここで決まります。')}")
        _live_mode_cur = "2" if _bot_reads_true(existing, "MOMENTUM_LIVE_TRADING") else "1"
        _live_choices = [
            ("1", "シャドー観察のみ   実発注なし・「もし注文していたら」を記録のみ"),
            ("2", "実発注も行う      実際に注文する（デモ口座→デモ発注 / 実口座→実発注）← 既定"),
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
        ok("モメンタム設定: " + _mom_profile_label(strategy_profile) + "（詳細設定はスキップ）/ "
           + ("実発注も行う" if _is_live else "シャドー観察のみ"))
        next_step_pause()
        return {
            "MOMENTUM_STRATEGY_PROFILE": strategy_profile,       # ★ v1.50: v2 を v1 に書き戻さない
            "NEWS_STRATEGY_PROFILE":  news_profile,           # ★ v1.46
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
            "MOMENTUM_ENABLED_SIDES":  _sides_keep,
        }

    # ── [1] 発火頻度 ─────────────────────────────────────────────
    print(f"  {bold('[1] シグナル発火頻度 (MOMENTUM_LEVEL)')}")
    print(f"  {dim('どれだけ厳格にシグナルを取りに行くか')}")
    print()
    momentum_level_choices = [
        ("1", "最厳格  (1-2 件/日)  黄金シグナルだけ厳選"),
        ("2", "厳格    (2-3 件/日)  やや慎重"),
        ("3", "標準    (3-5 件/日) ← 既定"),
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
        ("2", "実発注も行う   実際に注文する（デモ口座→デモ発注 / 実口座→実発注）← 既定"),
    ]
    # 既存設定から現在モードを推定 (MOMENTUM_LIVE_TRADING=true なら 2)
    # ★ v3.9.68: 既定を 2(実発注) に変更 (記載が無ければ実発注)
    cur_mode = "2" if _bot_reads_true(existing, "MOMENTUM_LIVE_TRADING") else "1"
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
        ("1", "ON   デモでもショートを実発注する ← 既定"),
        ("2", "OFF  デモのショートは記録のみ（シャドー）"),
    ]
    cur_ds_mode = "1" if _bot_reads_true(existing, "DEMO_SHORT_ENABLED") else "2"
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
    print()
    # 各銘柄の既定は「両方(1)」。IWM/DRAM はシャドー観察のみのため実発注選択肢から除外。
    _SIDE_SYMS = ["SPY", "QQQ", "SMH"]
    _std = {"SPY": "1", "QQQ": "1", "SMH": "1"}
    # 既存 env からの現在値推定
    cur_sides_set = set(s.strip().upper() for s in
                        existing.get("MOMENTUM_ENABLED_SIDES", "").split(",") if ":" in s)
    # キーがあるのに組が1つも無い（空欄・none・,,, など）＝本人が「なし」を選んだ。Bot も発注サイドなしと読む。
    # 以前はこれを「未設定」と同じに扱い、Enter で標準セット（5サイド）が書かれて実発注が始まっていた。
    _sides_chosen_none = ("MOMENTUM_ENABLED_SIDES" in existing) and not cur_sides_set

    def _cur_mode_for(sym):
        has_buy = f"{sym}:BUY" in cur_sides_set
        has_sht = f"{sym}:SELL_SHORT" in cur_sides_set
        if has_buy and has_sht: return "1"
        if has_buy:             return "2"
        if has_sht:             return "3"
        if cur_sides_set or _sides_chosen_none:
            return "4"                        # env明示済みで当該銘柄なし＝なし
        return _std[sym]                      # env未設定＝既定（両方）

    # ★ v1.21 (点3): まず「標準セット一括 / 個別選択」で分岐。大半は1画面で抜けられる。
    setup_choices = [
        ("1", "標準セットでまとめて設定（SPY・QQQ = 買い+売り、SMH = 売りのみ）← 既定"),
        ("2", "1銘柄ずつ方向を選ぶ（上級者向け）"),
    ]
    # ★ v1.42: 既存が標準セット以外のカスタムなら既定を[2]個別選択にし、Enterで上書きしない
    _std_sides_set = {f"{s}:{d}" for s in _SIDE_SYMS for d in ("BUY", "SELL_SHORT")} - {"SMH:BUY"}
    _setup_default = "2" if (_sides_chosen_none or (cur_sides_set and cur_sides_set != _std_sides_set)) else "1"
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
                # 買い+売りなら売りだけを残す。買いだけの人は、Enter で売りを増やさず「なし」にする。
                if _d == "1":
                    _d = "3"
                elif _d == "2":
                    _d = "4"
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
        print(f"  {dim('1日の損失上限は次の[3]リスク許容度で決まります（既定 Lv3 は予算の 0.5%・約 $' + format(budget_val * 0.005, ',.0f') + '）。')}")
        print(f"  {dim('別に予算の約3%（≒ $' + format(_cb_usd, ',.0f') + '）の上限も重ねてありますが、通常は[3]の方が先に効きます。')}")
        print()
    except Exception:
        pass
    if not enabled_sides:
        warn("実発注サイドが0件です（モメンタムは全て観察のみになります）。")
    _sides_disp = enabled_sides if enabled_sides else "（なし・観察のみ）"

    # ── ★ v1.34 [2-d] ロング発注のシグナル強度レンジ（5分モメンタム）─────────
    print(f"  {bold('[2-d] ロング発注のシグナル強度レンジ（5分モメンタム）')}")
    print(f"  {dim('買い(ロング)を実発注する5分モメンタムの範囲を選びます。ショートは対象外です。')}")
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
        ("3", "標準      1回-0.20% / 1日-0.50% / 急変動±0.70%  ← 既定"),
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
        mark = green("  ← 既定") if pct == 80 else ""
        fee = yellow("  ⚠ 手数料負けしやすい") if amt < 5000 else ""
        print(f"    {pct:3d}%  →  最大 ${amt:,.0f}{mark}{fee}")
    print()
    cur_max = existing.get("MOMENTUM_MAX_PCT", "80")
    while True:
        # ★ v1.49: 現在値が 50〜100 でないとき、Enter が通らないのに「Enter=現在値」と
        #   出していた（認定サポーターの報告・v1.48 の取りこぼし）。validate で既定を落とす。
        val = ask("最大発注比率 %（50〜100 の整数 / Enter=現在値）", default=cur_max,
                  validate=lambda _v: _int_trunc_in_range(_v, 50, 100))
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
    print(f"  {green('  0.50%  標準（時間切れ60分まで粘りやすい）← 既定')}")
    print(f"  {dim('  0.80%  粘る（1回の損失は増えるが伸ばせる）')}")
    print()
    cur_stop = existing.get("MOMENTUM_STOP_LOSS_PCT", "0.50")
    while True:
        # ★ v1.49: 上と同じ（現在値が範囲外だと Enter で進めないループになる）。
        val = ask("モメンタム損切り %（0.10〜5.0 / Enter=現在値）", default=cur_stop,
                  validate=lambda _v: _num_in_range(_v, 0.10, 5.0))
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
    print(f"        {dim('選抜プロファイル v1 と同じ出口。カスタマイズ設定でこれを選ぶと')}")
    print(f"        {dim('シートに「+flatstop」の印が付き、建玉トレール群との比較検証に使われます（Bot v3.9.128〜）。')}")
    print()
    print(f"  {dim('※ 既定は [1] 建玉トレール。ただし過去の集計では、細かく往復する場面で損切りが早まり、')}")
    print(f"  {dim('   損失の大きな部分を占めていました。[2] 固定損切りに替える効果を検証中です（協力いただける方は [2]）。')}")
    print(f"  {dim('※ 下方向へ一直線に動く場合は、[1] でも [2] と同じ損切り幅で守られます（不利になりません）。')}")
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
                     if is_select_profile else "カスタマイズ設定（今まで通り・絞り込みなし）")
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
        "NEWS_STRATEGY_PROFILE":  news_profile,          # ★ v1.46 ニュース選抜プロファイル (Bot v3.9.169)
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


def _ask_news_profile(existing):
    """★ v1.46: ニュース選抜プロファイル v1（Bot v3.9.169）。戻り値は "select_v1" / "standard"。

    6週間（7/13〜8/21・設定資金 $100k 未満）の実データで、ニュース売買の損失源は MACRO だけ
    （平均 −0.015%・t=−5.8）。TECH＋SEMI_STRONG に絞ると平均 +0.018%（t=+3.0）で、優位性は
    RTH に集中していた。選ぶと新規エントリーを TECH / SEMI_STRONG かつ RTH に限る。
    決済（既存ロングの決済・ショートの買い戻し・パニックセル）は止めない。
    未設定の新規は select_v1 を既定表示（モメンタムの [0] と同じ考え方。利益は非保証）。"""
    print(f"  {bold('B. ニュース選抜プロファイル v1（ニュース連動の新規エントリーの絞り込み）')}")
    print(f"  {dim('ニュース連動の売買（STEP 7 の銘柄）にも、モメンタムと同じ発想の絞り込みを選べます。')}")
    print()
    # 配布前レビュー（Claude 別人格）: キーが無い＝Bot の既定 standard で動いている人。Enter で
    #   動作が変わらないよう、既存 .env がある場合の既定は standard。新規セットアップだけ select_v1。
    _raw_news = str(existing.get("NEWS_STRATEGY_PROFILE", "")).strip().lower()
    if _raw_news in ("standard", "select_v1"):
        _cur_news = _raw_news
    else:
        _cur_news = "select_v1" if not existing else "standard"
    _cur_news_mode = "1" if _cur_news == "standard" else "2"
    print(f"  {green('▶') if _cur_news_mode == '1' else ' '} [1] カスタマイズ設定（今まで通り）")
    print( "        カテゴリ・時間帯の絞り込みなし。STEP 6 で自分で決めた時間帯設定がそのまま使われます。")
    print(f"  {green('▶') if _cur_news_mode == '2' else ' '} [2] ニュース選抜プロファイル v1（TECH / SEMI_STRONG・RTH のみ）")
    print( "        6週間の実データ（7/13〜8/21）で、ニュース売買の損失源はカテゴリ MACRO だけでした")
    print( "        （平均 −0.015%）。TECH と SEMI_STRONG に絞ると平均 +0.018% で、優位性は RTH に集中。")
    print( "        絞り込みの内容:")
    print( "          ① カテゴリ … 新規エントリーは TECH / SEMI_STRONG のニュースだけ（MACRO は新規建てしない）")
    print( "          ② 時間帯   … 新規エントリーは通常取引時間（RTH）のみ")
    print( "          ③ 決済     … 既存建玉の決済・買い戻し・パニックセルは今まで通り（止めません）")
    print( "                       （通常取引時間の外にニュース取得や決済を止めるか、移行前に全決済するかは STEP 6 の設定で決まります。")
    print( "                        STEP 15 の OVN取引機能は別枠で、STEP 6 の設定では止まりません）")
    print( "        見送ったニュースは全件シャドー記録に残り、毎週の集計で効果を確認できます。")
    print( "        （成績は変動し、利益は保証しません。個別株・決算ニュース由来の発注は対象外です）")
    print()
    _choices = [
        ("1", "カスタマイズ設定（今まで通り）"),
        ("2", "ニュース選抜プロファイル v1（TECH / SEMI_STRONG・RTH のみ）← 既定"),
    ]
    _sel = ask_choice("番号を選択（Enter=現在値を維持）", _choices, default=_cur_news_mode)
    news_profile = "select_v1" if _sel == "2" else "standard"
    ok("ニュース選抜プロファイル: " + ("v1（TECH / SEMI_STRONG・RTH のみ新規建て）" if news_profile == "select_v1"
                                     else "カスタマイズ設定（今まで通り）"))
    return news_profile


_OVN_VIX_CHOICES = [
    ("loose",  "ゆるめ   … VIXY が前日比で上がっていなければ買う（0% 以下）"),
    ("normal", "標準     … VIXY が前日比 −2% 以下のときだけ買う（過去データで成績を確かめたときの条件）← 既定"),
    ("strict", "きびしめ … VIXY が前日比 −3% 以下のときだけ買う"),
]


def _ovn_set_by(enabled: bool) -> str:
    """★ v1.46: 「自分で OVN を設定した」記録。Wizard の版・日付・使う/使わない（Bot は読まない）。"""
    return f"Wizard {WIZARD_VERSION} {datetime.date.today().isoformat()} " + ("使う" if enabled else "使わない")


def step_ovn(existing, budget):
    """★ v1.46: OVN取引機能（夜間持ち越し・Bot v3.9.13x〜）。Wizard の既定は「使う」・実売買の確認は Y 既定（PAN 指示）。
    自分で設定したことが後から分かるよう、OVN_SET_BY（Wizard の版・日付・使う/使わない）を .env に残す。

    引け際（15:55 ET）に条件がそろえば QQQ を買い、翌営業日の寄り付き（9:31 ET）で売る。
    条件は「QQQ の終値が 200 日線より上」かつ「VIXY の前日比が設定以下」。連休の前は既定で見送る。
    日中のニュース売買・モメンタムとは別枠の金額（OVN_BUDGET_USD）で動く。"""
    header(15, TOTAL, "🌙 STEP 15 ── OVN取引機能（夜間持ち越し・任意）")
    try:
        budget_val = float(budget)
    except (ValueError, TypeError):
        budget_val = 0.0

    print(f"  {bold('概要')}")
    print(f"  {dim('米国市場が閉まっている夜のあいだ QQQ を持つ、日中の売買とは別枠の機能です（時刻は米国東部時間）。')}")
    print(f"  {dim('・引け際（15:55）に条件がそろえば、Q3 の金額で買える株数の QQQ を買い、')}")
    print(f"  {dim('  翌営業日の開始直後（9:31）に売って現金に戻します')}")
    print(f"  {dim('・条件: QQQ の終値が過去 200 日の平均より上、かつ VIXY（相場の不安の強さを表す ETF）の前日比が設定以下')}")
    print(f"  {dim('・損益の目安: $800 で持ち越して翌朝 1% 下がれば約 −$8、3% 下がれば約 −$24（上がれば同じだけ利益）')}")
    print(f"  {dim('  （判定は前日の終値までのデータで行います。当日の一時的な値動きに振り回されないためで、')}")
    print(f"  {dim('   当日 15:55 までの値動きは条件に入りません）')}")
    print(f"  {dim('・実口座では引け後（16:05）に「翌朝の開始直後に売る」注文を予約します。予約が通れば Bot を止めても売れます')}")
    print(f"  {dim('  （予約後は証券会社側で注文が管理されます。約定は保証されないので、翌朝の注文状態を確認してください）')}")
    print(f"  {dim('  （予約を置く時刻に Bot が動いている必要があります。予約が通らなかった日は翌朝 9:31 に Bot が売るので、')}")
    print(f"  {dim('   翌朝も Bot を動かしておいてください。デモ口座は常に翌朝 9:31 に Bot が売ります）')}")
    print(f"  {dim('・買った・売った・見送った理由は Discord（STEP 11 で設定）と画面の [夜間持ち越し] の行で確認できます')}")
    print(f"  {dim('・早引けの日（感謝祭の翌日など）は買いません')}")
    print(f"  {dim('・この機能は STEP 6 の時間帯設定（オーバーナイトを「発注しない」にしても）とは別枠で動きます')}")
    print(f"  {dim('・1回に使う金額は Bot 本体の予算（BUDGET_USD）とは別枠です')}")
    print()
    print(f"  {yellow('⚠ 夜間は損切りが効きません。翌朝の寄り付きが大きく下げた日は、そのまま損失になります。')}")
    print(f"  {yellow('  試すときは、失っても困らない金額から始めてください。')}")
    print()

    # ★ v1.46: 既定は「使う」（PAN 指示）。既存 .env で false と書いてある人だけ「使わない」が既定
    # 書いてある値は Bot と同じく「true のときだけ使う」と読む（0 / no / 空欄の人を Enter で使う側にしない）。
    # キーが無い人の既定「使う」は PAN 指示のまま。OVN_MODE も Bot と同じく live のときだけ実売買で、空欄は記録のみ。
    _cur_enabled = ("OVN_ENABLED" not in existing) or _bot_reads_true(existing, "OVN_ENABLED")
    _cur_mode    = str(existing.get("OVN_MODE", "live")).strip().lower()
    _cur_vix     = str(existing.get("OVN_VIX_LEVEL", "normal")).strip().lower() or "normal"
    _cur_budget  = str(existing.get("OVN_BUDGET_USD", "")).strip()
    _cur_hol     = str(existing.get("OVN_SKIP_LONG_HOLIDAY", "true")).strip().lower() != "false"
    _cur_wknd    = str(existing.get("OVN_SKIP_WEEKEND", "false")).strip().lower() == "true"

    print(f"  {bold('Q1. OVN取引機能を使いますか？')}")
    _en_choices = [
        ("1", "使わない"),
        ("2", "使う ← 既定"),
    ]
    _en_sel = ask_choice("番号を選択（Enter=現在値を維持）", _en_choices, default=("2" if _cur_enabled else "1"))
    if _en_sel != "2":
        ok("OVN取引機能: 使わない")
        ok_box([("OVN_ENABLED", "false（使わない）"), ("OVN_SET_BY", _ovn_set_by(False))])
        next_step_pause()
        return {
            "OVN_ENABLED":           "false",
            "OVN_SET_BY":            _ovn_set_by(False),
            # 以前の設定は残す（再び有効にしたときに引き継ぐ）
            "OVN_MODE":              _cur_mode if _cur_mode in ("live", "shadow") else "shadow",
            "OVN_VIX_LEVEL":         _cur_vix if _cur_vix in ("loose", "normal", "strict") else "normal",
            "OVN_BUDGET_USD":        (_cur_budget if _ovn_budget_ok(_cur_budget) else "0"),
            "OVN_SKIP_LONG_HOLIDAY": "true" if _cur_hol else "false",
            "OVN_SKIP_WEEKEND":      "true" if _cur_wknd else "false",
        }

    # [2] 実際に売買するか
    print()
    print(f"  {bold('Q2. 実際に売買しますか？')}")
    _mode_choices = [
        ("1", "記録のみ      買った場合の結果だけを記録する（注文しない）"),
        ("2", "実際に売買    引け際に買い、翌寄りで売る（デモ口座→デモ発注 / 実口座→実発注）"),
    ]
    # 配布前レビュー: OVN_MODE が live 以外（shadow や不正値）なら Enter の既定は「記録のみ」（Bot と同じ扱い）
    _mode_sel = ask_choice("番号を選択（Enter=現在値を維持）", _mode_choices, default=("2" if _cur_mode == "live" else "1"))
    _live = (_mode_sel == "2")
    if _live:
        print()
        print(f"  {yellow('⚠ 実際に売買します。実口座なら実資金が動きます（デモ口座ならデモ発注）。')}")
        # PAN 指示（2026-09-07）: 確認の既定は Y（Enter で実売買）。金額の入力は必須なので Enter だけでは進まない。
        if not ask_yn("OVN取引機能の実売買を有効にします。よろしいですか？", default=True):
            _live = False
            print()
            info("記録のみに切り替えました。注文はしません。")
    mode = "live" if _live else "shadow"

    # [3] 1回に使う金額
    print()
    print(f"  {bold('Q3. 1回に使う金額（ドル・OVN_BUDGET_USD）')}")
    print(f"  {dim('QQQ 1株ぶん（おおよそ $700〜800）に届かない金額では買いません。')}")
    print(f"  {dim('Bot 本体の予算とは別枠ですが、引け際に Bot 本体が QQQ の建玉や注文を持っている日は見送ります。')}")
    print(f"  {dim('1株だけ試すなら、1株より少し多い金額を入れてください（例: 800）。')}")
    if budget_val > 0:
        print(f"  {dim(f'Bot 本体の予算 BUDGET_USD は ${budget_val:,.0f} です。この金額はそれとは別枠で、合計が口座の余力に収まる必要があります。')}")
    print()
    _default_budget = _cur_budget if _cur_budget not in ("", "0", "0.0") else ""
    while True:
        raw = ask("金額を入力（例: 800 ／ b で Q1 の「使わない」に戻る）", default=_default_budget,
                  validate=_ovn_budget_ok)
        if _is_back(raw):   # ★ v1.49: 全角の「ｂ」でも戻れる
            # 配布前レビュー（Claude 別人格）: 必須入力のループに出口が無かった（Ctrl+C しかない）
            info("OVN取引機能を「使わない」にします。")
            ok_box([("OVN_ENABLED", "false（使わない）"), ("OVN_SET_BY", _ovn_set_by(False))])
            next_step_pause()
            return {
                "OVN_ENABLED":           "false",
                "OVN_SET_BY":            _ovn_set_by(False),
                "OVN_MODE":              mode,
                "OVN_VIX_LEVEL":         _cur_vix if _cur_vix in ("loose", "normal", "strict") else "normal",
                "OVN_BUDGET_USD":        (_cur_budget if _ovn_budget_ok(_cur_budget) else "0"),
                "OVN_SKIP_LONG_HOLIDAY": "true" if _cur_hol else "false",
                "OVN_SKIP_WEEKEND":      "true" if _cur_wknd else "false",
            }
        try:
            val = float(_normalize_amount(raw))
        except (ValueError, TypeError):
            warn("数値で入力してください（例: 800。カンマ・$・全角も可）"); continue
        if not (val > 0) or val != val or val in (float("inf"), float("-inf")):
            warn("0 より大きい金額を入力してください（0 以下だと買いません）"); continue
        if val > 1_000_000_000:
            warn("金額が大きすぎます"); continue
        ovn_budget = _fmt_amount(val)   # 1234567 → "1234567"（指数表記にしない）
        break
    if val < 700:
        warn(f"${val:,.0f} は QQQ 1株の値段（目安 $700〜800）に届かない可能性があります。")
        warn("QQQ は1株単位なので、届かない日は何も買いません（エラーにもなりません）。1株から試すなら 800 以上が目安です。")

    # [4] 買う日の厳しさ
    print()
    print(f"  {bold('Q4. 買う日の厳しさ（VIXY の前日比で判定・OVN_VIX_LEVEL）')}")
    vix = ask_choice("番号を選択（Enter=現在値を維持）", _OVN_VIX_CHOICES,
                     default=(_cur_vix if _cur_vix in ("loose", "normal", "strict") else "normal"))

    # [5] 連休・週末
    print()
    print(f"  {bold('Q5. 連休の前は見送る（OVN_SKIP_LONG_HOLIDAY・既定は見送る）')}")
    print(f"  {dim('3連休など、市場が3日以上閉まる前日は買いません。通常の週末は次の Q6 で決めます。')}")
    skip_hol = ask_yn("連休の前は見送りますか？", default=_cur_hol)
    print()
    print(f"  {bold('Q6. 週末（土日）の前も見送る（OVN_SKIP_WEEKEND・既定は持ち越す）')}")
    print(f"  {dim('既定は「持ち越す」（過去データで成績を確かめたときの条件）。金曜は Bot 本体の週末決済のあとに建てます。')}")
    skip_wknd = ask_yn("週末の前も見送りますか？", default=_cur_wknd)

    print()
    ok("OVN取引機能: " + ("実際に売買" if _live else "記録のみ") + f" / 1回 ${val:,.0f} / 買う日の厳しさ " + {"loose": "ゆるめ", "normal": "標準", "strict": "きびしめ"}.get(vix, vix))
    ok_box([
        ("OVN_ENABLED",           "true（使う）"),
        ("OVN_MODE",              f"{'実際に売買' if _live else '記録のみ'}（{mode}）"),
        ("OVN_BUDGET_USD",        f"${val:,.0f}（Bot 本体の予算とは別枠）"),
        ("OVN_VIX_LEVEL",         {"loose": "ゆるめ（VIXY 前日比 0% 以下）", "normal": "標準（VIXY 前日比 −2% 以下）", "strict": "きびしめ（VIXY 前日比 −3% 以下）"}.get(vix, vix)),
        ("OVN_SKIP_LONG_HOLIDAY", "true（連休の前は見送る）" if skip_hol else "false（連休の前も持ち越す）"),
        ("OVN_SKIP_WEEKEND",      "true（週末の前も見送る）" if skip_wknd else "false（週末も持ち越す）"),
        ("OVN_SET_BY",            _ovn_set_by(True) + "（自分で設定した記録・.env に残ります）"),
    ])
    print(f"  {dim('※ この設定はあなた自身が Wizard で選んだものです。.env の OVN_SET_BY に版と日付を残します。')}")
    print(f"  {dim('※ 止めたいときは、この Wizard をもう一度実行して STEP 15 の Q1 で「使わない」を選んで保存してください。')}")
    print(f"  {dim('   保存した設定は次に Bot を起動したときから効きます（動いている Bot はそのままです）。')}")
    print(f"  {dim('   「使わない」は新しい持ち越しを止める設定で、持っている建玉をすぐ売る操作ではありません。')}")
    print(f"  {dim('   持ち越し中の建玉は Bot が翌朝に売ります（デモはその時刻に Bot が動いている必要があります）。')}")
    next_step_pause()
    return {
        "OVN_ENABLED":           "true",
        "OVN_SET_BY":            _ovn_set_by(True),
        "OVN_MODE":              mode,
        "OVN_BUDGET_USD":        ovn_budget,
        "OVN_VIX_LEVEL":         vix,
        "OVN_SKIP_LONG_HOLIDAY": "true" if skip_hol else "false",
        "OVN_SKIP_WEEKEND":      "true" if skip_wknd else "false",
    }


def step_alert_sound(existing):
    """★ v3.9.19: 上級者向け — 重大エラー時のアラート音設定 (デフォルト無効)。"""
    header(16, TOTAL, "🔔 STEP 16 ── 重大エラー時のアラート音（上級者向け・任意）")

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
    print(f"  {dim('夜間ミュート時間帯（ここだけは、あなたのいる日本時間で「寝ている時間」を書きます。HH:MM-HH:MM・日跨ぎ可）')}")
    print(f"  {dim('例: 23:00-06:00  （日本の夜11時〜朝6時は音を鳴らさない。未入力で常時有効）')}")
    # ★ v1.38: HH:MM-HH:MM 形式を検証（不正形式は Bot 側で黙って「ミュートなし」扱いになるため）
    _QH_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d-([01]?\d|2[0-3]):[0-5]\d$")
    # ★ v1.49（配布前レビュー Claude 別人格）: この欄は空が「ミュートなし」を意味するので、
    #   壊れた現在値を既定から落とすと、Enter が「設定を黙って消す」になる。先に断っておく。
    if cur_quiet_hours and not _QH_RE.match(cur_quiet_hours):
        warn(f"いまの値「{cur_quiet_hours}」は HH:MM-HH:MM の形ではありません。")
        info("このまま Enter だけ押すと「ミュートなし（常時有効）」になります。")
    while True:
        # ★ v1.49: 現在値が HH:MM-HH:MM でないと Enter で進めないループになっていた。
        quiet_hours = ask("夜間ミュート時間帯（未入力=常時有効）", default=cur_quiet_hours,
                          validate=lambda _v: bool(_QH_RE.match(str(_v).strip()))).strip()
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


_OVN_VIX_LEVEL_LABELS = {
    "loose":  "ゆるめ（VIXY 前日比 0% 以下）",
    "normal": "標準（VIXY 前日比 −2% 以下）",
    "strict": "きびしめ（VIXY 前日比 −3% 以下）",
}


def _fmt_ovn(config):
    """★ v1.46: 確認画面用の夜間持ち越しの1行"""
    if str(config.get("OVN_ENABLED", "false")).strip().lower() != "true":
        return "使わない"
    _mode = "実際に売買" if str(config.get("OVN_MODE", "live")).strip().lower() == "live" else "記録のみ"
    try:
        _b = float(config.get("OVN_BUDGET_USD", "0") or 0)
    except (ValueError, TypeError):
        _b = 0.0
    _by = str(config.get("OVN_SET_BY", "") or "").strip()
    _raw_lv = str(config.get("OVN_VIX_LEVEL", "normal")).strip().lower()
    _lv = _OVN_VIX_LEVEL_LABELS.get(_raw_lv, f"{_raw_lv}（読めない値のため Bot は標準として扱います）")
    return f"使う（{_mode} / 1回 ${_b:,.0f} / 買う日の厳しさ {_lv}）" + (f"　設定: {_by}" if _by else "")


def _disp_width(text):
    """★ v1.48: 端末での表示幅。全角（East Asian Wide/Fullwidth）は2桁として数える。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def _pad(text, width):
    """ANSIエスケープコードを除いた実表示幅でパディングする
    ★ v1.48: 文字数ではなく表示幅で数える（全角を含むラベルの行だけ値がずれていた）。"""
    visible_len = _disp_width(re.sub(r'\033\[[0-9;]*m', '', text))
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
    # OVN_BUDGET_USD は設定チェック側の validate（_ovn_budget_ok）で検証する
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

def _normalize_amount(raw):
    """★ v1.46: 金額入力の正規化（カンマ・$・全角数字/カンマ/ドル・空白を除く）"""
    import unicodedata as _ud
    _t = _ud.normalize("NFKC", str(raw or ""))
    return _t.replace(",", "").replace("$", "").replace("＄", "").strip()


def _fmt_amount(val):
    """★ v1.46: .env に書く金額。指数表記にせず、小数はあれば2桁まで"""
    _t = f"{float(val):.2f}"
    return _t.rstrip("0").rstrip(".") if "." in _t else _t


def _split_tickers(raw):
    """★ v1.48: 全角英数を半角に直し、カンマ／セミコロン／読点／空白のどれで区切っても同じに読む。"""
    s = unicodedata.normalize("NFKC", str(raw or ""))
    return [t for t in re.split(r"[,;、，；\s]+", s) if t]


def _ovn_budget_ok(v):
    """★ v1.46: 夜間持ち越しの金額の再入力検証（0 より大きい有限の数値）"""
    try:
        _x = float(_normalize_amount(v))
    except (ValueError, TypeError):
        return False
    return _x > 0 and _x == _x and _x not in (float("inf"), float("-inf")) and _x <= 1_000_000_000


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

    # ★ v1.46（配布前レビュー）: RTH 以外が全部「発注しない」なのに移行前全決済が OFF
    try:
        _all_off = all(float(_s(k, "0") or 0) >= 2.0 for k in ("CONFIDENCE_PREMARKET", "CONFIDENCE_AFTERHOURS", "CONFIDENCE_OVERNIGHT"))
    except (ValueError, TypeError):
        _all_off = False
    if _all_off and _s("CLOSE_BEFORE_INACTIVE", "true").lower() == "false":
        warnings.append({
            "level": "warning", "key": "CLOSE_BEFORE_INACTIVE",
            "message": ["RTH 以外が「発注しない」なのに移行前全決済が OFF です。",
                        "16:00 以降に残った建玉は翌朝 9:30 まで Bot が監視しません（損切り・時間切れが効きません）。"],
            "prompt": "移行前全決済を有効にしますか？（はい=Y / いいえ=N）",
            "validate": lambda v: str(v).strip().lower() in ("y", "n", "yes", "no", "true", "false", "はい", "いいえ"),
            "normalize": lambda v: "true" if str(v).strip().lower() in ("y", "yes", "true", "はい") else "false",
        })

    # ★ v1.46: 夜間持ち越し（有効なのに金額が無い／1株に届かない／モードが不正）
    if _s("OVN_ENABLED", "false").lower() == "true":
        _ovn_b = _f("OVN_BUDGET_USD", 0.0)
        if _ovn_b <= 0:
            warnings.append({
                "level": "error", "key": "OVN_BUDGET_USD",
                "message": ["夜間持ち越しが有効なのに 1回に使う金額が 0 です（この設定では買いません）。",
                            "STEP 15 の Q3 で金額を入れるか、Q1 で「使わない」にしてください。"],
                # 配布前レビュー（Gemini）: 修正を選ぶ経路は prompt/validate を必ず使う
                "prompt": "OVN_BUDGET_USD（1回に使う金額・ドル）を再入力",
                "validate": _ovn_budget_ok,
                "normalize": lambda v: _fmt_amount(float(_normalize_amount(v))),
            })
        elif _ovn_b < 700:
            warnings.append({
                "level": "warning", "key": "OVN_BUDGET_USD",
                "message": [f"夜間持ち越しの 1回の金額 ${_ovn_b:,.0f} は QQQ 1株の値段に届かない可能性があります。",
                            "届かない日は買いません。1株だけ試すなら 800 程度を目安にしてください。"],
                "prompt": "OVN_BUDGET_USD（1回に使う金額・ドル）を再入力",
                "validate": _ovn_budget_ok,
                "normalize": lambda v: _fmt_amount(float(_normalize_amount(v))),
            })
        if _s("OVN_MODE", "live").lower() not in ("live", "shadow"):
            warnings.append({
                "level": "warning", "key": "OVN_MODE",
                "message": [f"OVN_MODE の値 {_s('OVN_MODE')!r} は live / shadow 以外です（Bot は記録のみとして扱います）。"],
                "prompt": "OVN_MODE を再入力（live / shadow）",
                "validate": lambda v: str(v).strip().lower() in ("live", "shadow"),
            })
        if _s("OVN_VIX_LEVEL", "normal").lower() not in ("loose", "normal", "strict"):
            warnings.append({
                "level": "warning", "key": "OVN_VIX_LEVEL",
                "message": [f"OVN_VIX_LEVEL の値 {_s('OVN_VIX_LEVEL')!r} は loose / normal / strict 以外です（Bot は normal として扱います）。"],
                "prompt": "OVN_VIX_LEVEL を再入力（loose / normal / strict）",
                "validate": lambda v: str(v).strip().lower() in ("loose", "normal", "strict"),
            })

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
            raw = ask("番号を入力（エラーが無ければ Enter か 0 でこのまま保存）", default="")
            if not raw and not errors:
                return config
            if not raw:
                warn("エラーがあるので、直す項目の番号を入力してください")
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
                # ★ v1.46（配布前レビュー Codex 2周目）: 検証を通った値を正規化してから保存する。
                #   "1,000" をそのまま保存すると次の再検査で float() が失敗し、修正ループから抜けられない。
                _norm = target.get("normalize")
                if _norm:
                    try:
                        new_val = _norm(new_val)
                    except Exception:
                        pass
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
        #   食い違って見える（本体のバナーと同じ不具合。STEP4 の入力画面は
        #   もともと .2f なので、同じ実行の中で表示が矛盾していた）。
        ("TRAIL_TRIGGER_PCT",     f"+{trig_pct:.2f}% でトレール開始",                    "トレール発動"),
        ("TRAIL_DROP_PCT",        f"極値から {drop_pct:.2f}% 戻りで決済（買いは最高値・空売りは最安値）", "トレール幅"),
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
        ("MOMENTUM実発注",        _fmt_momentum_live(config), "モメンタムの売買銘柄（別系統）"),
        ("口座",                  _fmt_account(config), "実口座は 02_Real（Windows は Start-Bot-Real）で起動したときだけ"),
        ("STOCK_TICKERS",         config.get("STOCK_TICKERS","") or "なし",               "個別銘柄監視"),
        ("LIMIT_BUFFER_PCT",      ("ETF 0.30% / 個別株 0.50%" if buf_pct is None else f"{buf_pct:.2f}%（一律）"), "指値バッファ"),
        ("ORDER_CANCEL_MINUTES",  f"{config.get('ORDER_CANCEL_MINUTES','1')}分",     "未約定キャンセル"),
        ("発注サイズ",            "AI の確信度に応じて発注額を自動配分（山型）",           ""),
        ("── 戦略プロファイル・夜間持ち越し ────────────", None, None),
        ("MOMENTUM_STRATEGY_PROFILE", _mom_profile_label(config.get("MOMENTUM_STRATEGY_PROFILE", "select_v2")), "モメンタム"),
        ("NEWS_STRATEGY_PROFILE",     ("ニュース選抜 v1（TECH/SEMI_STRONG・RTH）" if str(config.get("NEWS_STRATEGY_PROFILE", "select_v1")).lower() == "select_v1" else "カスタマイズ設定（今まで通り）"), "ニュース連動"),
        ("OVN_ENABLED",               _fmt_ovn(config), "OVN取引機能（夜間持ち越し）"),
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
    # v1.46 (v3.9.169): ニュース選抜プロファイル (standard / select_v1)
    "NEWS_STRATEGY_PROFILE",
    # v1.46 (v3.9.13x〜): 夜間持ち越し
    "OVN_ENABLED", "OVN_MODE", "OVN_BUDGET_USD", "OVN_VIX_LEVEL",
    "OVN_SKIP_LONG_HOLIDAY", "OVN_SKIP_WEEKEND", "OVN_SET_BY",
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
        base = config.get("STRONG_BUY_CONFIDENCE", "0.70")  # ★ v1.38: STEP5 の既定 0.70 に統一
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
            # ★ v1.48: 読み取り側と同じく export 接頭辞を外す（外さないと同じキーが
            #   「export KEY=…（古い値）」と「KEY=…（新しい値）」の2行に増えてしまう）。
            if key.startswith("export "):
                key = key[len("export "):].strip()

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
    # 空の値は書かないが、MOMENTUM_ENABLED_SIDES の空は「発注サイドなし」という選択なので書く。
    # 書かないと Bot は既定の5サイドで実発注する（Bot は「キーが無い」と「空」を別に読む）。
    missing = [k for k in _WIZARD_MANAGED_KEYS if k not in written_keys
               and (_get_wizard_value(k, config) or (k == "MOMENTUM_ENABLED_SIDES" and k in config))]
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
        "#   MOMENTUM_STRATEGY_PROFILE  戦略プロファイル (select_v2=選抜プロファイル v2[既定 v1.50〜・検証中] /",
        "#                              select_v1=選抜プロファイル v1 / standard=今まで通り・Wizard STEP1 で選択。",
        "#                              select_v1: SHORTのみ/SPY除外/ET 9・10・12・13時台のみ実発注",
        "#                              select_v2: 売り ET 9・12時台/買い ET 9〜11時台/Level 2 以上/直近60分で",
        "#                              QQQ が +0.15% 超なら売り見送り/SPY と SMH の買いは除外",
        "#                              どちらも固定損切り/日次損失はリスク許容度の上限と1.5%を重ね、先に当たった方で停止。",
        "#                              シャドー記録は全件継続)",
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
        f"MOMENTUM_STRATEGY_PROFILE={config.get('MOMENTUM_STRATEGY_PROFILE', 'select_v2')}",
        "#   NEWS_STRATEGY_PROFILE  ニュース選抜プロファイル (select_v1=TECH/SEMI_STRONG かつ RTH のみ新規建て /",
        "#                          standard=今まで通り・Wizard STEP1 で選択。決済は止めない・見送りは全件記録)",
        f"NEWS_STRATEGY_PROFILE={config.get('NEWS_STRATEGY_PROFILE', 'select_v1')}",
        f"MOMENTUM_ENABLED_SIDES={config.get('MOMENTUM_ENABLED_SIDES', 'SPY:BUY,SPY:SELL_SHORT,QQQ:BUY,QQQ:SELL_SHORT,SMH:SELL_SHORT')}",
        f"MOMENTUM_SHADOW_ENABLED={config.get('MOMENTUM_SHADOW_ENABLED', 'true')}",
        f"MOMENTUM_LIVE_TRADING={config.get('MOMENTUM_LIVE_TRADING', 'false')}",
        "# ── 反対シグナルでの転換 (上級者向け・v3.9.89) ──────────",
        "#   false: 保有中に反対シグナルが出ても転換せず見送る (既定・実データで転換は勝率が低いため)",
        "#   true : 従来どおり反対シグナルで強制転換する",
        f"MOMENTUM_REVERSE_EXIT={config.get('MOMENTUM_REVERSE_EXIT', 'false')}",
        "",
        "# ── OVN取引機能 (夜間持ち越し・Wizard STEP15 で選択・任意) ──",
        "#   OVN_ENABLED            true で有効（Wizard の既定は「使う」・.env 直書きの場合の Bot 既定は false）。",
        "#                          引け際(15:55 ET)に条件がそろえば QQQ を買い、翌寄り(9:31 ET)で売る",
        "#   OVN_MODE               live=実際に売買 / shadow=記録だけ",
        "#   OVN_BUDGET_USD         1回に使う金額（Bot 本体の BUDGET_USD とは別枠）。QQQ 1株に届かない金額では買わない",
        "#   OVN_VIX_LEVEL          loose / normal / strict（VIXY 前日比 0% / -2% / -3% 以下で買う）",
        "#   OVN_SKIP_LONG_HOLIDAY  連休の前は持ち越さない（既定 true）",
        "#   OVN_SKIP_WEEKEND       週末の前も持ち越さない（既定 false）",
        f"OVN_ENABLED={config.get('OVN_ENABLED', 'false')}",
        f"OVN_MODE={config.get('OVN_MODE', 'live')}",
        f"OVN_BUDGET_USD={config.get('OVN_BUDGET_USD', '0')}",
        f"OVN_VIX_LEVEL={config.get('OVN_VIX_LEVEL', 'normal')}",
        f"OVN_SKIP_LONG_HOLIDAY={config.get('OVN_SKIP_LONG_HOLIDAY', 'true')}",
        f"OVN_SKIP_WEEKEND={config.get('OVN_SKIP_WEEKEND', 'false')}",
        "#   OVN_SET_BY             自分で設定した記録（Wizard の版・日付・使う/使わない。Bot は読まない）",
        f"OVN_SET_BY={config.get('OVN_SET_BY', '')}",
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
    print(f"  {cyan(_demo_padded)}  ← デモ口座（01_Demo / Start-Bot-Demo をダブルクリックでも同じ）\n")
    print(f"  {cyan(_live_cmd)}  ← 実口座（02_Real / Start-Bot-Real）\n")
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
        " 1  PROFILE       戦略プロファイル（実発注の絞り込み・最初に決める）",
        " 2  BUDGET        発注上限額",
        " 3  RISK          損切り・リスク管理",
        " 4  TRAILING      トレイリングストップ",
        " 5  AI THRESHOLD  AIしきい値（ベース・RTH）",
        " 6  SESSION       時間帯別トレード設定（選抜プロファイルなら自動）",
        " 7  SYMBOLS       銘柄選択",
        " 8  ORDER         発注詳細",
        " 9  ANTHROPIC     Claude APIキー",
        "10  ALPACA        Alpaca News API",
        "11  FINNHUB       Finnhub（ニュース）＋ Discord通知（任意）",
        "12  MOOMOO        moomoo OpenD 接続",
        "13  DATA COLLECT  取引データ収集への参加（任意）",
        "14  MOMENTUM      モメンタム発注設定（実発注の確認・選抜プロファイルなら詳細は自動）",
        "15  OVN           OVN取引機能（引け際に QQQ を買い翌寄りで売る・任意）",
        "16  ALERT SOUND   重大エラー時のアラート音（任意）",
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

    def _step1(s):  return step_profiles(s)                      # ★ v1.46: 戦略プロファイルを最初に
    def _step2(s):  return {"BUDGET_USD": step1_budget(s)}
    def _step3(s):  return step2_risk(s, s.get("BUDGET_USD", 0))
    def _step4(s):  return step3_trailing(s)
    def _step5(s):  return step4_confidence(s)
    def _step6(s):  return step5_session(s, s.get("STRONG_BUY_CONFIDENCE", ""))
    def _step7(s):  return step6_symbols(s)
    def _step8(s):  return step7_order_detail(s)
    def _step9(s):  return {"ANTHROPIC_API_KEY": step8_anthropic(s)}
    def _step10(s): return step9_alpaca(s)
    def _step11(s): return step10_finnhub(s)
    def _step12(s):
        r = step11_connection(s)
        r["MOOMOO_RSA_KEY"] = s.get("MOOMOO_RSA_KEY", "")
        return r
    def _step13(s): return step_data_collect(s)
    def _step14(s): return step_momentum(s, s.get("BUDGET_USD", 0))
    def _step15(s): return step_ovn(s, s.get("BUDGET_USD", 0))
    def _step16(s): return step_alert_sound(s)

    _steps = [_step1, _step2, _step3, _step4, _step5, _step6, _step7, _step8,
              _step9, _step10, _step11, _step12, _step13, _step14, _step15, _step16]

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
        # ★ v1.48: ここまで来たら画面も保存も終わり。応答しない OpenD を見切っていた場合だけ、
        #   SDK を握ったままのスレッドで終了できなくなるのを避けてプロセスを落とす（_exit_now_if_probe_abandoned）。
        globals()["_WIZARD_FINISHED_OK"] = True
    except (KeyboardInterrupt, EOFError):
        print("\n\n  " + yellow("キャンセルしました。"))
        sys.exit(0)

if __name__ == "__main__":
    main()

