# 식당 주문 시스템 기술 명세서

## 1. 시스템 아키텍처

### 1.1 전체 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   고객 모바일    │    │   직원 태블릿    │    │   관리자 PC     │
│   (QR 주문)     │    │  (테이블 관리)   │    │  (시스템 관리)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Django Server  │
                    │   (Backend)     │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Database      │
                    │ (SQLite/PostgreSQL) │
                    └─────────────────┘
```

### 1.2 기술 스택
- **Backend Framework**: Django 4.2+
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: SQLite (개발), PostgreSQL (운영)
- **Additional Libraries**:
  - qrcode: QR코드 생성
  - Pillow: 이미지 처리
  - django-cors-headers: CORS 처리
  - Chart.js: 매출 차트

## 2. 데이터베이스 설계

### 2.1 ERD (Entity Relationship Diagram)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Table     │    │    Order    │    │    Menu     │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (PK)     │    │ id (PK)     │    │ id (PK)     │
│ number      │◄───┤ table_id(FK)│    │ name        │
│ seats       │    │ created_at  │    │ price       │
│ status      │    │ status      │    │ description │
│ qr_code     │    │ total_amount│    │ is_active   │
└─────────────┘    │ discount    │    └─────────────┘
                   └─────────────┘           ▲
                          │                  │
                          ▼                  │
                   ┌─────────────┐          │
                   │ OrderItem   │          │
                   ├─────────────┤          │
                   │ id (PK)     │          │
                   │ order_id(FK)│          │
                   │ menu_id(FK) │──────────┘
                   │ quantity    │
                   │ options     │
                   │ unit_price  │
                   └─────────────┘
```

### 2.2 모델 정의

#### Table 모델
```python
class Table(models.Model):
    STATUS_CHOICES = [
        ('empty', '빈 테이블'),
        ('ordered', '주문 완료'),
        ('cooking', '조리 완료'),
        ('paid', '결제 완료'),
    ]
    
    number = models.IntegerField(unique=True)
    seats = models.IntegerField(default=4)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='empty')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Menu 모델
```python
class Menu(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    description = models.TextField(blank=True)
    options = models.JSONField(default=list)  # ['고추빼고', '면 많이']
    min_order = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
```

#### Order 모델
```python
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '주문 대기'),
        ('confirmed', '주문 확인'),
        ('cooking', '조리 중'),
        ('ready', '조리 완료'),
        ('served', '서빙 완료'),
        ('paid', '결제 완료'),
    ]
    
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    total_amount = models.IntegerField(default=0)
    discount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

## 3. API 설계

### 3.1 RESTful API 엔드포인트

#### 테이블 관리
- `GET /api/tables/` - 전체 테이블 목록
- `GET /api/tables/{id}/` - 특정 테이블 정보
- `PUT /api/tables/{id}/status/` - 테이블 상태 변경
- `GET /api/tables/{id}/qr/` - QR코드 생성/조회

#### 주문 관리
- `GET /api/orders/` - 전체 주문 목록
- `POST /api/orders/` - 새 주문 생성
- `GET /api/orders/{id}/` - 특정 주문 정보
- `PUT /api/orders/{id}/` - 주문 수정
- `DELETE /api/orders/{id}/` - 주문 취소

#### 메뉴 관리
- `GET /api/menus/` - 메뉴 목록
- `POST /api/menus/` - 메뉴 추가 (관리자)
- `PUT /api/menus/{id}/` - 메뉴 수정 (관리자)
- `DELETE /api/menus/{id}/` - 메뉴 삭제 (관리자)

### 3.2 실시간 통신
```javascript
// AJAX 폴링을 통한 실시간 업데이트
function updateTableStatus() {
    fetch('/api/tables/')
        .then(response => response.json())
        .then(data => {
            updateTableDisplay(data);
        });
}

setInterval(updateTableStatus, 2000); // 2초마다 업데이트
```

## 4. 보안 설계

### 4.1 인증 및 권한
- Django 기본 인증 시스템 사용
- 세션 기반 인증
- 관리자/직원 권한 분리

### 4.2 데이터 보안
- CSRF 토큰 사용
- SQL Injection 방지 (Django ORM)
- XSS 방지 (템플릿 이스케이핑)

## 5. 성능 최적화

### 5.1 데이터베이스 최적화
- 인덱스 설정
- 쿼리 최적화 (select_related, prefetch_related)
- 페이지네이션 적용

### 5.2 프론트엔드 최적화
- 정적 파일 압축
- 이미지 최적화
- 브라우저 캐싱 활용

## 6. 배포 환경

### 6.1 개발 환경
- Python 3.9+
- Django 4.2+
- SQLite 데이터베이스
- Django 개발 서버

### 6.2 운영 환경
- Ubuntu 20.04 LTS
- Nginx + Gunicorn
- PostgreSQL 13+
- SSL 인증서 적용

## 7. 모니터링 및 로깅

### 7.1 로깅 설정
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'restaurant.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 7.2 성능 모니터링
- 응답 시간 측정
- 데이터베이스 쿼리 분석
- 메모리 사용량 모니터링

## 8. 백업 및 복구

### 8.1 데이터 백업
- 일일 자동 백업
- 주간 전체 백업
- 클라우드 스토리지 연동

### 8.2 복구 절차
1. 서비스 중단 알림
2. 백업 데이터 복원
3. 데이터 무결성 검증
4. 서비스 재시작

## 9. 확장성 고려사항

### 9.1 수평 확장
- 로드 밸런서 적용
- 데이터베이스 읽기 전용 복제본
- 캐시 서버 도입 (Redis)

### 9.2 기능 확장
- 결제 시스템 연동
- 재고 관리 시스템
- 고객 관리 시스템 (CRM)
- 배달 주문 시스템