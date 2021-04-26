import datetime
import json
import math
import os
import time
import traceback

import requests
import schedule
import twitter
from PIL import Image, ImageFont, ImageDraw

os.chdir(os.path.dirname(os.path.abspath(__file__))) #カレントディレクトリを同一階層に(これをやらないとc:\users\username内にファイルを作りやがる)

def unexpected_error():
    """
    予期せぬエラーが起きたときの対処
    エラーメッセージ全文と発生時刻をウェブフックで通知"""

    now = datetime.datetime.now().strftime("%H:%M")
    error_msg = f"```\n{traceback.format_exc()}```"
    main_content = {
        "username": "ERROR",
        "avatar_url": "https://cdn.discordapp.com/attachments/644880761081561111/703088291066675261/warning.png",
        "content": "<@523303776120209408>",
        "embeds": [
            {
                "title": "エラーが発生しました",
                "description": error_msg,
                "color": 0xff0000,
                "footer": {
                    "text": now
                }
            }
        ]
    }
    error_notice_webhook_url = os.getenv("error_notice_webhook")
    requests.post(error_notice_webhook_url, json.dumps(main_content), headers={'Content-Type': 'application/json'}) #エラーメッセをウェブフックに投稿


def login():
    """
    プログラム起動時の処理"""

    login_webhook_url = "WEBHOOKURL"
    main_content = {
            "username": "グラフbot",
            "avatar_url": "https://cdn.discordapp.com/attachments/644880761081561111/771962392027463710/icon_break.png",
            "content": "グラフbot(整地)(建築)が起動しました"
        }
    requests.post(login_webhook_url, main_content) #ログインメッセをウェブフックに投稿


