# mokumoku-bot

## 1. プロジェクト概要

もくもく会の開始・終了をアナウンスする際のDiscord Bot

主な技術構成：

- Python 3.13.11
- uv (パッケージ管理)
- docker
- koyeb

## 2. CI/CD

mainブランチにプッシュしたら、koyeb側でデプロイ作業をしてあげる必要があります。

### 手動デプロイ（koyeb CLI）

`main` へ push せずにデプロイだけ走らせたい時の手順。事前に koyeb CLI のインストールとログインが必要。

```sh
# 初回のみ：CLI のインストール（例：brew）
brew install koyeb

# 初回のみ：ログイン（API トークンを聞かれる）
koyeb login
```

デプロイの実行：

```sh
# サービス ID を確認
koyeb services list

# リデプロイ（<service-id> は上記で確認した ID）
koyeb services redeploy <service-id>

# 進捗確認
koyeb deployments list

# ログ確認（ビルド / ランタイム）
koyeb deployment logs <deployment-id> -t build
koyeb deployment logs <deployment-id>
```

## 3. 開発手順

パッケージ管理にuvを利用しています。

以下のコマンドでインストールしてください。

```sh
mise use -g uv
```

最初にライブラリの同期を行います。

```sh
uv sync
```

OKです！

あとは任意のエディターで開発しましょう。

プロジェクトを起動する際は以下のコマンドで起動可能です。

```sh
uv run serve
```

デバッグは`src/mokumoku_bot/__init__.py`をエントリーポイントにして実行すれば可能です。
