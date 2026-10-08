# Vercel + Neon 배포

이 프로젝트는 로컬에서는 `db.sqlite3`를 사용하고, Vercel에서는 `DATABASE_URL`이 설정된 PostgreSQL만 사용합니다. Vercel 함수의 파일시스템은 영구 저장소가 아니므로 SQLite나 CSV로 운영하면 안 됩니다.

## 최초 설정

1. Vercel 프로젝트에서 **Marketplace → Neon → Install**을 선택하고 새 데이터베이스를 만듭니다.
2. Neon 리소스를 이 Vercel 프로젝트의 **Production** 환경에 연결합니다. 연결 시 `DATABASE_URL`이 자동으로 환경 변수에 추가됩니다.
3. Vercel 프로젝트의 **Settings → Environment Variables**에서 `DJANGO_SECRET_KEY`를 Production에 추가합니다. 충분히 긴 무작위 문자열을 사용합니다.
4. 커스텀 도메인을 연결했다면 `DJANGO_ALLOWED_HOSTS`에 그 도메인을 추가합니다. 예: `order.example.com`.
5. 이 변경을 기본 브랜치에 push합니다. 배포 중 `migrate`가 PostgreSQL 테이블을 만들고 `create_initial_data.py`가 기본 테이블·메뉴를 한 번만 생성합니다.

## 배포 확인

- Vercel Deployment 로그에서 `Applying ...`과 `초기 데이터 생성 완료!`을 확인합니다.
- 배포 URL을 열어 메뉴·테이블 목록이 보이는지 확인합니다.
- 주문 하나를 등록하고 새로고침한 뒤에도 남아 있으면 PostgreSQL 저장이 정상입니다.

## 주의사항

- Preview 배포도 같은 `DATABASE_URL`을 쓰면 migration이 실행됩니다. Preview별 격리가 필요하면 Neon의 브랜치 기능을 연결하거나 Preview에는 별도 DB를 지정하세요.
- QR 이미지 업로드는 Vercel에서 저장되지 않도록 기본 비활성화했습니다. 나중에 필요해지면 Vercel Blob/S3 같은 파일 저장소를 추가해야 합니다.