def draw_graph(
    today,
    player_data_from1_to20_dict,
    player_data_from21_to40_dict,
    player_data_build_from1_to20_dict,
    player_data_build_from21_to40_dict):
    """
    グラフ描画
    本プログラムの中で一番の見どころ"""

    try:
        #整地
        for mcid in player_data_from1_to20_dict:
            max_data = player_data_from1_to20_dict[mcid]["23_58"]
            break

        px = 320 #pxの最小値は320
        #最大整地量に応じた規定の大きさになるまで拡大
        while True:
            if (max_data/50000) <= px:
                break
            else:
                px += 100
        px += 50

        hour_place = 50
        background = Image.new(mode="RGB", size=(1550, px), color=0x000000)
        background_instance = ImageDraw.Draw(background)
        font = ImageFont.truetype(r"./UDDigiKyokashoN-R.ttc",size=16)

        #横軸(時間)を書く
        for h in range(24):
            background_instance.text((hour_place, px-30), text=f"{h}時", font=font, fill=0xffffff)
            hour_place += 50
        background_instance.text((hour_place, px-30), text="最終", font=font, fill=0xffffff)

        #画像範囲内に目盛り線を引く
        i = 0
        while True:
            background_instance.line((60, px-35-i, 1250, px-35-i), fill=0xaaaaaa, width=1)
            background_instance.text((10, px-35-i-8), text=f"{i*5}万", font=font, fill=0xffffff)
            i += 100
            if i > px:
                break

        #順位ごとに違う色付け
        color_list = [
            0x00d2f4, #金
            0xaaaaaa, #銀(灰)
            0x3c65bc, #銅
            0x9999ff, #白強めの赤
            0xff9999, #白強めの青
            0x99ff99, #白強めの黄緑
            0x99ffff, #白強めの黄
            0xffff99, #白強めの水
            0xff99ff, #白強めの紫(ピンク)
            0x99ccff, #白強めの橙
            0xff99cc, #白強めの紫
            0xccff99, #何色だよコレ、私にだけ通じる言い方をすれば白の強いねりけし色
            0x99ffcc, #これまた表現のしようがない
            0xffcc99, #水色みたいな色
            0xcc99ff, #ピンク
            0x00ff00, #黄緑
            0x0000ff, #赤
            0x00ffff, #黄
            0xffff00, #水
            0xff00ff #ショッキングピンク
        ]

        i = 0
        mcid_wide = math.floor(px/20)
        mcid_place = math.floor(mcid_wide/2) - 8
        mcid_break_place_list = [] #最終点とMCIDを紐づけするのに使うのでその準備
        color_index = 0
        for mcid in player_data_from1_to20_dict:
            #右側にMCIDと最終整地量を入力
            break_amount = player_data_from1_to20_dict[mcid]["23_58"] #最終整地量を取得
            break_amount = "{:,}".format(break_amount)
            background_instance.text((1340, mcid_place), text=f"{mcid}: {break_amount}", fill=color_list[color_index], font=font) #1位から順に右上から等間隔にMCIDと最終整地量を入力
            mcid_break_place_list.append(mcid_place+8)

            #時間毎の点を入力
            point_x = 50 + 10
            xy_list = [] #線を引くときに使うのでその準備
            for hour in range(25):
                if hour == 24:
                    hour = "23_58"
                try:
                    raw_data = player_data_from1_to20_dict[mcid][f"{hour}"] #時間毎の整地量を取得
                except KeyError:
                    raw_data = 0
                point_y = math.floor(raw_data/50000) #座標を決定
                xy = (point_x, px-35-point_y) #線を引くときに使うのでその準備
                xy_list.append(xy) #線を引くときに使うのでその準備
                background_instance.ellipse((point_x-3, px-35-point_y-3, point_x+3, px-35-point_y+3), fill=color_list[color_index]) #点を打つ
                point_x += 50

            xy_list.append((1340, mcid_place+8))

            #点と点を結ぶ線を引く
            for i in range(25):
                width = 4
                if i == 24:
                    width = 2
                x_before, y_before = xy_list[i]
                x_after, y_after = xy_list[i+1]
                background_instance.line(
                    (x_before, y_before, x_after, y_after),
                    fill=color_list[color_index],
                    width=width
                )

            mcid_place += mcid_wide
            color_index += 1

        background.save(f"{today}_seichi_1-20.png") #本日のグラフとしてpng形式で保存

        for mcid in player_data_from21_to40_dict:
            max_data = player_data_from21_to40_dict[mcid]["23_58"]
            break

        px = 320 #pxの最小値は320
        #最大整地量に応じた規定の大きさになるまで拡大
        while True:
            if (max_data/5000) <= px:
                break
            else:
                px += 100
        px += 50

        hour_place = 50
        background = Image.new(mode="RGB", size=(1550, px), color=0x000000)
        background_instance = ImageDraw.Draw(background)
        font = ImageFont.truetype(r"./UDDigiKyokashoN-R.ttc",size=16)

        #横軸(時間)を書く
        for h in range(24):
            background_instance.text((hour_place, px-30), text=f"{h}時", font=font, fill=0xffffff)
            hour_place += 50
        background_instance.text((hour_place, px-30), text="最終", font=font, fill=0xffffff)

        #画像範囲内に目盛り線を引く
        i = 0
        while True:
            background_instance.line((60, px-35-i, 1250, px-35-i), fill=0xaaaaaa, width=1)
            background_instance.text((10, px-35-i-8), text=f"{math.floor(i*0.5)}万", font=font, fill=0xffffff)
            i += 100
            if i > px:
                break

        #順位ごとに違う色付け
        color_list = [
            0x9999ff, #白強めの赤
            0xff9999, #白強めの青
            0x99ff99, #白強めの黄緑
            0x99ffff, #白強めの黄
            0xffff99, #白強めの水
            0xff99ff, #白強めの紫(ピンク)
            0x99ccff, #白強めの橙
            0xff99cc, #白強めの紫
            0xccff99, #何色だよコレ、私にだけ通じる言い方をすればねりけし色
            0x99ffcc, #これまた表現のしようがない
            0xffcc99, #水色みたいな色
            0xcc99ff, #ピンク
            0x00ff00, #黄緑
            0x0000ff, #赤
            0x00ffff, #黄
            0xffff00, #水
            0xff00ff, #ショッキングピンク
            0x3299ff, #橙
            0x99ff32, #私にだけ通じる言い方をすればねりけし色
            0xff3299 #紫(見づらいかも)
        ]

        i = 0
        mcid_wide = math.floor(px/20)
        mcid_place = math.floor(mcid_wide/2) - 8
        mcid_break_place_list = [] #最終点とMCIDを紐づけするのに使うのでその準備
        color_index = 0
        for mcid in player_data_from21_to40_dict:
            #右側にMCIDと最終整地量を入力
            break_amount = player_data_from21_to40_dict[mcid]["23_58"] #最終整地量を取得
            break_amount = "{:,}".format(break_amount)
            background_instance.text((1340, mcid_place), text=f"{mcid}: {break_amount}", fill=color_list[color_index], font=font) #1位から順に右上から等間隔にMCIDと最終整地量を入力
            mcid_break_place_list.append(mcid_place+8)

            #時間毎の点を入力
            point_x = 50 + 10
            xy_list = [] #線を引くときに使うのでその準備
            for hour in range(25):
                if hour == 24:
                    hour = "23_58"
                try:
                    raw_data = player_data_from21_to40_dict[mcid][f"{hour}"] #時間毎の整地量を取得 #時間毎の整地量を取得
                except KeyError:
                    raw_data = 0
                point_y = math.floor(raw_data/5000) #座標を決定
                xy = (point_x, px-35-point_y) #線を引くときに使うのでその準備
                xy_list.append(xy) #線を引くときに使うのでその準備
                background_instance.ellipse((point_x-3, px-35-point_y-3, point_x+3, px-35-point_y+3), fill=color_list[color_index]) #点を打つ
                point_x += 50

            xy_list.append((1340, mcid_place+8))

            #点と点を結ぶ線を引く
            for i in range(25):
                width = 4
                if i == 24:
                    width = 2
                x_before, y_before = xy_list[i]
                x_after, y_after = xy_list[i+1]
                background_instance.line(
                    (x_before, y_before, x_after, y_after),
                    fill=color_list[color_index],
                    width=width
                )

            mcid_place += mcid_wide
            color_index += 1

        background.save(f"{today}_seichi_21-40.png") #本日のグラフとしてpng形式で保存

        #建築
        for mcid in player_data_build_from1_to20_dict:
            max_data = player_data_build_from1_to20_dict[mcid]["23_58"]
            break

        px = 320 #pxの最小値は320
        #最大整地量に応じた規定の大きさになるまで拡大
        while True:
            if (max_data/500) <= px:
                break
            else:
                px += 100
        px += 50

        hour_place = 50
        background = Image.new(mode="RGB", size=(1550, px), color=0x000000)
        background_instance = ImageDraw.Draw(background)
        font = ImageFont.truetype(r"./UDDigiKyokashoN-R.ttc",size=16)

        #横軸(時間)を書く
        for h in range(24):
            background_instance.text((hour_place, px-30), text=f"{h}時", font=font, fill=0xffffff)
            hour_place += 50
        background_instance.text((hour_place, px-30), text="最終", font=font, fill=0xffffff)

        #画像範囲内に目盛り線を引く
        i = 0
        while True:
            background_instance.line((60, px-35-i, 1250, px-35-i), fill=0xaaaaaa, width=1)
            background_instance.text((10, px-35-i-8), text=f"{math.floor(i*0.05)}千", font=font, fill=0xffffff)
            i += 100
            if i > px:
                break

        #順位ごとに違う色付け
        color_list = [
            0x00d2f4, #金
            0xaaaaaa, #銀(灰)
            0x3c65bc, #銅
            0x9999ff, #白強めの赤
            0xff9999, #白強めの青
            0x99ff99, #白強めの黄緑
            0x99ffff, #白強めの黄
            0xffff99, #白強めの水
            0xff99ff, #白強めの紫(ピンク)
            0x99ccff, #白強めの橙
            0xff99cc, #白強めの紫
            0xccff99, #何色だよコレ、私にだけ通じる言い方をすれば白の強いねりけし色
            0x99ffcc, #これまた表現のしようがない
            0xffcc99, #水色みたいな色
            0xcc99ff, #ピンク
            0x00ff00, #黄緑
            0x0000ff, #赤
            0x00ffff, #黄
            0xffff00, #水
            0xff00ff #ショッキングピンク
        ]

        i = 0
        mcid_wide = math.floor(px/20)
        mcid_place = math.floor(mcid_wide/2) - 8
        mcid_break_place_list = [] #最終点とMCIDを紐づけするのに使うのでその準備
        color_index = 0
        for mcid in player_data_build_from1_to20_dict:
            #右側にMCIDと最終整地量を入力
            break_amount = player_data_build_from1_to20_dict[mcid]["23_58"] #最終整地量を取得
            break_amount = "{:,}".format(break_amount)
            background_instance.text((1340, mcid_place), text=f"{mcid}: {break_amount}", fill=color_list[color_index], font=font) #1位から順に右上から等間隔にMCIDと最終整地量を入力
            mcid_break_place_list.append(mcid_place+8)

            #時間毎の点を入力
            point_x = 50 + 10
            xy_list = [] #線を引くときに使うのでその準備
            for hour in range(25):
                if hour == 24:
                    hour = "23_58"
                try:
                    raw_data = player_data_build_from1_to20_dict[mcid][f"{hour}"] #時間毎の整地量を取得
                except KeyError:
                    raw_data = 0
                point_y = math.floor(raw_data/50) #座標を決定
                xy = (point_x, px-35-point_y) #線を引くときに使うのでその準備
                xy_list.append(xy) #線を引くときに使うのでその準備
                background_instance.ellipse((point_x-3, px-35-point_y-3, point_x+3, px-35-point_y+3), fill=color_list[color_index]) #点を打つ
                point_x += 50

            xy_list.append((1340, mcid_place+8))

            #点と点を結ぶ線を引く
            for i in range(25):
                width = 4
                if i == 24:
                    width = 2
                x_before, y_before = xy_list[i]
                x_after, y_after = xy_list[i+1]
                background_instance.line(
                    (x_before, y_before, x_after, y_after),
                    fill=color_list[color_index],
                    width=width
                )

            mcid_place += mcid_wide
            color_index += 1

        background.save(f"{today}_build_1-20.png") #本日のグラフとしてpng形式で保存

        for mcid in player_data_build_from21_to40_dict:
            max_data = player_data_build_from21_to40_dict[mcid]["23_58"]
            break

        px = 320 #pxの最小値は320
        #最大整地量に応じた規定の大きさになるまで拡大
        while True:
            if (max_data/50) <= px:
                break
            else:
                px += 100
        px += 50

        hour_place = 50
        background = Image.new(mode="RGB", size=(1550, px), color=0x000000)
        background_instance = ImageDraw.Draw(background)
        font = ImageFont.truetype(r"./UDDigiKyokashoN-R.ttc",size=16)

        #横軸(時間)を書く
        for h in range(24):
            background_instance.text((hour_place, px-30), text=f"{h}時", font=font, fill=0xffffff)
            hour_place += 50
        background_instance.text((hour_place, px-30), text="最終", font=font, fill=0xffffff)

        #画像範囲内に目盛り線を引く
        i = 0
        while True:
            background_instance.line((60, px-35-i, 1250, px-35-i), fill=0xaaaaaa, width=1)
            background_instance.text((10, px-35-i-8), text=f"{i*5}", font=font, fill=0xffffff)
            i += 100
            if i > px:
                break

        #順位ごとに違う色付け
        color_list = [
            0x9999ff, #白強めの赤
            0xff9999, #白強めの青
            0x99ff99, #白強めの黄緑
            0x99ffff, #白強めの黄
            0xffff99, #白強めの水
            0xff99ff, #白強めの紫(ピンク)
            0x99ccff, #白強めの橙
            0xff99cc, #白強めの紫
            0xccff99, #何色だよコレ、私にだけ通じる言い方をすればねりけし色
            0x99ffcc, #これまた表現のしようがない
            0xffcc99, #水色みたいな色
            0xcc99ff, #ピンク
            0x00ff00, #黄緑
            0x0000ff, #赤
            0x00ffff, #黄
            0xffff00, #水
            0xff00ff, #ショッキングピンク
            0x3299ff, #橙
            0x99ff32, #私にだけ通じる言い方をすればねりけし色
            0xff3299 #紫(見づらいかも)
        ]

        i = 0
        mcid_wide = math.floor(px/20)
        mcid_place = math.floor(mcid_wide/2) - 8
        mcid_break_place_list = [] #最終点とMCIDを紐づけするのに使うのでその準備
        color_index = 0
        for mcid in player_data_build_from21_to40_dict:
            #右側にMCIDと最終整地量を入力
            break_amount = player_data_build_from21_to40_dict[mcid]["23_58"] #最終整地量を取得
            break_amount = "{:,}".format(break_amount)
            background_instance.text((1340, mcid_place), text=f"{mcid}: {break_amount}", fill=color_list[color_index], font=font) #1位から順に右上から等間隔にMCIDと最終整地量を入力
            mcid_break_place_list.append(mcid_place+8)

            #時間毎の点を入力
            point_x = 50 + 10
            xy_list = [] #線を引くときに使うのでその準備
            for hour in range(25):
                if hour == 24:
                    hour = "23_58"
                try:
                    raw_data = player_data_build_from21_to40_dict[mcid][f"{hour}"] #時間毎の整地量を取得 #時間毎の整地量を取得
                except KeyError:
                    raw_data = 0
                point_y = math.floor(raw_data/5) #座標を決定
                xy = (point_x, px-35-point_y) #線を引くときに使うのでその準備
                xy_list.append(xy) #線を引くときに使うのでその準備
                background_instance.ellipse((point_x-3, px-35-point_y-3, point_x+3, px-35-point_y+3), fill=color_list[color_index]) #点を打つ
                point_x += 50

            xy_list.append((1340, mcid_place+8))

            #点と点を結ぶ線を引く
            for i in range(25):
                width = 4
                if i == 24:
                    width = 2
                x_before, y_before = xy_list[i]
                x_after, y_after = xy_list[i+1]
                background_instance.line(
                    (x_before, y_before, x_after, y_after),
                    fill=color_list[color_index],
                    width=width
                )

            mcid_place += mcid_wide
            color_index += 1

        background.save(f"{today}_build_21-40.png") #本日のグラフとしてpng形式で保存

    except:
        unexpected_error()


