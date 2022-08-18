# Сервис для покупки и продажи акций
Проект реализован с использованием фреймворка Flask.

:heavy_dollar_sign:Веб-приложение, позволяющее пользователям покупать и продавать акции. Пользователи могут регистрироваться на сайте и пополнять свой портфель.

На сервисе предусмотрена аутентификация пользователей:
![Вход пользователя](finance/demonstration/Registration.gif)

Возможность просматривать цены акций:
![Просмотр цен акций](finance/demonstration/Viewing_shares.gif)

Возможность покупать акции:
![Покупка акций](finance/demonstration/Purchase_of_shares.gif)

Возможность продавать акции:
![Покупка акций](finance/demonstration/Sale_of_shares.gif)


Логины и пароли пользователей хранятся в базе данных SQLite.

Вы можете запустить этот проект локально, выполнив следующие действия:

- Скопируйте данный репозиторий командой `git clone https://github.com/RomanMRR/finance.git`
- `cd finance/finance`
- `export API_KEY=your_key` (Ключ API можно получить на  [сайте](https://iexcloud.io/cloud-login#/register/))
- `flask run`


