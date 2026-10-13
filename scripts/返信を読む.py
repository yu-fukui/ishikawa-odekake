"""1本の投稿への返信の中身を、ジョブのログにだけ出す（リポジトリには書かない）

2026-10-13 運用部・石川担当（代表の依頼）：14時の問いかけ投稿への返信を集計するため。
代表「返信の本文そのものを外に出さない（集計だけ）」。ユーザー名はログにも出さない。

環境変数:
  THREADS_ACCESS_TOKEN … 今の投稿用のトークン
  POST_ID              … 返信を読みたい投稿の ID（数字）
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.threads.net/v1.0"
# username は取らない（ログにも出さないため）
FIELDS = "id,text,timestamp,is_reply_owned_by_me,replied_to,root_post,hide_status"


def get(path: str, params: dict) -> dict:
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.environ['THREADS_ACCESS_TOKEN']}"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def エラー文(e: urllib.error.HTTPError) -> str:
    try:
        d = json.load(e)
        err = d.get("error", {})
        return f"{e.code} {err.get('type', '')} code={err.get('code', '')}: {err.get('message', '')}"[:300]
    except Exception:
        return str(e.code)


def 返信を全部(post_id: str) -> list[dict]:
    出, after = [], None
    while True:
        p = {"fields": FIELDS, "reverse": "false", "limit": 100}
        if after:
            p["after"] = after
        d = get(f"{post_id}/conversation", p)
        出 += d.get("data", [])
        after = ((d.get("paging") or {}).get("cursors") or {}).get("after")
        if not after or not (d.get("paging") or {}).get("next"):
            return 出


def いいね(reply_id: str) -> str:
    try:
        d = get(f"{reply_id}/insights", {"metric": "likes"})
        for m in d.get("data", []):
            vals = m.get("values") or [{}]
            v = m.get("total_value", {}).get("value", vals[0].get("value"))
            return str(v)
    except urllib.error.HTTPError:
        return "取れない"
    return "?"


def main() -> None:
    post_id = os.environ.get("POST_ID", "").strip()
    if not post_id.isdigit():
        sys.exit("POST_ID は数字の投稿 ID を入れてください")
    try:
        返信 = 返信を全部(post_id)
    except urllib.error.HTTPError as e:
        print(f"::error::返信を読めません（{エラー文(e)}）")
        print("足りない権限の候補：threads_read_replies（返信を読む）。トークンを作るときにこの権限を足す必要があります。")
        sys.exit(1)
    自分 = sum(1 for r in 返信 if r.get("is_reply_owned_by_me"))
    print(f"投稿 {post_id} への返信：{len(返信)} 件（こちらの返信 {自分} 件・ほかの人 {len(返信) - 自分} 件）")
    いいねが取れた = False
    for i, r in enumerate(返信, 1):
        誰 = "こちら" if r.get("is_reply_owned_by_me") else "ほかの人"
        先 = (r.get("replied_to") or {}).get("id")
        段 = "投稿への返信" if not 先 or 先 == post_id else "返信への返信"
        数 = いいね(r["id"])
        いいねが取れた |= 数 not in ("取れない", "?")
        本文 = " ".join((r.get("text") or "").split())
        隠し = "（非表示）" if r.get("hide_status") not in (None, "NOT_HUSHED", "") else ""
        print(f"{i:>3}. [{誰}・{段}・いいね {数}{隠し}] {本文}")
    if 返信 and not いいねが取れた:
        print("※ ほかの人の返信のいいね数は、今の API（insights）では取れませんでした。")


if __name__ == "__main__":
    main()