def push_to_discord(today):
    """
    ファイルをdiscordに送信"""

    try:
        #整地
        f0 = open(f"player_data{today}.json", mode="r", encoding="utf-8")
        f1 = open(f"{today}_seichi_1-20.png", mode="rb")
        f2 = open(f"{today}_seichi_21-40.png", mode="rb")
        files = { #指定したファイル達
            "file0": f0,
            "file1": f1,
            "file2": f2
        }
        break_webhook_url = "WEBHOOKURL"
        requests.post(break_webhook_url, files=files)

        f0.close()
        f1.close()
        f2.close()

        #建築
        f1 = open(f"{today}_build_1-20.png", mode="rb")
        f2 = open(f"{today}_build_21-40.png", mode="rb")
        files = { #指定したファイル達
            "file1": f1,
            "file2": f2
        }
        build_webhook_url = "WEBHOOKURL"
        requests.post(build_webhook_url, files=files)

        f1.close()
        f2.close()

    except:
        unexpected_error()


def push_to_twitter(today):
    """
    整地量の1~20のグラフ画像をtwitterに送信"""

    try:
        with open(f"{today}_seichi_1-20.png", mode="rb") as image:
            image = image.read()

        consumer_key = os.getenv("consumer_key")
        consumer_secret = os.getenv("consumer_secret")
        twitter_token = os.getenv("twitter_token")
        token_secret = os.getenv("token_secret")

        auth = twitter.OAuth(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            token=twitter_token,
            token_secret=token_secret
        )

        t = twitter.Twitter(auth=auth)

        pic_upload = twitter.Twitter(domain="upload.twitter.com", auth=auth)
        id_img1 = pic_upload.media.upload(media=image)["media_id_string"]
        t.statuses.update(status=f"@tos\n# 整地鯖\nこれはデバッグです\n{today}", media_ids=",".join([id_img1]))

    except:
        unexpected_error()


