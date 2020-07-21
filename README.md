整地鯖の日間整地量ランキング上位二十人の時間毎の整地量をまとめてグラフ化するコード  
恥ずかしいからプログラミングガチ勢の人は見ないで><  
**完全なコピペ禁止！**  
参考にするのはいいよ  
参考にして何か不具合が発生しても私責任取りません  

# 動きの概要  
毎時01分に全プレイヤーの整地量を取得->player_data.jsonに記録  
23:58に全プレイヤーの整地量を取得->player_data.jsonに記録  
再度ランキングページにアクセスし、上位20人の整地量を取得->{today}.jsonに記録  
{today}.jsonをもとにグラフとエクセルを作成、player_data.jsonをコピーし、player_data{today}.jsonとして保存  
webhookを使用し、グラフ、エクセル、{today}.json、player_data{today}.jsonをdiscordに送信  
グラフをtwitterに投稿