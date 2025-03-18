import pytest
from httpx import AsyncClient
from models import Order  # Ensure this import is at the top of your test file
from sqlalchemy.orm import Session

ORDER_DATA = {
    "quantity": 2,
    "pizza_size": "LARGE"
}

@pytest.mark.asyncio
async def test_place_order(async_client: AsyncClient):
    """Test placing an order without wiping the database."""
    
    # ✅ Log existing orders to ensure nothing is deleted
    existing_orders = await async_client.get("/orders/orders")
    print(f"Existing orders before test: {existing_orders.json()}")

    # ✅ Login staff user to get token
    login_response = await async_client.post(
        "/auth/login",
        json={"username": "testStaff", "password": "password"},  
        headers={"Content-Type": "application/json"},
    )

    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    # ✅ Place an order
    response = await async_client.post(
        "/orders/order",  
        json=ORDER_DATA,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201, response.text
    order = response.json()
    
    print(f"✅ Order placed: {order}")  # Debug print

    assert order["quantity"] == ORDER_DATA["quantity"]
    assert order["pizza_size"] == ORDER_DATA["pizza_size"]
    assert "id" in order  

    return order["id"], token  


@pytest.mark.asyncio
async def test_update_order_status(async_client: AsyncClient):
    """Test updating an order status."""

    # ✅ Place an order first to get an order_id and token
    order_id, token = await test_place_order(async_client)

    # ✅ Update the order status using the token
    response = await async_client.patch(
        f"/orders/order/update/{order_id}",  # Try removing the trailing slash if it exists
        json={"order_status": "DELIVERED"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # ✅ Validate response
    assert response.status_code == 200, response.text
    updated_order = response.json()
    assert updated_order["order_status"]["value"] == "DELIVERED"

@pytest.mark.asyncio
async def test_delete_order(async_client: AsyncClient):
    """Test deleting an order."""
    # Pass async_client to test_place_order to ensure it gets the correct argument
    order_id, token = await test_place_order(async_client)

    # Update the base_url to localhost where your FastAPI app is running
    async with AsyncClient(base_url="http://127.0.0.1:8000") as client:  # Use http://localhost:8000
        # Send DELETE request to delete the order
        response = await client.delete(
            f"/orders/order/delete/{order_id}",  # Ensure the endpoint matches your app
            headers={"Authorization": f"Bearer {token}"},  # Attach token in header
        )

        # Assert that the status code is 204 No Content, indicating successful deletion
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"

        # Verify that the order no longer exists by attempting to GET the order
        response = await client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token}"})
        
        # Assert that a 404 status code is returned, indicating the order is deleted
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"