def down_server(today):
    """
    23:58にサーバがダウンしていてランキングが取得できなかった場合"""

    try:
        #整地
        f0 = open(f"player_data{today}.json", mode="r", encoding="utf-8")
        files = { #指定したファイル達
            "file0": f0
        }
        break_webhook_url = "WEBHOOKURL"
        requests.post(break_webhook_url, files=files)

        f0.close()

        #建築
        content = {
            "content": f"データなし"
        }
        build_webhook_url = "WEBHOOKURL"
        requests.post(build_webhook_url, files=files)

        #Twitter
        consumer_key = os.getenv("consumer_key")
        consumer_secret = os.getenv("consumer_secret")
        twitter_token = os.getenv("twitter_token")
        token_secret = os.getenv("token_secret")

        auth = twitter.OAuth(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            token=twitter_token,
            token_secret=token_secret
        )

        t = twitter.Twitter(auth=auth)

        t.statuses.update(status=f"{today}\nデータなし")

    except:
        unexpected_error()


def neta(today):
    """
    完全なるネタ機能
    飽きたらやめる"""

    try:
        sukiyaki = "https://ranking-gigantic.seichi.click/api/ranking/player/9e78b64a-900f-4f6f-83d6-1e4a9de690ed?types=break"
        leveling = "https://ranking-gigantic.seichi.click/api/ranking/player/a1965397-bf44-4368-8330-d2f1dbc6de17?types=break"

        try:
            res1 = requests.get(sukiyaki)
            res2 = requests.get(leveling)
            sukiyaki = res1.json()
            leveling = res2.json()
        except requests.exceptions.HTTPError:
            return

        sukiyaki_break = int(sukiyaki[0]["data"]["raw_data"])
        leveling_break = int(leveling[0]["data"]["raw_data"])

        nokori = "{:,}".format(leveling_break - sukiyaki_break)

        today = datetime.date.today().strftime(r"%Y%m%d")
        with open(f"player_data{today}.json", mode="r", encoding="utf-8") as f:
            player_data = json.load(f)

        try:
            today_break = player_data["SUKIYAKI_da1210"]["23_58"]
        except KeyError:
            today_break = 0

        today_break = "{:,}".format(today_break)

        consumer_key = os.getenv("consumer_key")
        consumer_secret = os.getenv("consumer_secret")
        twitter_token = os.getenv("twitter_token")
        token_secret = os.getenv("token_secret")

        auth = twitter.OAuth(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            token=twitter_token,
            token_secret=token_secret
        )

        t = twitter.Twitter(auth=auth)

        t.statuses.update(status=f"@tos\nS君の本日の整地量: {today_break}\nLさんとの差: {nokori}")

    except:
        unexpected_error()



