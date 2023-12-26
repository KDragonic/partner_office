from django.conf import settings
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build

flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    settings.CLIENT_SECRET_FILE,
    scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],
    redirect_uri="https://turgorodok.ru/google/auth/"
    )

# print(settings.CLIENT_SECRET_FILE)


def create_authorization_url(state):
    # Используйте файл client_secret.json для идентификации приложения, запрашивающего авторизацию.
    # Требуются идентификатор клиента (из этого файла) и области доступа.

    # Укажите, куда API-сервер перенаправит пользователя после завершения пользователя
    # процесс авторизации. Требуется перенаправление URI. Значение должно точно
    # соответствовать одному из авторизованных URI перенаправления для клиента OAuth 2.0, который вы
    # настроили в консоли API. Если это значение не соответствует авторизованному URI,
    # вы получите ошибку 'redirect_uri_mismatch'.
    flow.redirect_uri = "https://turgorodok.ru/google/auth/"

    # Генерировать URL для запроса к серверу OAuth 2.0 Google.
    # Используйте kwargs для установки необязательных параметров запроса.
    authorization_url, state = flow.authorization_url(
        # Включить инкрементальную авторизацию. Рекомендуется как лучшая практика.
        include_granted_scopes='true')

    return authorization_url


def token_to_user_info(code):
    flow.fetch_token(code=code)

    # Store the credentials in the session.
    # ACTION ITEM for developers:
    #     Store user's access and refresh tokens in your data store if
    #     incorporating this code into your real app.

    credentials = flow.credentials
    credentials_result = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return credentials, credentials_result


def get_userinfo(credentials):
    user_info = build('oauth2', 'v2', credentials=credentials)
    userinfo = user_info.userinfo().get().execute()
    return userinfo