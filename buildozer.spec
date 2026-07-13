[app]
title = Прыжкин Приключение
package.name = prygkin
package.domain = org.raulbros

source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,wav,ogg

version = 1.0

# pygame — единственная зависимость игры; buildozer сам соберёт под Android
requirements = python3,pygame

orientation = landscape
fullscreen = 1

icon.filename = %(source.dir)s/assets/icon.png

android.permissions = INTERNET

# Минимальная и целевая версия Android API
android.minapi = 24
android.api = 33
android.ndk_api = 24

android.archs = arm64-v8a, armeabi-v7a

log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