def do_every_hour():
    try:
        today = datetime.date.today().strftime(r"%Y%m%d")
        hour = datetime.datetime.now().hour
        #整地
        try:
            with open(f"player_data{today}.json", mode="r", encoding="utf-8") as f:
                player_data_dict = json.load(f)
        except FileNotFoundError:
            player_data_dict = {}

        i = 0
        while True:
            try:
                url = f"https://ranking-gigantic.seichi.click/api/ranking?type=break&offset={i*100}&lim=100&duration=daily"
                res = requests.get(url)
                player_data_every_hour_dict = res.json()
                player_data_every_hour_list = player_data_every_hour_dict["ranks"]

            except:
                for mcid in player_data_dict.keys(): 
                    player_data = player_data_dict[mcid]
                    player_data[f"{hour}"] = player_data[f"{hour-1}"] #1時間前と同じものを記録する
                break

            for player_data_every_hour in player_data_every_hour_list:
                mcid = player_data_every_hour["player"]["name"] #リストからMCIDを取得
                raw_data = int(player_data_every_hour["data"]["raw_data"]) #リストから整地量を取得
                try:
                    player_data = player_data_dict[mcid] #player_dataはdict型
                except KeyError:
                    player_data_dict[mcid] = {}
                    player_data = player_data_dict[mcid]
                player_data[f"{hour}"] = raw_data

            if player_data_every_hour_dict["result_count"] == 100:
                i += 1
            else:
                break

        player_data_json = json.dumps(player_data_dict, indent=4)
        with open(f"player_data{today}.json", mode="w", encoding="utf-8") as f:
            f.write(player_data_json)

        #建築
        try:
            with open(f"player_data_build{today}.json", mode="r", encoding="utf-8") as f:
                player_data_dict = json.load(f)
        except FileNotFoundError:
            player_data_dict = {}

        i = 0
        while True:
            try:
                url = f"https://ranking-gigantic.seichi.click/api/ranking?type=break&offset={i*100}&lim=100&duration=daily"
                res = requests.get(url)
                player_data_every_hour_dict = res.json()
                player_data_every_hour_list = player_data_every_hour_dict["ranks"]

            except:
                for mcid in player_data_dict.keys(): 
                    player_data = player_data_dict[mcid]
                    player_data[f"{hour}"] = player_data[f"{hour-1}"] #1時間前と同じものを記録する
                break

            for player_data_every_hour in player_data_every_hour_list:
                mcid = player_data_every_hour["player"]["name"] #リストからMCIDを取得
                raw_data = int(player_data_every_hour["data"]["raw_data"]) #リストから整地量を取得
                try:
                    player_data = player_data_dict[mcid] #player_dataはdict型
                except KeyError:
                    player_data_dict[mcid] = {}
                    player_data = player_data_dict[mcid]
                player_data[f"{hour}"] = raw_data

            if player_data_every_hour_dict["result_count"] == 100:
                i += 1
            else:
                break

        player_data_json = json.dumps(player_data_dict, indent=4)
        with open(f"player_data_build{today}.json", mode="w", encoding="utf-8") as f:
            f.write(player_data_json)

    except:
        unexpected_error() #こちらでは考えつかないエラーが起きたときunexpected_error()に回す。


