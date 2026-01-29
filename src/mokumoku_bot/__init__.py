import multiprocessing
import subprocess
import sys
import time

from mokumoku_bot.discord_bot import TOKEN, client


def run_bot():
    """Discord Botを起動する関数（別プロセスで実行）"""
    print("Starting Discord Bot...")
    client.run(TOKEN)


def run_streamlit():
    """Streamlitをサブプロセスとして起動する関数"""
    print("Starting Streamlit UI...")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "src/mokumoku_bot/streamlit_app.py",
        "--server.port",
        "8000",
        "--server.address",
        "0.0.0.0",
    ]
    subprocess.run(cmd)


def main():
    # 1. Botを別プロセスで開始
    bot_process = multiprocessing.Process(target=run_bot, daemon=True)
    bot_process.start()

    # Botのログイン時間を考慮して少し待機（任意）
    time.sleep(2)

    # 2. Streamlitをメインプロセスで開始（subprocess.runは終了までブロックする）
    try:
        run_streamlit()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        bot_process.terminate()


if __name__ == "__main__":
    # Windowsでmultiprocessingを使うために必須
    multiprocessing.freeze_support()
    main()
