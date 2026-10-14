# ARTICLE_LOGGING.md

## 記事操作のログ

記事作成、成果計測URLへの差し替え、内部リンク更新、公開確認を行ったらARTICLE_LOG.jsonへ操作履歴を追加し、ARTICLE_LOG.mdへ人が読める一覧を反映する。ARTICLE_INDEX.jsonは現在の状態、ログは時系列の履歴として扱う。設定ファイルの変更は記事作成ログへ混ぜない。

## 記録項目

ARTICLE_LOG.jsonのeventsは以下のフィールドを持つオブジェクトの配列とする。

- event_id：一意な操作ID
- occurred_at：実際の操作日時。Asia/TokyoのISO 8601形式で+09:00を付ける
- article_id、title、slug：対象記事
- action：created、affiliate_replaced、internal_links_updated、images_generated、image_urls_updated、publication_confirmedのいずれか
- revision：記事の版番号。初回は1、内容更新時に増やす
- body_characters、minimum_body_characters、length_check_status：その版の実測本文文字数、適用下限、passed・failed・unverified。実測未完了の値を推測しない
- publication_status：draftまたはpublished。ローカル更新だけで公開状態を変えない
- link_status：official、affiliate、mixed、noneのいずれか。商品リンクの現在状態
- body_path、info_path、snapshot_body_path、snapshot_info_path：最新本文・管理情報とその版の保存先
- changes：product_id、provider、old_url、new_url、change_typeを持つ配列。リンク変更がなければ空配列
- images：画像のrole、path、alt、generation_status、published_urlを持つ配列。URL未指定ならpublished_urlはnull
- notes：未確認の提携先、公式URLが見つからない商品、その他の未解決事項

URLやパスを架空の値で埋めない。不明値はnullまたは未確認とし、過去の操作日時を推測してログを作らない。

## 保存と一覧

1. 初回作成はarticles/<slug>/article-body.mdとarticle-info.mdを保存し、同じ内容をarticles/<slug>/history/0001/article-body.mdとarticle-info.mdへ保存する。
2. 更新前に直前の版がhistoryにあるか確認し、未保存なら実ファイルから退避する。更新後は新しい版番号のhistoryへ本文と管理情報の両方を保存する。既存の版を上書きしない。
3. 記事ファイルとスナップショットの保存成功を確認してから、現在の台帳を更新してイベントを追加する。保存に失敗した操作を完了ログへ記録しない。

新規作成のcreatedイベントは文字数チェックの合格後に記録する。ARTICLE_LOG.mdの記事一覧には実測本文文字数と合否も表示する。
4. ARTICLE_LOG.mdは「記事一覧」と「操作履歴」に分ける。記事一覧はタイトル、更新日時、版、公開状態、商品リンク状態、本文・管理情報・提携先情報へのリンクを表示する。操作履歴は日時、記事、操作内容、変更URL、対応する版へのリンクを表示する。
5. 再実行で本文や管理情報に変更がなければ版やイベントを増やさない。記録済みイベントを削除・改変せず、新しい操作を追加する。ARTICLE_LOG.mdの現在状態一覧は台帳に合わせて更新してよい。

画像を再生成する場合は既存の画像ファイルを上書きせず、版番号などを含む新しいファイル名で保存する。履歴の本文が参照する旧画像も保持する。履歴の相対画像パスは元の記事フォルダを基準に解決するものとし、過去の版を表示・復元する際は保存されたimagesのパスを使う。

過去の記事ファイルを後から取り込む場合は、取り込んだ時刻と未確認の過去日時を区別し、notesへ明記する。空のログはこの仕組みに未登録であることだけを意味する。

記事作成・更新の応答ではARTICLE_LOG.mdへのリンクも提示する。過去の本文を確認する依頼では、指定された版をhistoryから読む。
