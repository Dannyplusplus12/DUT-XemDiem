#!/usr/bin/env bash
set -e

if ! command -v railway >/dev/null 2>&1; then
  echo "Vui lòng cài Railway CLI trước: npm i -g @railway/cli"
  exit 1
fi

flutter pub get
flutter build web --release
railway up
echo "Deploy Flutter Web lên Railway hoàn tất"