def do_every_day():
    try:
        today = datetime.date.today().strftime(r"%Y%m%d")
        hour = "23_58"
        #整地
        try:
            with open(f"player_data{today}.json", mode="r", encoding="utf-8") as f:
                player_data_dict = json.load(f)
        except FileNotFoundError:
            player_data_dict = {}

        i = 0
        while True:
            try:
                url = f"https://ranking-gigantic.seichi.click/api/ranking?type=break&offset={i*100}&lim=100&duration=daily"
                res = requests.get(url)
                player_data_every_hour_dict = res.json()
                player_data_every_hour_list = player_data_every_hour_dict["ranks"]

            except:
                for mcid in player_data_dict.keys(): 
                    player_data = player_data_dict[mcid]
                    player_data[hour] = player_data["23"] #1時間前と同じものを記録する
                break

            for player_data_every_hour in player_data_every_hour_list:
                mcid = player_data_every_hour["player"]["name"] #リストからMCIDを取得
                raw_data = int(player_data_every_hour["data"]["raw_data"]) #リストから整地量を取得
                try:
                    player_data = player_data_dict[mcid] #player_dataはdict型
                except KeyError:
                    player_data_dict[mcid] = {}
                    player_data = player_data_dict[mcid]
                player_data[hour] = raw_data

            if player_data_every_hour_dict["result_count"] == 100:
                i += 1
            else:
                break

        player_data_json = json.dumps(player_data_dict, indent=4)
        with open(f"player_data{today}.json", mode="w", encoding="utf-8") as f:
            f.write(player_data_json)

        #建築
        try:
            with open(f"player_data_build{today}.json", mode="r", encoding="utf-8") as f:
                player_data_dict = json.load(f)
        except FileNotFoundError:
            player_data_dict = {}

        i = 0
        while True:
            try:
                url = f"https://ranking-gigantic.seichi.click/api/ranking?type=build&offset={i*100}&lim=100&duration=daily"
                res = requests.get(url)
                player_data_every_hour_dict = res.json()
                player_data_every_hour_list = player_data_every_hour_dict["ranks"]

            except:
                for mcid in player_data_dict.keys(): 
                    player_data = player_data_dict[mcid]
                    player_data[hour] = player_data["23"] #1時間前と同じものを記録する
                break

            for player_data_every_hour in player_data_every_hour_list:
                mcid = player_data_every_hour["player"]["name"] #リストからMCIDを取得
                raw_data = int(player_data_every_hour["data"]["raw_data"]) #リストから整地量を取得
                try:
                    player_data = player_data_dict[mcid] #player_dataはdict型
                except KeyError:
                    player_data_dict[mcid] = {}
                    player_data = player_data_dict[mcid]
                player_data[hour] = raw_data

            if player_data_every_hour_dict["result_count"] == 100:
                i += 1
            else:
                break

        player_data_json = json.dumps(player_data_dict, indent=4)
        with open(f"player_data_build{today}.json", mode="w", encoding="utf-8") as f:
            f.write(player_data_json)

        #----ここまで記録 ほぼdo_every_hour()と同じ----

        #整地
        try:
            url = f"https://ranking-gigantic.seichi.click/api/ranking?type=break&offset=0&lim=40&duration=daily"
            res = requests.get(url)
            player_data_every_day_dict = res.json()
            player_data_every_day_list = player_data_every_day_dict["ranks"]

        except: #23:58にサイトが落ちてたら？
            down_server(today)
            return

        with open(f"player_data{today}.json", mode="r", encoding="utf-8") as f:
            player_data_dict = json.load(f)

        player_data_from1_to20_dict = {}
        player_data_from21_to40_dict = {}
        i = 0
        for player_data_every_day in player_data_every_day_list: #len(List) <= 40
            mcid = player_data_every_day["player"]["name"]
            if i <= 19:
                player_data_from1_to20_dict[mcid] = player_data_dict[mcid]
            elif i <= 38:
                player_data_from21_to40_dict[mcid] = player_data_dict[mcid]
            else:
                break
            i += 1

        #建築
        try:
            url = f"https://ranking-gigantic.seichi.click/api/ranking?type=build&offset=0&lim=40&duration=daily"
            res = requests.get(url)
            player_data_every_day_dict = res.json()
            player_data_every_day_list = player_data_every_day_dict["ranks"]

        except: #23:58にサイトが落ちてたら？
            down_server(today)
            return

        with open(f"player_data_build{today}.json", mode="r", encoding="utf-8") as f:
            player_data_dict = json.load(f)

        player_data_build_from1_to20_dict = {}
        player_data_build_from21_to40_dict = {}

        i = 0
        for player_data_every_day in player_data_every_day_list: #len(List) <= 40
            mcid = player_data_every_day["player"]["name"]
            if i <= 19:
                player_data_build_from1_to20_dict[mcid] = player_data_dict[mcid]
            elif i <= 38:
                player_data_build_from21_to40_dict[mcid] = player_data_dict[mcid]
            else:
                break
            i += 1

        draw_graph(
            today,
            player_data_from1_to20_dict,
            player_data_from21_to40_dict,
            player_data_build_from1_to20_dict,
            player_data_build_from21_to40_dict
            )

        push_to_discord(today)
        push_to_twitter(today)

        #完全なるネタ機能、飽きたらやめる
        neta(today)

    except:
        unexpected_error() #こちらでは考えつかないエラーが起きたときunexpected_error()に回す。

login() #login()を実行。プログラム起動時に実行される。
schedule.every().hour.at(":01").do(do_every_hour) #do_every_hour()を毎時1分に実行
schedule.every().day.at("23:58").do(do_every_day) #do_every_every()を毎日23:58に実行

#ちょっとは動作軽くしたいじゃん？一秒間に何回も確認してたら重くなるやん？ってことで1秒休み
while True:
    schedule.run_pending()
    time.sleep(1)