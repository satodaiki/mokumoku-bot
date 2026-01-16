# mokumoku-bot

## 1. プロジェクト概要

もくもく会の開始・終了をアナウンスする際のDiscord Bot

主な技術構成：

- Python 3.13.11
- uv (パッケージ管理)
- docker
- koyeb

## 3. CI/CD

mainブランチにプッシュされると、koyeb側でDockerfileで作成されたイメージがデプロイされます。
