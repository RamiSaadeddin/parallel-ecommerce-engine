# High-Performance E-Commerce Backend Engine

This project is a high-performance backend system for an e-commerce platform. It was built as a Parallel Programming course project and focuses on backend performance, concurrency control, caching, asynchronous processing, load distribution, resource management, and stress testing.

The system is implemented using Django REST Framework, PostgreSQL, Redis, Celery, Docker Redis, and Locust.

---

## Project Goal

The goal of this project is not only to build a basic e-commerce backend, but also to demonstrate important non-functional backend concepts such as:

* Race condition prevention
* ACID transactions
* Pessimistic locking
* Redis caching
* Performance monitoring
* Asynchronous background jobs
* Batch processing
* Load distribution simulation
* Resource/capacity management
* Stress testing with concurrent users
* Bottleneck analysis and optimization benchmarking

---

## Technologies Used

* Python
* Django
* Django REST Framework
* PostgreSQL
* Redis
* Celery
* Docker
* Locust
* PowerShell / Windows environment

---

## Main Features

### Products API

The system provides an API to fetch active products.

Endpoint:

```http
GET /api/products/
```

The products endpoint uses Redis caching. On the first request, data is fetched from PostgreSQL. On repeated requests, data is served from Redis.

Example response source:

```json
{
    "source": "redis_cache"
}
```

---

### Orders API

The system provides an API to create orders.

Endpoint:

```http
POST /api/orders/create/
```

Order creation includes:

* Product stock validation
* Stock reduction
* Order creation
* Order item creation
* Payment creation
* Asynchronous invoice generation

The order creation process uses:

```python
transaction.atomic()
select_for_update()
```

This prevents race conditions when many users try to buy the same product at the same time.

---

### Race Condition Protection

The system uses pessimistic locking to prevent stock corruption.

A concurrency test was created to simulate multiple users buying the same product at the same time.

Test file:

```text
scripts/concurrency_test.py
```

Run:

```bash
python scripts/concurrency_test.py
```

Example result:

```text
Successful orders: 5
Failed orders: 15
Final stock: 0
TEST PASSED: Race condition was prevented. Stock is correct.
```

---

### Redis Caching

Redis is used to cache active products and reduce repeated database reads.

Redis is started using Docker:

```bash
docker start ecommerce-redis
```

If the Redis container does not exist yet:

```bash
docker run --name ecommerce-redis -p 6379:6379 -d redis:latest
```

To test Redis:

```bash
docker exec -it ecommerce-redis redis-cli ping
```

Expected result:

```text
PONG
```

---

### Redis Benchmark

A benchmark script compares product-list performance before and after Redis caching.

Benchmark file:

```text
scripts/cache_benchmark.py
```

Run:

```bash
python scripts/cache_benchmark.py
```

The benchmark clears the cache before each request in the "before Redis" test, then warms the cache and measures repeated cached requests in the "after Redis" test.

A larger dataset of benchmark products was used to make the database-read bottleneck more visible.

Seed benchmark products:

```bash
python scripts/seed_products.py
```

Benchmark result:

```text
Before Redis average: 156.26 ms
After Redis average: 92.41 ms
Improvement: 40.86%
```

This shows that Redis caching improved repeated product-list requests by reducing PostgreSQL reads.

---

### AOP-Style Performance Monitoring

The project includes middleware that measures API response time without mixing monitoring code with business logic.

Middleware:

```text
monitoring/middleware.py
```

Performance logs endpoint:

```http
GET /api/monitoring/performance/
```

The middleware measures:

* Endpoint path
* HTTP method
* Response time in milliseconds
* Status code
* Request timestamp

The benchmark can skip performance logging using this header:

```http
X-Skip-Performance-Log: true
```

This allows cleaner performance measurements without adding extra database writes during benchmarking.

---

### Asynchronous Invoice Generation

The system uses Celery with Redis as a broker to generate invoices asynchronously after order creation.

This means the order request can finish quickly while the invoice is generated in the background.

Start Celery worker on Windows:

```bash
celery -A config worker --pool=solo -l info
```

Example Celery output:

```text
Task orders.tasks.generate_invoice_task received
Task orders.tasks.generate_invoice_task succeeded
```

The invoice is generated after the order transaction is successfully committed.

---

### Daily Sales Batch Processing

The system includes a batch processing task that calculates daily sales reports in chunks.

Endpoint:

```http
POST /api/orders/process-daily-sales/
```

Example request body:

```json
{
    "chunk_size": 2
}
```

Reports endpoint:

```http
GET /api/orders/daily-sales-reports/
```

Example result:

```json
{
    "report_date": "2026-06-15",
    "total_orders": 6,
    "total_sales": "6000.00",
    "processed_chunks": 3,
    "chunk_size": 2
}
```

This proves that the system processes daily sales in batches instead of processing everything in one large operation.

---

### Load Balancing Simulation

The system simulates distributing incoming order-processing requests across multiple backend servers using Round Robin.

Endpoint:

```http
POST /api/monitoring/load-balanced-order/
```

Example response:

```json
{
    "message": "Order request distributed successfully",
    "strategy": "round_robin",
    "request_type": "order_processing",
    "handled_by": "server-1",
    "available_servers": [
        "server-1",
        "server-2",
        "server-3"
    ]
}
```

