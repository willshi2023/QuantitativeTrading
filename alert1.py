import pygame
import datetime

# 播放铃声
# 铃声只有早上11点到晚上11点才饷
def play_remind():
    # 获取当前时间
    current_time = datetime.datetime.now()
    current_hour = current_time.hour

    # 仅在11点到23点之间播放铃声
    if 11 <= current_hour < 23:
        play_alert_core("new_message.mp3")
    else:
        print("当前时间不在播放铃声的时间范围内。")
# 播放失败提示音
def play_error():
    play_alert_core("error.mp3")
# 播放铃声
def play_alert_core(file):
    pygame.mixer.init()
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()

    # 等待音频播放完成
    while pygame.mixer.music.get_busy():
        continue
if __name__ == '__main__':
    # 播放提示音
    play_error()