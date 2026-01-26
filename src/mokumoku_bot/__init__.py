import sys
import threading
from mokumoku_bot.discord_bot import TOKEN, client
from streamlit.web import cli as stcli


def main():
    # Discord Botを別スレッドで起動
    print("Starting Discord Bot...")
    threading.Thread(target=client.run, args=(TOKEN,), daemon=True).start()

    # Streamlitをメインスレッドで起動
    print("Starting Streamlit UI...")
    # 実行するファイルとしてstreamlit_app.pyを指定
    sys.argv = [
        "streamlit",
        "run",
        "src/mokumoku_bot/streamlit_app.py",
        "--server.port",
        "8000",
        "--server.address",
        "0.0.0.0",
    ]
    stcli.main()


if __name__ == "__main__":
    main()
