# MyWeb

## Docker + Nginx 배포

1. `.env` 파일을 준비합니다.
   - `ADMIN_HASH`: Argon2 해시 값
   - `SECRET_KEY`: 임의의 긴 문자열

2. 프로젝트 루트에서 실행:

```bash
docker compose up -d --build
```

3. 브라우저에서 NAS의 IP 주소로 접속:

```text
http://<NAS_IP>
```

- Flask 앱은 내부적으로 `flask_web:5000`으로 연결됩니다.
- Nginx가 80번 포트에서 외부 요청을 받아 프록시합니다.
- 필요하면 나중에 HTTPS를 붙일 때 `nginx` 설정에 TLS를 추가하면 됩니다.