Repeated requests rotate between:

```text
server-1
server-2
server-3
server-1
...
```

Load balance logs endpoint:

```http
GET /api/monitoring/load-balance-logs/
```

---

### Resource Management / Capacity Control

The system simulates resource management by limiting the number of heavy order-processing tasks that can run at the same time.

Only 3 heavy tasks are allowed concurrently. Extra requests are rejected with HTTP 429.

Endpoint:

```http
POST /api/monitoring/resource-limited-task/
```

Resource capacity test file:

```text
scripts/resource_capacity_test.py
```

Run:

```bash
python scripts/resource_capacity_test.py
```

Example result:

```text
Concurrent users: 10
Maximum allowed simultaneous tasks: 3

Completed tasks: 3
Rejected tasks: 7
TEST PASSED: Resource capacity limit was enforced.
```

This proves that the backend can enforce a capacity limit and protect itself from overload.

---

### Stress Testing

Locust is used to simulate 100 concurrent users.

Stress test file:

```text
stress_tests/locustfile.py
```

Run with UI:

```bash
locust -f stress_tests/locustfile.py
```

Then open:

```text
http://localhost:8089
```

Use:

```text
Users: 100
Spawn rate: 10
Host: http://127.0.0.1:8000
```

Run headless for one minute:

```bash
locust -f stress_tests/locustfile.py --headless -u 100 -r 10 -t 1m --host http://127.0.0.1:8000 --html stress_tests/stress_report_1min.html
```

Example stress test result:

```text
Total requests: 2607
Failures: 0
Exceptions: 0
Average response time: 113.44 ms
Requests per second: 44.15
```

---

## API Endpoints

### Products

```http
GET /api/products/
```

### Orders

```http
GET /api/orders/
POST /api/orders/create/
POST /api/orders/process-daily-sales/
GET /api/orders/daily-sales-reports/
```

### Monitoring

```http
GET /api/monitoring/performance/
POST /api/monitoring/load-balanced-order/
GET /api/monitoring/load-balance-logs/
POST /api/monitoring/resource-limited-task/
GET /api/monitoring/resource-usage-logs/
```

---

## How to Run the Project

### 1. Create and activate virtual environment

```bash
python -m venv venv
```

PowerShell:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Create `.env`

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=ecommerce_engine
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

Do not commit `.env` to GitHub.

---

### 4. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 5. Create admin user

```bash
python manage.py createsuperuser
```

---

### 6. Start Redis

If the Redis container already exists:

```bash
docker start ecommerce-redis
```

If it does not exist:

```bash
docker run --name ecommerce-redis -p 6379:6379 -d redis:latest
```

Check Redis:

```bash
docker exec -it ecommerce-redis redis-cli ping
```

Expected:

```text
PONG
```

---

### 7. Start Django server

```bash
python manage.py runserver
```

Server URL:

```text
http://127.0.0.1:8000
```

---

### 8. Start Celery worker

Open another terminal, activate the virtual environment, then run:

```bash
celery -A config worker --pool=solo -l info
```

---

## Useful Test Commands

### Run race-condition test

```bash
python scripts/concurrency_test.py
```

### Seed benchmark products

```bash
python scripts/seed_products.py
```

### Run Redis cache benchmark

```bash
python scripts/cache_benchmark.py
```

### Run resource capacity test

```bash
python scripts/resource_capacity_test.py
```

### Run Locust stress test

```bash
locust -f stress_tests/locustfile.py --headless -u 100 -r 10 -t 1m --host http://127.0.0.1:8000 --html stress_tests/stress_report_1min.html
```

---

## Project Structure

```text
ecommerce-engine/
│
├── config/
│   ├── settings.py
│   ├── celery.py
│   └── urls.py
│
├── products/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── orders/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── tasks.py
│   └── urls.py
│
├── monitoring/
│   ├── models.py
│   ├── middleware.py
│   ├── views.py
│   └── urls.py
│
├── scripts/
│   ├── concurrency_test.py
│   ├── cache_benchmark.py
│   ├── seed_products.py
│   └── resource_capacity_test.py
│
├── stress_tests/
│   ├── locustfile.py
│   └── stress_report_1min.html
│
├── benchmark_results/
│   └── cache_benchmark_result.json
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Notes

* `.env` should not be committed.
* `venv/` should not be committed.
* `__pycache__/` and `.pyc` files should not be committed.
* Redis must be running before using caching, Celery, load balancing simulation, and resource capacity control.
* Celery must be running for asynchronous invoice generation and daily sales batch processing.
* PostgreSQL must be running before starting Django.

---

## Summary

This backend demonstrates several high-performance backend techniques:

* PostgreSQL transactions protect order consistency.
* Pessimistic locking prevents race conditions.
* Redis caching improves repeated product-list requests.
* Celery handles background invoice generation and batch processing.
* Locust validates system behavior under 100 concurrent users.
* Round Robin simulation demonstrates load distribution.
* Resource capacity simulation prevents overload by limiting concurrent heavy tasks.
* AOP-style middleware monitors API performance without mixing monitoring logic with business logic.
