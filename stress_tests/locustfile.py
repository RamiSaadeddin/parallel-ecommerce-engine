from locust import HttpUser, task, between


class EcommerceUser(HttpUser):
    """
    Simulates normal users using the e-commerce backend.

    This stress test is used to prove that the system can handle
    many concurrent users without crashing.
    """

    wait_time = between(1, 3)

    @task(6)
    def view_products(self):
        """
        Most users browse products.
        This also tests Redis caching because /api/products/ uses cache.
        """
        self.client.get("/api/products/")

    @task(2)
    def view_orders(self):
        """
        Some users view orders.
        """
        self.client.get("/api/orders/")

    @task(1)
    def create_order(self):
        """
        Some users try to create orders.

        If stock runs out, the backend returns 400 Not enough stock.
        This is not considered a server crash, so we mark it as expected.
        """
        payload = {
            "product_id": 1,
            "quantity": 1,
        }

        with self.client.post(
            "/api/orders/create/",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 400:
                try:
                    data = response.json()
                    if data.get("message") == "Not enough stock":
                        response.success()
                    else:
                        response.failure(f"Unexpected 400 response: {data}")
                except Exception:
                    response.failure("Invalid 400 response")
            else:
                response.failure(
                    f"Unexpected status code: {response.status_code}"
                )

    @task(1)
    def view_performance_logs(self):
        """
        Tests the monitoring endpoint.
        """
        self.client.get("/api/monitoring/performance/")